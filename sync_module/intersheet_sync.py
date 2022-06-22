import gc
import logging
import time

import app.config as config
import data_module.helper as helper


def full_smartsheet_sync(minutes):
    """Sync Smartsheet data between rows using UUID
    """
    import data_module.get_data as get_data

    # import data_module.write_data as write_data
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

    sheet_ids = get_data.get_all_sheet_ids(
        minutes, config.workspace_id, config.index_sheet)
    sheet_ids = list(set(sheet_ids))

    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.
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
