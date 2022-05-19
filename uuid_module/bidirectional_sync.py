import logging

import app.config as config
import smartsheet

import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars
import uuid_module.get_data as get_data

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


def compare_dates(index_cell, index_cell_history,
                  plan_cell, plan_cell_history):
    ''' Compare the modified date of the row and cell v. the modified date
    in the Jira Index SHeet
    If Index > Sheet: Copy Index Cell -> Sheet Cell
    If Index < Sheet: Copy Sheet Cell -> Index Cell
    If Index == Sheet (+/- 1 minute): Do nothing
    If Index Value == Cell Value: Do nothing
    Data we need from Index: UUID, Modified Date/Time, row_id, column_id,
    cell_value
    '''
    # Smartsheet Date Format: 2022-05-08T19:00:22Z
    # Might need to convert to datetime object
    if index_cell_history.modified_at > plan_cell_history.modified_at:
        delta = index_cell_history.modified_at - plan_cell_history.modified_at
        if delta.seconds <= 30:
            return None
        else:
            return index_cell
    elif index_cell_history.modified_at < plan_cell_history.modified_at:
        delta = plan_cell_history.modified_at - index_cell_history.modified_at
        if delta.seconds <= 30:
            return None
        else:
            return plan_cell
    elif index_cell_history.modified_at == plan_cell_history.modified_at:
        return None
    else:
        return None


# REWRITE EVERYTING BELOW THIS LINE.
def build_row(jira_index_sheet, jira_index_col_map, index_row, plan_sheet,
              plan_row, plan_col_map, columns_to_compare):

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

        # If the index cell and plan cell values match, continue to the
        # next column.
        if index_cell.value == plan_cell.value:
            continue

        # Query the cell history for both cells from the API.
        # Defaults to only pulling the most recent history object.
        index_cell_history = smartsheet_api.get_cell_history(
            jira_index_sheet.id, index_row.id, jira_index_col_map[col]
        )
        plan_cell_history = smartsheet_api.get_cell_history(
            plan_sheet.id, plan_row.id, plan_col_map[col]
        )

        # Get the newer of the two cells
        newer_cell = compare_dates(
            index_cell, index_cell_history, plan_cell, plan_cell_history)

        if newer_cell is None:
            # Newer Cell was modified within the last 30 seconds, skip
            continue
        elif newer_cell == index_cell:
            # Index Cell was the newer cell. Copy the Plan Cell column
            # ID to the newer cell object, and append it to the new plan
            # row object.
            newer_cell.column_id = plan_col_map[col]
            updated_plan_row.cells.append(newer_cell)
        elif newer_cell == plan_cell:
            # Plan Cell was the newer cell. Copy the Index Cell column
            # ID to the newer cell object, and append it to the new index
            # row object.
            newer_cell.column_id = jira_index_col_map[col]
            updated_index_row.cells.append(newer_cell)
        else:
            # Catch if the cell returned doesn't meet those criteria
            continue

    return updated_index_row, updated_index_row


def bidirectional_sync():
    # Define the list of columns where we want to copy data
    # TODO: Add predecessor and create Jira links (blocked/is blocked by)
    # Will need to check the Index Sheet Linked Issues column and handle
    # single list v CSV, parse each index for strings and
    # ticket IDs, match to Row IDs (might need to re-pull the predecessor
    # row by row number?)
    columns_to_compare = [app_vars.jira_col, app_vars.status_col,
                          app_vars.task_col, app_vars.assignee_col]

    # Get all sheet IDs modified within the last config.minutes
    sheet_ids = get_data.get_all_sheet_ids(config.minutes, config.workspace_id,
                                           config.index_sheet)
    # Pull the sheets from the API and add them to a list.
    source_sheets = get_data.refresh_source_sheets(sheet_ids, config.minutes)
    # Pull the Jira Index Sheet and get the sheet data and columns
    jira_index_sheet, jira_index_col_map, jira_index_rows =\
        get_data.load_jira_index(config.index_sheet)

    # Loop through the list of sheets modified in the last config.minutes
    for plan_sheet in source_sheets:
        # Loop through each row. Look for a Jira Ticket value. Look up that
        # value against all the tickets in the Index Sheet.
        plan_rows_to_update = []
        index_rows_to_update = []
        plan_col_map = helper.get_column_map(plan_sheet)
        for plan_row in plan_sheet.rows():
            plan_jira_cell = helper.get_cell_data(
                plan_row, app_vars.jira_col, plan_col_map)
            if plan_jira_cell is None:
                # Plan Jira cell never had a value
                continue
            if plan_jira_cell.value is None:
                # Plan Jira cell value is blank
                continue
            if plan_jira_cell.value not in jira_index_rows.keys():
                # Plan Jira cell value isn't in the Jira Index Sheet
                # TODO: Update the plan row with an error message, a la:
                # "Jira Key" not found in the index sheet. Check that
                # The ticket was created or modified within the last 3 months.
                continue

            index_row = smartsheet_api.get_row(
                jira_index_sheet.id, jira_index_rows[plan_jira_cell.value])
            updated_index_row, updated_plan_row = build_row(
                jira_index_sheet, jira_index_col_map, index_row, plan_sheet,
                plan_row, plan_col_map, columns_to_compare)
            if updated_index_row.cells:
                index_rows_to_update.append(updated_index_row)
            if updated_plan_row.cells:
                plan_rows_to_update.append(updated_plan_row)
        if index_rows_to_update:
            smartsheet_api.write_rows_to_sheet(
                index_rows_to_update, jira_index_sheet, "update")
        if plan_rows_to_update:
            smartsheet_api.write_rows_to_sheet(
                plan_rows_to_update, plan_sheet, "update")
