import logging
import time
import gc

import app.config as config
import data_module.get_data as get_data
import data_module.helper as helper
import data_module.write_data as write_data

logger = logging.getLogger(__name__)


def write_uuids_to_sheets(minutes):
    """Writes UUIDs to each blank cell in the UUID column across every sheet
        in the workspace, excluding the Index Sheet.

    Args:
        minutes (int): Number of minutes into the past to check for changes

    Raises:
        TypeError: Minutes should be an INT
        ValueError: Minutes should be a positive number, or zero
    """
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

    blank_uuid_index = get_data.get_blank_uuids(source_sheets)
    if blank_uuid_index:
        logging.info("There are {} project sheets to be updated "
                     "with UUIDs".format(len(blank_uuid_index)))
        sheets_updated = write_data.write_uuids(blank_uuid_index)
        if sheets_updated:
            logging.info("{} project sheet(s) updated with UUIDs"
                         "".format(sheets_updated))

    end = time.time()
    elapsed = end - start
    elapsed = helper.truncate(elapsed, 3)
    msg = str("Writing UUIDs took: {} seconds.").format(elapsed)
    logging.info(msg)
    gc.collect()
    if elapsed > 30:
        delta = elapsed - 30
        warn_msg = str("Writing UUIDs took {} seconds longer than "
                       "the interval.").format(delta)
        logging.warning(warn_msg)
        return msg, warn_msg
    else:
        return msg
