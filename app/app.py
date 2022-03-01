import gc
import logging
import threading
import time
import app.config as config
from uuid_module.create_jira_tickets import create_tickets
# from uuid_module.cell_link_sheet_data import write_uuid_cell_links

from uuid_module.helper import truncate
from uuid_module.variables import sheet_columns


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
    from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                      get_blank_uuids, get_sub_indexes,
                                      refresh_source_sheets)
    from uuid_module.write_data import write_jira_index_cell_links, write_uuids
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
        sheet_ids = get_all_sheet_ids(
            minutes, config.workspace_id, config.index_sheet)
        sheet_ids = list(set(sheet_ids))

    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.
    global sheet_index_lock
    with sheet_index_lock:
        source_sheets = refresh_source_sheets(sheet_ids, minutes)

    blank_uuid_index = get_blank_uuids(source_sheets)
    if blank_uuid_index:
        logging.info("There are {} project sheets to be updated "
                     "with UUIDs".format(len(blank_uuid_index)))
        sheets_updated = write_uuids(blank_uuid_index)
        if sheets_updated:
            logging.info("{} project sheet(s) updated with UUIDs"
                         "".format(sheets_updated))

    if not source_sheets:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Sheet index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    global project_index_lock
    with project_index_lock:
        try:
            project_uuid_index = get_all_row_data(
                source_sheets, sheet_columns, minutes)
        except ValueError as e:
            msg = str("Getting all row data returned an error. {}").format(e)
            logging.error(msg)

    if project_uuid_index:
        logging.info("Project Index is {} "
                     "items long".format(len(project_uuid_index)))

    if not project_uuid_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Project UUID Index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    try:
        jira_sub_index, project_sub_index = get_sub_indexes(
            project_uuid_index)
    except ValueError as e:
        msg = str("Getting sub-indexes returned an error. {}").format(e)
        logging.error(msg)

    if project_sub_index:
        logging.info("Project Sub Index is {} "
                     "items long".format(len(project_sub_index)))

    if not project_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Project sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    if jira_sub_index:
        logging.info("Jira Sub Index is {} "
                     "items long".format(len(jira_sub_index)))

    if not jira_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Jira sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    write_jira_index_cell_links(project_sub_index, config.index_sheet)

    # write_uuid_cell_links(project_uuid_index,
    #                       source_sheets)

    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    logging.info(
        "Full Jira sync took: {} seconds.".format(elapsed))
    gc.collect()


def full_smartsheet_sync():
    """Sync Smartsheet data between rows using UUID
    """
    from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                      refresh_source_sheets)
    start = time.time()
    msg = str("Starting refresh of Smartsheet project data.").format()
    logging.debug(msg)

    global sheet_id_lock
    with sheet_id_lock:
        sheet_ids = get_all_sheet_ids(
            config.minutes, config.workspace_id, config.index_sheet)
        sheet_ids = list(set(sheet_ids))

    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.
    global sheet_index_lock
    with sheet_index_lock:
        source_sheets = refresh_source_sheets(sheet_ids, config.minutes)

    with project_index_lock:
        try:
            project_uuid_index = get_all_row_data(
                source_sheets, sheet_columns, config.minutes)
        except ValueError as e:
            msg = str("Getting all row data returned an error. {}").format(e)
            logging.error(msg)

    # write_uuid_cell_links(project_uuid_index, source_sheets)

    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    logging.info(
        "Full Smartsheet cross-sheet sync took: {} seconds.".format(elapsed))
    gc.collect()


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
    # logging.debug("------------------------")
    # logging.debug("Adding job to refresh Jira tickets in real time. "
    #               "Interval = every 30 seconds.")
    # logging.debug("------------------------")
    # config.scheduler.add_job(full_jira_sync,
    #                          'interval',
    #                          args=[config.minutes],
    #                          seconds=30)

    # logging.debug("------------------------")
    # logging.debug("Adding job to get all data in the past week. "
    #               "Cron = every day at 1:00am UTC.")
    # logging.debug("------------------------")
    # config.scheduler.add_job(full_jira_sync,
    #                          'cron',
    #                          args=[10080],
    #                          day='*/1',
    #                          hour='1')

    logging.debug("------------------------")
    logging.debug("Adding job to write new Jira tickets in real time. "
                  "Interval = every 5 minutes.")
    logging.debug("------------------------")
    # TODO: Revert to 5 mins before merging with debug
    config.scheduler.add_job(create_tickets,
                             'interval',
                             args=[config.minutes],
                             minutes=5)
    return True
