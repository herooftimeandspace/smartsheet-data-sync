import gc
import json
import logging
import time

import app.config as config
import app.variables as app_vars
import data_module.get_data as get_data
import data_module.helper as helper
import data_module.jobs as jobs
import data_module.smartsheet_api as smartsheet_api
import smartsheet

logger = logging.getLogger(__name__)

# General Approach: Load up the Index Sheet. Collect all rows with UUIDs.
# On subset of Index Sheet rows with UUIDs, look up the sheet and row IDs
# For each cell in the sheet row, match column names to the Index Sheet
# If there's a match between the Index Sheet column name and the cell column
# name, check the value. If the values are a match, do nothing. Check the
# modified date on each cell. If the modified date/time matches +/- 30 seconds
# do nothing.
# Create two row objects, one for the Index Sheet and one for the Plan Sheet
#
# If the Index Sheet is more recent (Data was synced from Jira),
# copy the Index Sheet Cell Value into the matching Sheet Cell/Row.
# If the Plan Sheet Cell is more recent (Data was updated in the Sheet),
# copy the Plan Sheet Cell Value into the Index Sheet Row object
# Do this for each column in the row, then write both rows back to their
# respective sheets.
# Make sure Modified Dates are in the same ISO timezone/format or we'll end
# up with constantly flipping values when we compare times.


def compare_dates(index_history, plan_history, context="Cell"):
    """Compare the modified date of the index cell v. the modified date
    in the program plan.
    If Index > Sheet: Copy Index Cell -> Plan is more recent
    If Index < Sheet: Copy Sheet Cell -> Index is more recent
    If Index == Sheet (+/- 1 second): Do nothing

    Returns:
        str: None, Index, or Plan depending on which cell has the most
        recent modified_at date
    """
    if not isinstance(index_history, (smartsheet.models.row.Row,
                                      smartsheet.models.cell.Cell,
                                      list)):
        msg = str("Index History should be smartsheet.models.Row or "
                  "smartsheet.models.Cell, not {}"
                  "").format(type(index_history))
        raise TypeError(msg)
    if not isinstance(plan_history, (smartsheet.models.row.Row,
                                     smartsheet.models.cell.Cell,
                                     list)):
        msg = str("Index History should be smartsheet.models.Row or "
                  "smartsheet.models.Cell, not {}"
                  "").format(type(index_history))
        raise TypeError(msg)
    if not isinstance(context, str):
        msg = str("Context should be a string, not {}"
                  "").format(type(index_history))
        raise TypeError(msg)
    if context not in ("Row", "Cell"):
        msg = str("Type should be either 'Row' or 'Cell', not {}"
                  "").format(type(context))
        raise ValueError(msg)

    if context == "Cell":
        if not index_history:
            index_modified_at = None
            msg = str("Used Index Cell ModAt: {}").format(
                index_modified_at)
            logging.debug(msg)
        else:
            index_modified_at = index_history[0]
            index_modified_at = index_modified_at.modified_at
            msg = str("Used Index Cell History ModAt: {}").format(
                index_modified_at)
            logging.debug(msg)

        if not plan_history:
            plan_modified_at = None
            msg = str("Used Plan Cell ModAt: {}").format(
                plan_modified_at)
            logging.debug(msg)
        else:
            plan_modified_at = plan_history[0]
            plan_modified_at = plan_modified_at.modified_at
            msg = str("Used Plan Cell History ModAt: {}").format(
                plan_modified_at)
            logging.debug(msg)
        # Set threshold for cell detection to 1 seconds
        threshold = 1
    if context == "Row":
        if not index_history:
            index_modified_at = None
            msg = str("Used Index Row ModAt: {}").format(
                index_modified_at)
            logging.debug(msg)
        else:
            index_modified_at = index_history.modified_at
            msg = str("Used Index Row History ModAt: {}").format(
                index_modified_at)
            logging.debug(msg)

        if not plan_history:
            plan_modified_at = None
            msg = str("Used Plan Row ModAt: {}").format(
                plan_modified_at)
            logging.debug(msg)
        else:
            plan_modified_at = plan_history.modified_at
            msg = str("Used Plan Row History ModAt: {}").format(
                plan_modified_at)
            logging.debug(msg)
        # Set threshold for row detection to 15 seconds
        threshold = 15

    if index_modified_at is None and plan_modified_at is not None:
        return "Plan"
    elif index_modified_at is not None and plan_modified_at is None:
        return "Index"
    elif index_modified_at is None and plan_modified_at is None:
        return None
    else:
        # Smartsheet Date Format: 2022-05-08T19:00:22Z
        if index_modified_at > plan_modified_at:
            delta = index_modified_at - plan_modified_at
            if delta.seconds <= threshold:
                return None
            else:
                return "Index"
        elif index_modified_at < plan_modified_at:
            delta = plan_modified_at - index_modified_at
            if delta.seconds <= threshold:
                return None
            else:
                return "Plan"
        elif index_modified_at == plan_modified_at:
            return None
        else:
            return None


def get_index_row(index_sheet, row_id):
    if not isinstance(index_sheet, (dict, smartsheet.models.Sheet)):
        msg = str("Index Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(index_sheet))
        raise TypeError(msg)
    if not isinstance(row_id, int):
        msg = str("Row ID should be an int, not {}"
                  "").format(type(row_id))
        raise TypeError(msg)
    if row_id <= 0:
        msg = str("Row ID should be a positive int, not {}"
                  "").format(row_id)
        raise ValueError(msg)
    for row in index_sheet.rows:
        if row.id == row_id:
            return row
    return None


def rebuild_cell(cell, column_id):
    """Takes the most recent cell data and builds a new cell that the API will
    accept. Drops either the object_value or value parameter. Prefers
    object_value if present.

    Args:
        cell (smartsheet.Cell): The cell with the source data
        column_id (int): The ID of the column for the new cell

    Returns:
        smartsheet.Cell: The new Smartsheet cell.
    """
    if not isinstance(cell, smartsheet.models.Cell):
        msg = str("Cell should be smartsheet.models.Cell, not {}"
                  "").format(type(cell))
        raise TypeError(msg)
    if not isinstance(column_id, int):
        msg = str("Column ID should be an int, not {}"
                  "").format(type(column_id))
        raise TypeError(msg)
    if column_id <= 0:
        msg = str("Column ID should be a positive int, not {}"
                  "").format(column_id)
        raise ValueError(msg)
    newer_cell = smartsheet.models.Cell()
    newer_cell.column_id = int(column_id)
    # Use object_value first for more complex cells like picklists, URLS, etc
    if cell.object_value:
        newer_cell.object_value = cell.object_value
        # If object_value is still None after copying it from the source,
        # set basic value instead.
        if not newer_cell.object_value:
            newer_cell.value = cell.value
    else:
        # Default to setting basic cell value
        newer_cell.value = cell.value
    # Set the hyperlink if there is one.
    if cell.hyperlink:
        link = str({}).format(cell.hyperlink)
        link = json.loads(link)
        newer_cell.hyperlink = link

    if not newer_cell.value:
        newer_cell.value = smartsheet.models.ExplicitNull()
    elif not newer_cell.object_value:
        newer_cell.object_value = smartsheet.models.ExplicitNull()

    # logging.debug("Newer Cell v: {} | ov: {} | hl: {}"
    #               "". format(newer_cell.value, newer_cell.object_value,
    #                          newer_cell.hyperlink))

    return newer_cell


def build_row(jira_index_sheet, jira_index_col_map, index_row, plan_sheet,
              plan_col_map, plan_row, columns_to_compare):
    """Builds the row data necessary to update both the Index Sheet and the
    Program Plan sheet(s). Parses through the cell history of each row and
    determines which cell is the most recent, then creates new rows with the
    updated data and adds it to the list

    Args:
        jira_index_sheet (smartsheet.Sheet): The Jira Index Sheet
        jira_index_col_map (dict): The Jira Index Sheet column map in the form
                                   of Column Name: Column ID
        index_row (smartsheet.Row): The Index row to evaluate
        plan_sheet (smartsheet.sheet): The Program Plan sheet
        plan_row (smartsheet.row): The Program Plan row to evaluate
        plan_col_map (dict): The Program Plan column nap in the form of
                             Column Name: Column ID
        columns_to_compare (list): A list of columns to compare between the
                                   two rows

    Returns:
        list, list: A Smartsheet Row to update the Index Sheet, and a
                    Smartsheet Row to update the Program Plan sheet
    """
    if not isinstance(jira_index_sheet, smartsheet.models.Sheet):
        msg = str("Jira Index Sheet should be smartsheet.models.Sheet, not {}"
                  "").format(type(jira_index_sheet))
        raise TypeError(msg)
    if not isinstance(jira_index_col_map, dict):
        msg = str("Index Column Map should be a dict, not {}"
                  "").format(type(jira_index_col_map))
        raise TypeError(msg)
    if not isinstance(index_row, smartsheet.models.Row):
        msg = str("Index Row should be smartsheet.models.Row, not {}"
                  "").format(type(index_row))
        raise TypeError(msg)
    if not isinstance(plan_sheet, smartsheet.models.Sheet):
        msg = str("Plan Sheet should be smartsheet.models.Sheet, not {}"
                  "").format(type(plan_sheet))
        raise TypeError(msg)
    if not isinstance(plan_col_map, dict):
        msg = str("Plan Column Map should be a dict, not {}"
                  "").format(type(plan_col_map))
        raise TypeError(msg)
    if not isinstance(plan_row, smartsheet.models.Row):
        msg = str("Plan Row should be smartsheet.models.Row, not {}"
                  "").format(type(plan_row))
        raise TypeError(msg)
    if not isinstance(columns_to_compare, list):
        msg = str("Columns to compare should be a list, not {}"
                  "").format(type(columns_to_compare))
        raise TypeError(msg)
    if not columns_to_compare:
        msg = str("Columns to compare cannot be an enpty list.")
        raise ValueError(msg)
    # Create new row for the Index Sheet and copy the row's ID
    updated_index_row = smartsheet.models.Row()
    updated_index_row.id = index_row.id

    # Create a new row object for the plan sheet and copy the plan_row ID
    updated_plan_row = smartsheet.models.Row()
    updated_plan_row.id = plan_row.id

    # Interate through each column that we want to sync data
    for col in columns_to_compare:
        # Get the cell data for matching columns between the two rows
        index_cell = helper.get_cell_data(index_row, col, jira_index_col_map)
        plan_cell = helper.get_cell_data(plan_row, col, plan_col_map)
        # logging.debug("Index v: {}, ov: {}, hl: {}".format(
        #     index_cell.value, index_cell.object_value,
        #     index_cell.hyperlink))
        # logging.debug("Plan v: {}, ov: {}, hl: {}".format(
        #     plan_cell.value, plan_cell.object_value,
        #     plan_cell.hyperlink))

        # If the index cell and plan cell values match, continue to the
        # next column.
        if index_cell.value == plan_cell.value or\
                index_cell.object_value == plan_cell.value:
            # Check the hyperlink property to ensure we arent missing a URL
            # between the two. Mostly for links to Jira tickets.
            if index_cell.hyperlink == plan_cell.hyperlink:
                logging.debug("Values Match, skipping {}".format(col))
                continue

        # Always write the Jira Col on the plan sheet if not hyperlinked
        if col == app_vars.jira_col:
            # logging.debug("Jira Col found, returning Index")
            newer = "Index"
            plan_link = str({}).format(plan_cell.hyperlink)
            index_link = str({}).format(index_cell.hyperlink)
            if plan_link == index_link:
                logging.debug("URL links match, skipping {}.".format(col))
                continue
        else:
            # Query the cell history for both cells from the API.
            # Defaults to only pulling the most recent history object.
            index_cell_history = smartsheet_api.get_cell_history(
                jira_index_sheet.id, index_row.id, jira_index_col_map[col]
            )
            plan_cell_history = smartsheet_api.get_cell_history(
                plan_sheet.id, plan_row.id, plan_col_map[col]
            )
            # Get the newer of the two cells
            newer = compare_dates(index_cell_history, plan_cell_history)

        if not newer:
            # Newer Cell was modified within the last 30 seconds, skip
            msg = str("Newer {} cell is None, skipping.").format(col)
            logging.debug(msg)
            continue
        if newer == "Index":
            # Index Cell was the newer cell. Copy the Plan Cell column
            # ID to the newer cell object, and append it to the new plan
            # row object.
            msg = str("Newer {} cell is the {} cell.").format(col, newer)
            logging.debug(msg)
            newer_cell = rebuild_cell(index_cell, plan_col_map[col])
            # Update the cell even if it's None
            updated_plan_row.cells.append(newer_cell)
            # if newer_cell.object_value or newer_cell.value:
            #     updated_plan_row.cells.append(newer_cell)
            # else:
            #     logging.debug("Skipped {} because value: {} | object_value: {}"
            #                   "".format(col, newer_cell.value,
            #                             newer_cell.object_value))
        if newer == "Plan":
            # Plan Cell was the newer cell. Copy the Index Cell column
            # ID to the newer cell object, and append it to the new index
            # row object.
            msg = str("Newer {} cell is the {} cell.").format(col, newer)
            logging.debug(msg)
            newer_cell = rebuild_cell(plan_cell, jira_index_col_map[col])
            updated_plan_row.cells.append(newer_cell)
            # if newer_cell.object_value or newer_cell.value:
            #     updated_plan_row.cells.append(newer_cell)
            # else:
            #     logging.debug("Skipped {} because value: {} | object_value: {}"
            #                   "".format(col, newer_cell.value,
            #                             newer_cell.object_value))

    return updated_index_row, updated_plan_row


def drop_dupes(row_list):
    """Drops duplicate row IDs from the list of rows to update

    Args:
        row_list (list): List of Smartsheet Row objects to parse

    Raises:
        TypeError: Row List must be a list
        ValueError: Row List must not be empty

    Returns:
        list: A new list with only unique Row IDs
    """
    if not isinstance(row_list, list):
        msg = str("Project data must be type: list, not"
                  " {}").format(type(row_list))
        raise TypeError(msg)
    if not row_list:
        msg = str("List of Row objects must not be empty."
                  "").format()
        raise ValueError(msg)

    row_ids = []
    list_copy = row_list
    for row in list_copy:
        if row.id in row_ids:
            index = list_copy.index(row)
            del list_copy[index]
        else:
            row_ids.append(row.id)
    return list_copy


def bidirectional_sync(minutes):
    """Main execution for syncing bidirectionally between Program Plan sheets
    and the Jira Index Sheet, and by extension, Jira.

    Args:
        minutes (int): Number of minutes in the past used to filter sheets and
        sheet data. Defaults to dev_minutes

    Raises:
        TypeError: Minutes must be an int
        ValueError: Minutes must be a positive integer or 0
    """
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    start = time.time()
    msg = str("Starting bidirectinal sync between the Jira Index Sheet "
              "and all available Program Plans. "
              "Looking back {} minutes from {}"
              "").format(minutes,
                         time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.localtime(start)))
    logging.debug(msg)
    # Define the list of columns where we want to copy data
    # TODO: Add predecessor and create Jira links (blocked/is blocked by)
    # Will need to check the Index Sheet Linked Issues column and handle
    # single list v CSV, parse each index for strings and
    # ticket IDs, match to Row IDs (might need to re-pull the predecessor
    # row by row number?)
    columns_to_compare = [app_vars.jira_col, app_vars.jira_status_col,
                          app_vars.task_col, app_vars.assignee_col]

    # Get all sheet IDs modified within the last N minutes
    sheet_ids = get_data.get_all_sheet_ids(minutes, config.workspace_id,
                                           config.index_sheet)
    # Pull the sheets from the API and add them to a list.
    source_sheets = get_data.refresh_source_sheets(sheet_ids, minutes)
    # Pull the Jira Index Sheet and get the sheet data and columns
    jira_index_sheet, jira_index_col_map, jira_index_rows =\
        get_data.load_jira_index(config.index_sheet)

    # Loop through the list of sheets modified in the last N minutes
    for plan_sheet in source_sheets:
        # Loop through each row. Look for a Jira Ticket value. Look up that
        # value against all the tickets in the Index Sheet.
        plan_rows_to_update = []
        index_rows_to_update = []
        plan_col_map = helper.get_column_map(plan_sheet)
        # Skip the sheet if it doesn't have a Jira column
        if app_vars.jira_col not in plan_col_map.keys():
            continue

        for plan_row in plan_sheet.rows:
            plan_jira_cell = helper.get_cell_data(
                plan_row, app_vars.jira_col, plan_col_map)
            if not plan_jira_cell:
                # Plan Jira cell never had a value
                continue
            if not plan_jira_cell.value:
                # Plan Jira cell value is blank
                continue
            if plan_jira_cell.value not in jira_index_rows.keys():
                # Plan Jira cell value isn't in the Jira Index Sheet.
                # Raise error by setting plan jira cell value
                msg = str("[WARNING]; {} not found in the index sheet. Check "
                          "that the ticket was created or modified within the "
                          "last 3 months and try again."
                          "").format(plan_jira_cell.value)
                plan_jira_cell.value = msg
                new_row = smartsheet.models.Row()
                new_row.id = plan_row.id
                new_row.append(plan_jira_cell)
                plan_rows_to_update.append(new_row)
                continue
            else:
                index_row = get_index_row(
                    jira_index_sheet, jira_index_rows[plan_jira_cell.value])
            # index_row = smartsheet_api.get_row(
            #     jira_index_sheet.id, jira_index_rows[plan_jira_cell.value])
            msg = str("Index Row type: {}, Data: {}"
                      "").format(type(index_row), index_row)
            logging.debug(msg)
            msg = str("Plan Row type: {}, Data: {}"
                      "").format(type(plan_row), plan_row)
            logging.debug(msg)
            newer = compare_dates(index_row, plan_row, "Row")
            if not newer:
                # Skip to next row if rows were updated within 30 seconds of
                # each other.
                continue
            else:
                updated_index_row, updated_plan_row = build_row(
                    jira_index_sheet, jira_index_col_map, index_row,
                    plan_sheet, plan_col_map, plan_row, columns_to_compare)
            if updated_index_row.cells:
                index_rows_to_update.append(updated_index_row)
            else:
                logging.debug("No Index Rows to Update")
            if updated_plan_row.cells:
                plan_rows_to_update.append(updated_plan_row)
            else:
                logging.debug("No Plan Rows to Update")
        if index_rows_to_update:
            # Drop multiple references to the same row
            index_rows_to_update = drop_dupes(index_rows_to_update)
            smartsheet_api.write_rows_to_sheet(
                index_rows_to_update, jira_index_sheet, "update")
        if plan_rows_to_update:
            # Drop multiple references to the same row. This should never
            # happen since the Jira Index Sheet can't contain more than
            # 1 reference to a Jira Key, but adding it to be safe.
            plan_rows_to_update = drop_dupes(plan_rows_to_update)
            smartsheet_api.write_rows_to_sheet(
                plan_rows_to_update, plan_sheet, "update")

    end = time.time()
    elapsed = end - start
    elapsed = helper.truncate(elapsed, 3)
    msg = str("Bidirectional sync took: {} seconds.").format(elapsed)
    logging.info(msg)
    interval_msg = jobs.modify_scheduler(
        elapsed, 'sync_jira_interval', 'seconds', 1)
    logging.info(interval_msg)
    gc.collect()
    return True
