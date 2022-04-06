import logging
import smartsheet

import uuid_module.build_data as build_data
import uuid_module.get_data as get_data
import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars

logger = logging.getLogger(__name__)


def write_uuids(sheets_to_update):
    """Writes UUIDs back to a collection of Smartsheets

    Args:
        sheets_to_update (dict): The sheets that need a UUID written. Format is
        {
            7208979009955716: { # int, sheet ID
                "sheet_name": "Program Plan", # str, sheet name
                "row_data": {} # dict, row data
            }
        }
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        int: The number of sheets that were updated.
    """
    if not isinstance(sheets_to_update, dict):
        msg = str("Sheets to Update must be type: dict, not"
                  " {}").format(type(sheets_to_update))
        raise TypeError(msg)
    # Reset the counter on each run
    sheets_updated = 0

    # Iterate through each set of sheet IDs and associated data from the
    # dictionary
    for sheet_id, sheet_data in sheets_to_update.items():

        # Assign friendly names to make grokking easier.
        sheet_name = sheet_data['sheet_name']
        row_data = sheet_data['row_data']

        # Create an empty list of rows to write back to the sheet.
        rows_to_write = []

        # Iterate through each set of row IDs and assocaiated cell data,
        # create new row and cell objects to overwrite the existing data,
        # and update the UUID value for the row.
        for row_id, cell_data in row_data.items():
            new_row = smartsheet.models.Row()
            new_row.id = int(row_id)

            new_cell = smartsheet.models.Cell()
            new_cell.column_id = int(cell_data['column_id'])
            new_cell.value = cell_data['uuid']

            new_row.cells.append(new_cell)
            rows_to_write.append(new_row)

        # Finally, write updated cells back to Smartsheet
        if rows_to_write:
            msg = str("Writing {} rows back to Sheet ID: {} "
                      "| Sheet Name: {}").format(len(rows_to_write),
                                                 sheet_id, sheet_name)
            logging.debug(msg)
            smartsheet_api.write_rows_to_sheet(rows_to_write, int(sheet_id),
                                               write_method="update")
            sheets_updated += 1
        else:
            msg = str("No UUID updates required for Sheet ID: "
                      "{} | Sheet Name: {}").format(sheet_id, sheet_name)
            logging.debug(msg)
    return sheets_updated


def write_jira_index_cell_links(project_sub_index,
                                index_sheet=app_vars.dev_jira_idx_sheet):
    """For each sheet in the destination sheet index, parse through the rows,
       determine if cells need to be linked, create cell links and then write
       the rows back to the sheet.

    Args:
        project_sub_index (dict): The list of projects that have a
                                  UUID:Jira Ticket map.
        index_sheet (int): The Jira Index Sheet to write cell links to.
            Defaults to the Dev Jira Index Sheet

    Returns:
        bool: True if any links were written, False if no data was
              written back to any sheet.
    """
    if not isinstance(project_sub_index, dict):
        msg = str("Project sub-index must be type: dict, not"
                  " {}").format(type(project_sub_index))
        raise TypeError(msg)
    if not project_sub_index:
        msg = str("Project sub-index cannot be empty")
        raise ValueError(msg)
    for k, v in project_sub_index.items():
        if not isinstance(k, (str, type(None))):
            msg = str("Project sub-index key (UUID) must be a str or None"
                      "not value: {} | type: {}").format(k, type(k))
            raise ValueError(msg)
        if not isinstance(v, str):
            msg = str("Project sub-index value (Jira Ticket) must be a string,"
                      " not value: {} | type: {} | IndexDump {}"
                      "").format(v, type(v), project_sub_index)
            raise ValueError(msg)

    # Create a copy of the project_sub_index so that we don't alter any
    # other function's data set.
    # Remove all None keys from the dict so we have only valid UUID:Ticket
    project_data_copy = project_sub_index.copy()
    for k in project_data_copy.keys():
        if not k:
            project_data_copy.pop('k', None)

    # Create a list of columns that will be cell linked.
    columns_to_link = [app_vars.jira_col, app_vars.status_col,
                       app_vars.task_col, app_vars.assignee_col]

    # Create smaller indexes from the copy to speed up processing
    dest_sheet_index = build_data.dest_indexes(project_data_copy)[0]
    jira_index_sheet, jira_index_col_map, jira_index_rows = \
        get_data.load_jira_index(index_sheet)

    # Iterate through each sheet ID in the smaller sheet index.
    for sheet_id in dest_sheet_index.keys():
        # Get the sheet data for the ID.
        dest_sheet = smartsheet_api.get_sheet(sheet_id, minutes=0)

        # Build a column map for easier column name to ID reference
        dest_col_map = helper.get_column_map(dest_sheet)

        # Create an empty list of cell links to update.
        cell_links_to_update = []

        # Iterate through each row in the sheet.
        for row in dest_sheet.rows:
            # Get the value of the Jira Ticket cell and validate that there
            # is a value in the cell.
            jira_cell = helper.get_cell_data(
                row, app_vars.jira_col, dest_col_map)
            if jira_cell is None or jira_cell.value is None:
                logging.debug(
                    "Jira Ticket not found in Dest Sheet row. Skipping")
                continue

            # Set a friendly variable names, validate that the row ID is
            # present in the sheet, and create a new row with the cell
            # links.
            try:
                idx_row_id = jira_index_rows[jira_cell.value]
            except KeyError:
                logging.debug(
                    "{} not found in Row Index. Skipping"
                    "".format(jira_cell.value))
                continue

            new_row = build_data.build_row(row, columns_to_link,
                                           dest_col_map,
                                           jira_index_sheet,
                                           jira_index_col_map,
                                           idx_row_id)
            if new_row:
                cell_links_to_update.append(new_row)
                msg = str("Writing {} cells to Row ID: {} | "
                          "Sheet Name: {}."
                          "").format(len(new_row.cells),
                                     new_row.id,
                                     dest_sheet.name)
                logging.debug(msg)
            else:
                continue

        # Write back new cell links to the Sheet
        if cell_links_to_update:
            msg = str("Writing {} cell link rows back to Sheet ID: {} | "
                      "Sheet Name: {}."
                      "").format(len(cell_links_to_update), dest_sheet.id,
                                 dest_sheet.name)
            logging.info(msg)

            smartsheet_api.write_rows_to_sheet(cell_links_to_update,
                                               dest_sheet,
                                               write_method="update")
            return msg
        else:
            msg = str("No Jira Ticket updates needed for Sheet ID: {} | "
                      "Sheet Name {}.").format(dest_sheet.id,
                                               dest_sheet.name)
            logging.info(msg)
            return msg


# def write_predecessor_dates(src_data, project_data_index):
#     """Ensure predecessor start dates are updated across all linked sheets,
#        but only if the new start date is != the existing start date.

#     Args:
#         src_data (dict): Row data from the write_uuid_cell_links.
#         project_data_index (dict): The dict of UUIDs and row data pulled
#                                    from every project sheet.

#     Returns:
#         bool: True if the Start Date in the earliest predecessor was
#               written back via API. False if the Start Date was not
#               written due to failure.
#     """
#     if not isinstance(src_data, dict):
#         msg = str("Source data must be type: dict, not"
#                   " {}").format(type(src_data))
#         raise TypeError(msg)
#     if not isinstance(project_data_index, dict):
#         msg = str("Sheets to Update must be type: dict, not"
#                   " {}").format(type(project_data_index))
#         raise TypeError(msg)
#     for k, v in src_data.items():
#         if not isinstance(v, (str, type(None))):
#             msg = str("{} in project data index is {} not str or None."
#                       "").format(k, type(v))
#             raise ValueError(msg)
#     for col in app_vars.sheet_columns:
#         if col not in src_data.keys():
#             msg = str("Column: {} was not found in the source data keys"
#                       "").format(col)
#             raise ValueError(msg)

#     # Create friendly names for sheet ID, row ID and start date.
#     dest_sheet_id = src_data[app_vars.uuid_col].split("-")[0]
#     dest_row_id = src_data[app_vars.uuid_col].split("-")[1]
#     start_date = src_data[app_vars.start_col]

#     # Query the API for the sheet data, get the column map, and get the row
#     # data. Include the objectValue so we can see the row predecessor(s).
#     dest_sheet = smartsheet_api.get_sheet(dest_sheet_id)
#     dest_col_map = helper.get_column_map(dest_sheet)
#     dest_row = smartsheet_api.get_row(dest_sheet_id, dest_row_id)

#     # Validate that the start date is useful.
#     # if not start_date:
#     #     logging.debug("Start date is {}".format(start_date))
#     #     return False

#     # Get the start date of the row's predecessor. Verify that they are
#     # different.
#     # TODO: Replace with get_cell_data
#     pred_start_cell = helper.get_cell_data(
#         dest_row, app_vars.start_col, dest_col_map)
#     if pred_start_cell.value == start_date:
#         msg = str("Start date {} matches the start date {} in the "
#                   "predecessor row. No update needed"
#                   "").format(start_date, pred_start_cell.value)
#         logging.debug(msg)
#         return True

#     # Get the predecessor cell values.
#     pred_cell = helper.get_cell_data(
#         dest_row, app_vars.predecessor_col, dest_col_map)

#    # Evaluate the value of the predecessor cell. If it has a value other than
#     # None, get the predecessor row ID and loop. If the new pred_cell value
#     # is None but there is no objectValue, the row doesn't have a predecessor
#     # so we set the destination row ID to the final predecessor ID and break
#     # the loop.

#    # TODO: Handle multiple predecessors. Find earliest predecessor and update
#     # that date, or update every predecessor.
#     predecessor_row = smartsheet_api.get_row(dest_sheet_id, dest_row_id)
#     while pred_cell.value is not None:
#         pred_cell = helper.get_cell_data(predecessor_row,
#                                          app_vars.predecessor_col,
#                                          dest_col_map)
#         # TODO: Replace with get_cell_data
#         pred_start_cell = helper.get_cell_data(
#             dest_row, app_vars.start_col, dest_col_map)

#         if pred_start_cell.value == start_date:
#             msg = str("Start date {} matches the start date {} in the "
#                       "predecessor row. No update needed."
#                       "").format(start_date, pred_start_cell.value)
#             logging.debug(msg)
#             return True
#         elif pred_cell.object_value is None:
#             # Set the destination row ID to the predecessor row and break the
#             # loop even if the cell value is None because the row doesn't
#             # have a predecessor value.
#             dest_row = predecessor_row
#             break
#         else:
#             # Set the destination row ID to the predecessor row ID and loop.
#             cell_dict = json.loads(str(pred_cell))
#             dest_row_id = helper.json_extract(cell_dict, "rowId")
#             dest_row_id = str(dest_row_id).translate(
#                 {ord(i): None for i in "[]'"})
#             predecessor_row = smartsheet_api.get_row(dest_sheet_id,
#                                                      dest_row_id)

#     # Get the value of the destination Start Date cell.
#     dest_start_cell = helper.get_cell_data(
#         dest_row, app_vars.start_col, dest_col_map)

#     try:
#         if dest_start_cell.linkInFromCell is not None:
#             # Follow cell links to final destination. Use project
#             # data index to find the UUID, sheet, row and row data.
#             msg = str("Destination Start Date cell is linked to another "
#                       "cell. Locating next Start Date cell at {} and "
#                       "detecting predecessors."
#                       "").format(dest_start_cell.linkInFromCell)
#             logging.warning(msg)
#             dest_sheet_id = helper.json_extract(dest_start_cell, "sheetId")
#             dest_row_id = helper.json_extract(dest_start_cell, "rowId")
#             dest_sheet = smartsheet_api.get_sheet(dest_sheet_id)
#             dest_col_map = helper.get_column_map(dest_sheet)
#             dest_row = smartsheet_api.get_row(dest_sheet_id, dest_row_id)
#             dest_uuid = helper.get_cell_data(
#                 dest_row, app_vars.uuid_col, dest_col_map)
#             row_data = project_data_index[dest_uuid]
#             write_predecessor_dates(
#                 row_data, project_data_index)
#     except AttributeError:
#         logging.debug("Cell is not linked to another cell. Continuing.")

#     if start_date == dest_start_cell.value:
#         msg = str("Start date {} matches the start date {} in the "
#                   "predecessor row. No update needed."
#                   "").format(start_date, dest_start_cell.value)
#         logging.warning(msg)
#     else:
#         # Create empty cell
#         new_start_date_cell = smartsheet.models.Cell()
#         new_start_date_cell.value = start_date
#         new_start_date_cell.column_id = dest_col_map[app_vars.start_col]

#         # Create a new row and append the updated cell
#         new_row = smartsheet.models.Row()
#         new_row.id = predecessor_row.id
#         new_row.cells.append(new_start_date_cell)

#         # Send the updated row to the destination sheet.
#         smartsheet_api.write_rows_to_sheet(
#             new_row, dest_sheet, write_method="update")
#         msg = str("Uploaded new start date {} to ancestor "
#                   "predecessor").format(start_date)
#         logging.debug(msg)

#         return True
