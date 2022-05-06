import gc
import logging
import threading
import time

import uuid_module.create_jira_tickets as create_jira_tickets
import uuid_module.helper as helper
import uuid_module.variables as app_vars

import app.config as config

# import uuid_module.cell_link_sheet_data as uuid_links


sheet_id_lock = threading.Lock()
sheet_index_lock = threading.Lock()
project_index_lock = threading.Lock()


def full_jira_sync(minutes):
    """Executes a full Jira sync across all sheets in the workspace.

    Args:
        minutes (int): Number of minutes into the past to check for changes

    Raises:
        TypeError: Minutes should be an INT
        ValueError: Minutes should be a positive number, or zero
    """
    import uuid_module.get_data as get_data
    import uuid_module.write_data as write_data
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    start = time.time()
    msg = str("Starting refresh of Smartsheet project data. "
              "Looking back {} minutes from {}"
              "").format(minutes,
                         time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.localtime(start)))
    logging.debug(msg)
    global sheet_id_lock

    with sheet_id_lock:
        sheet_ids = get_data.get_all_sheet_ids(
            minutes, config.workspace_id, config.index_sheet)
        sheet_ids = list(set(sheet_ids))

    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.
    global sheet_index_lock
    with sheet_index_lock:
        source_sheets = get_data.refresh_source_sheets(sheet_ids, minutes)

    if not source_sheets:
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 3)
        msg = str("Sheet index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return msg

    blank_uuid_index = get_data.get_blank_uuids(source_sheets)
    if blank_uuid_index:
        logging.info("There are {} project sheets to be updated "
                     "with UUIDs".format(len(blank_uuid_index)))
        sheets_updated = write_data.write_uuids(blank_uuid_index)
        if sheets_updated:
            logging.info("{} project sheet(s) updated with UUIDs"
                         "".format(sheets_updated))

    global project_index_lock
    with project_index_lock:
        project_uuid_index = get_data.get_all_row_data(
            source_sheets, app_vars.sheet_columns, minutes)

    if project_uuid_index:
        logging.info("Project Index is {} "
                     "items long".format(len(project_uuid_index)))

    if not project_uuid_index:
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 3)
        msg = str("Project UUID Index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return msg

    jira_sub_index, project_sub_index = get_data.get_sub_indexes(
        project_uuid_index)

    if not project_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 3)
        msg = str("Project sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return msg

    if project_sub_index:
        logging.info("Project Sub Index is {} "
                     "items long".format(len(project_sub_index)))

    if not jira_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 3)
        msg = str("Jira sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return msg

    if jira_sub_index:
        logging.info("Jira Sub Index is {} "
                     "items long".format(len(jira_sub_index)))

    write_data.write_jira_index_cell_links(project_sub_index,
                                           config.index_sheet)

    # write_uuid_cell_links(project_uuid_index,
    #                       source_sheets)

    end = time.time()
    elapsed = end - start
    elapsed = helper.truncate(elapsed, 3)
    msg = str("Full Jira sync took: {} seconds.").format(elapsed)
    logging.info(msg)
    gc.collect()
    if elapsed > 30:
        delta = elapsed - 30
        warn_msg = str("Full Jira Sync took {} seconds longer than "
                       "the interval.").format(delta)
        logging.warning(warn_msg)
        return msg, warn_msg
    else:
        return msg


def full_smartsheet_sync(minutes):
    """Sync Smartsheet data between rows using UUID
    """
    import uuid_module.get_data as get_data
    # import uuid_module.write_data as write_data
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    start = time.time()
    msg = str("Starting refresh of Smartsheet project data. "
              "Looking back {} minutes from {}"
              "").format(minutes,
                         time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.localtime(start)))
    logging.debug(msg)
    global sheet_id_lock

    with sheet_id_lock:
        sheet_ids = get_data.get_all_sheet_ids(
            minutes, config.workspace_id, config.index_sheet)
        sheet_ids = list(set(sheet_ids))

    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.
    global sheet_index_lock
    with sheet_index_lock:
        source_sheets = get_data.refresh_source_sheets(sheet_ids, minutes)

    if not source_sheets:
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 3)
        msg = str("Sheet index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return msg

    # with project_index_lock:
    #     project_uuid_index = get_data.get_all_row_data(
    #         source_sheets, app_vars.sheet_columns, config.minutes)

    # write_uuid_cell_links(project_uuid_index, source_sheets)

    end = time.time()
    elapsed = end - start
    elapsed = helper.truncate(elapsed, 3)
    msg = str("Full Smartsheet cross-sheet sync took: {} seconds."
              "").format(elapsed)
    logging.info(msg)
    gc.collect()
    if elapsed > 120:
        delta = elapsed - 120
        warn_msg = str("Full Smartsheet cross-sheet sync took {} seconds "
                       "longer than the interval.").format(delta)
        logging.warning(warn_msg)
        return msg, warn_msg
    else:
        return msg


def main():
    """Configures the scheduler to run jobs.
       1: Runs full_jira_sync every 30 seconds and looks back based on the
          minutes defined in variables for which rows to write to.
       2: Runs full_jira_sync every day at 1:00am UTC and looks back 1 week
          for which rows to write to.
       3: Runs create_tickets every 5 minutes, and looks back based on the
          minutes defined in variables for which rows to write to.

    Returns:
        bool: Returns True if main successfully initialized and scheduled jobs,
              False if not.
    """
    logging.debug("------------------------")
    logging.debug("Adding job to refresh Jira tickets in real time. "
                  "Interval = every 30 seconds.")
    logging.debug("------------------------")
    config.scheduler.add_job(full_jira_sync,
                             'interval',
                             args=[config.minutes],
                             seconds=30,
                             id="sync_jira_interval")

    logging.debug("------------------------")
    logging.debug("Adding job to get all data in the past week. "
                  "Cron = every day at 1:00am UTC.")
    logging.debug("------------------------")
    config.scheduler.add_job(full_jira_sync,
                             'cron',
                             args=[10080],
                             day='*/1',
                             hour='1',
                             id="sync_jira_cron")

    logging.debug("------------------------")
    logging.debug("Adding job to write new Jira tickets in real time. "
                  "Interval = every 2 minutes.")
    logging.debug("------------------------")
    config.scheduler.add_job(create_jira_tickets.create_tickets,
                             'interval',
                             args=[config.minutes],
                             minutes=2,
                             id="create_jira_interval")

    logging.debug("------------------------")
    logging.debug("Adding job to create any tickets missed in the past week. "
                  "Cron = every day at 1:00am UTC.")
    logging.debug("------------------------")
    config.scheduler.add_job(create_jira_tickets.create_tickets,
                             'cron',
                             args=[10080],
                             day='*/1',
                             hour='1',
                             id="create_jira_cron")
    return True
