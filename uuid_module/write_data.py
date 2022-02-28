import json
import logging
import smartsheet

# import smartsheet
from uuid_module.build_data import build_row, dest_indexes
from uuid_module.get_data import load_jira_index
from uuid_module.helper import (chunks, get_cell_data, get_cell_value,
                                get_column_map, json_extract)
from uuid_module.variables import (assignee_col, jira_col, predecessor_col,
                                   start_col, status_col, task_col, uuid_col)

logger = logging.getLogger(__name__)


def write_uuids(sheets_to_update, smartsheet_client):
    """Writes UUIDs back to a collection of Smartsheets

    Args:
        sheets_to_update (dict): The sheets that need a UUID written
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        int: The number of sheets that were updated.
    """
    if not isinstance(sheets_to_update, dict):
        msg = str("Sheets to Update must be type: dict, not"
                  " {}").format(type(sheets_to_update))
        raise TypeError(msg)
    if not isinstance(smartsheet_client, smartsheet.Smartsheet):
        msg = str("Smartsheet Client must be type: smartsheet.Smartsheet, not"
                  " {}").format(type(smartsheet_client))
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
            new_row = smartsheet_client.models.Row()
            new_row.id = int(row_id)

            new_cell = smartsheet_client.models.Cell()
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
            result = smartsheet_client.Sheets.update_rows(int(sheet_id),
                                                          rows_to_write)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
            logging.debug(msg)
            sheets_updated += 1
        else:
            msg = str("No UUID updates required for Sheet ID: "
                      "{} | Sheet Name: {}").format(sheet_id, sheet_name)
            logging.debug(msg)
    return sheets_updated


def write_jira_index_cell_links(project_sub_index,
                                smartsheet_client):
    """For each sheet in the destination sheet index, parse through the rows,
       determine if cells need to be linked, create cell links and then write
       the rows back to the sheet.

    Args:
        project_sub_index (dict): The list of projects that have a
                                  UUID:Jira Ticket map.
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        bool: True if any links were written, False if no data was
              written back to any sheet.
    """
    if not isinstance(project_sub_index, dict):
        msg = str("Project sub-index must be type: dict, not"
                  " {}").format(type(project_sub_index))
        raise TypeError(msg)
    if not isinstance(smartsheet_client, smartsheet.Smartsheet):
        msg = str("Smartsheet Client must be type: smartsheet.Smartsheet, not"
                  " {}").format(type(smartsheet_client))
        raise TypeError(msg)

    # Create a copy of the project_sub_index so that we don't alter any
    # other function's data set.
    project_data_copy = project_sub_index.copy()

    # Create a list of columns that will be cell linked.
    columns_to_link = [jira_col, status_col, task_col, assignee_col]

    # Create smaller indexes from the copy to speed up processing
    dest_sheet_index = dest_indexes(project_data_copy)[0]
    jira_index_sheet, jira_index_col_map, jira_index_rows = load_jira_index(
        smartsheet_client)

    # Iterate through each sheet ID in the smaller sheet index.
    for sheet_id in dest_sheet_index.keys():
        # Get the sheet data for the ID.
        dest_sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2)

        # Build a column map for easier column name to ID reference
        dest_col_map = get_column_map(dest_sheet)

        # Create an empty list of cell links to update.
        cell_links_to_update = []

        # Iterate through each row in the sheet.
        for row in dest_sheet.rows:
            # Get the value of the Jira Ticket cell and validate that there
            # is a value in the cell.
            jira_cell = get_cell_data(
                row, jira_col, dest_col_map)
            if jira_cell is None or jira_cell.value is None:
                logging.debug(
                    "Jira Ticket not found in Dest Sheet row. Skipping")
                continue
            else:
                # Set a friendly variable names, validate that the row ID is
                # present in the sheet, and create a new row with the cell
                # links.
                jira_value = jira_cell.value
                idx_row_id = jira_index_rows[jira_value]
                if not idx_row_id:
                    logging.debug(
                        "{} not found in Row Index. Skipping"
                        "".format(jira_value))
                    continue
                idx_row_id = str(idx_row_id)
                new_row = build_row(row, columns_to_link, dest_col_map,
                                    jira_index_sheet, jira_index_col_map,
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

            # If over 125 rows need to be written to a single sheet, chunk
            # the rows into segments of 125. Anything over 125 will cause
            # the API to fail.
            if len(cell_links_to_update) > 125:
                chunked_cells = chunks(cell_links_to_update, 125)
                for i in chunked_cells:
                    try:
                        result = smartsheet_client.Sheets.\
                            update_rows(dest_sheet.id, i)
                        logging.debug(result)
                    except Exception as e:
                        logging.warning(e.message)
            else:
                try:
                    result = smartsheet_client.Sheets.\
                        update_rows(dest_sheet.id, cell_links_to_update)
                    logging.debug(result)
                except Exception as e:
                    logging.warning(e.message)
        else:
            msg = str("No Jira Ticket updates needed for Sheet ID: {} | "
                      "Sheet Name {}.").format(dest_sheet.id,
                                               dest_sheet.name)
            logging.info(msg)


def check_uuid(uuid_value, jira_value, uuid_list, jira_data_values):
    """Function to check the UUIDs in the Jira Index.

    Args:
        uuid_value (list): The list of UUIDs to look for
        jira_value (str): Used in logging to associate UUID(s) with a Jira
             ticket
        uuid_list (list): UIDs to check in to see if there's a match
        jira_data_values (list): UUIDs associated with a Jira ticket
                                   from the Jira Index

    Returns:
        bool: False if there is no UUID list or if the UUID is found
              in the UUID list.
        list: uuid_list if the UUID is not found in the uuid_list after
              appending the new UUID, or jira_data_values if the UUID
              value is None
        none: If the 'if' checks fail.
    """
    if not isinstance(uuid_value, list):
        msg = str("UUID Value must be type: list, not"
                  " {}").format(type(uuid_value))
        raise TypeError(msg)
    if not isinstance(jira_value, str):
        msg = str("Jira value must be type: str, not"
                  " {}").format(type(jira_value))
        raise TypeError(msg)
    if not isinstance(uuid_list, list):
        msg = str("UUID list must be type: list, not"
                  " {}").format(type(uuid_list))
        raise TypeError(msg)
    if not isinstance(jira_data_values, list):
        msg = str("Jira data values must be type: list, not"
                  " {}").format(type(jira_data_values))
        raise TypeError(msg)

    # Raise error if none / empty, try-catch the caller
    if uuid_list is None:
        msg = str("UUID list is {}. Cannot process against an empty "
                  "list.").format(uuid_list)
        logging.warning(msg)
        return False
    else:
        uuid_list = uuid_list.split(", ")

    if uuid_value is None:
        msg = str("UUID is {}. Replacing with {} for {}.").format(
            uuid_value, jira_data_values, jira_value)
        logging.debug(msg)
        return jira_data_values
    elif uuid_value is not None:
        uuid_value_list = uuid_value.split(", ")
        if len(uuid_value_list) > 1:
            for uuid in uuid_value_list:
                if uuid not in uuid_list:
                    uuid_list.append(uuid)
                else:
                    return False
            msg = str("Appending {} to {} because it wasn't "
                      "found in the list.").format(uuid, uuid_list)
            logging.debug(msg)
            return uuid_list
        elif len(uuid_value_list) == 1:
            if uuid_value not in uuid_list:
                msg = str("Appending {} to {} because it wasn't "
                          "found in the list.").format(uuid_value, uuid_list)
                logging.debug(msg)
                uuid_list.append(uuid_value)
                return uuid_list
        else:
            return False
    else:
        return None


def write_predecessor_dates(src_data, project_data_index, smartsheet_client):
    """Ensure predecessor start dates are updated across all linked sheets,
       but only if the new start date is != the existing start date.

    Args:
        src_data (dict): Row data from the write_uuid_cell_links.
        project_data_index (dict): The dict of UUIDs and row data pulled
                                   from every project sheet.
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        bool: True if the Start Date in the earliest predecessor was
              written back via API. False if the Start Date was not
              written due to failure.
    """
    if not isinstance(src_data, dict):
        msg = str("Source data must be type: dict, not"
                  " {}").format(type(src_data))
        raise TypeError(msg)
    if not isinstance(project_data_index, dict):
        msg = str("Sheets to Update must be type: dict, not"
                  " {}").format(type(project_data_index))
        raise TypeError(msg)
    if not isinstance(smartsheet_client, smartsheet.Smartsheet):
        msg = str("Smartsheet Client must be type: smartsheet.Smartsheet, not"
                  " {}").format(type(smartsheet_client))
        raise TypeError(msg)

    # Create friendly names for sheet ID, row ID and start date.
    dest_sheet_id = src_data[uuid_col].split("-")[0]
    dest_row_id = src_data[uuid_col].split("-")[1]
    start_date = src_data[start_col]

    # Query the API for the sheet data, get the column map, and get the row
    # data. Include the objectValue so we can see the row predecessor(s).
    dest_sheet = smartsheet_client.Sheets.get_sheet(
        dest_sheet_id, include='object_value', level=2)
    dest_col_map = get_column_map(dest_sheet)
    dest_row = smartsheet_client.Sheets.get_row(dest_sheet_id,
                                                dest_row_id,
                                                include='objectValue')

    # Validate that the start date is useful.
    if not start_date:
        logging.debug("Start date is {}".format(start_date))
        return False

    # Get the start date of the row's predecessor. Verify that they are
    # different.
    pred_start_value = get_cell_value(dest_row, start_col, dest_col_map)
    if pred_start_value == start_date:
        msg = str("Start date {} matches the start date {} in the "
                  "predecessor row. No update needed"
                  "").format(start_date, pred_start_value)
        logging.debug(msg)
        return True

    # Get the predecessor cell values.
    pred_cell = get_cell_data(dest_row, predecessor_col, dest_col_map)

    # Evaluate the value of the predecessor cell. If it has a value other than
    # None, get the predecessor row ID and loop. If the new pred_cell value
    # is None but there is no objectValue, the row doesn't have a predecessor
    # so we set the destination row ID to the final predecessor ID and break
    # the loop.

    # TODO: Handle multiple predecessors. Find earliest predecessor and update
    # that date, or update every predecessor.
    while pred_cell.value is not None:
        predecessor_row = smartsheet_client.Sheets.get_row(
            dest_sheet_id, dest_row_id, include='objectValue')
        pred_cell = get_cell_data(predecessor_row, predecessor_col,
                                  dest_col_map)
        pred_start_value = get_cell_value(dest_row, start_col, dest_col_map)

        if pred_start_value == start_date:
            msg = str("Start date {} matches the start date {} in the "
                      "predecessor row. No update needed."
                      "").format(start_date, pred_start_value)
            logging.debug(msg)
            return True
        elif pred_cell.object_value is None:
            # Set the destination row ID to the predecessor row and break the
            # loop even if the cell value is None because the row doesn't
            # have a predecessor value.
            dest_row = predecessor_row
            break
        else:
            # Set the destination row ID to the predecessor row ID and loop.
            cell_dict = json.loads(str(pred_cell))
            dest_row_id = json_extract(cell_dict, "rowId")
            dest_row_id = str(dest_row_id).translate(
                {ord(i): None for i in "[]'"})

    # Get the value of the destination Start Date cell.
    dest_start_cell = get_cell_data(dest_row, start_col, dest_col_map)

    try:
        if dest_start_cell.linkInFromCell is not None:
            # Follow cell links to final destination. Use project
            # data index to find the UUID, sheet, row and row data.
            msg = str("Destination Start Date cell is linked to another "
                      "cell. Locating next Start Date cell at {} and "
                      "detecting predecessors."
                      "").format(dest_start_cell.linkInFromCell)
            logging.warning(msg)
            dest_sheet_id = json_extract(dest_start_cell, "sheetId")
            dest_row_id = json_extract(dest_start_cell, "rowId")
            dest_sheet = smartsheet_client.Sheets.get_sheet(
                dest_sheet_id, include='object_value', level=2)
            dest_col_map = get_column_map(dest_sheet)
            dest_row = smartsheet_client.Sheets.get_row(dest_sheet_id,
                                                        dest_row_id)
            dest_uuid = get_cell_data(dest_row, uuid_col, dest_col_map)
            row_data = project_data_index[dest_uuid]
            write_predecessor_dates(
                row_data, project_data_index, smartsheet_client)
    except AttributeError:
        logging.debug("Cell is not linked to another cell. Continuing.")

    if start_date == dest_start_cell.value:
        msg = str("Start date {} matches the start date {} in the "
                  "predecessor row. No update needed."
                  "").format(start_date, dest_start_cell.value)
        logging.warning(msg)
    else:
        # Create empty cell
        new_start_date_cell = smartsheet_client.models.Cell()
        new_start_date_cell.value = start_date
        new_start_date_cell.column_id = dest_col_map[start_col]

        # Create a new row and append the updated cell
        new_row = smartsheet_client.models.Row()
        new_row.id = predecessor_row.id
        new_row.cells.append(new_start_date_cell)

        # Send the updated row to the destination sheet.
        result = smartsheet_client.Sheets.update_rows(dest_sheet_id,
                                                      new_row)
        logging.debug(result)
        logging.debug(
            "Uploaded new start date {} to ancestor predecessor".format(
                start_date))
        return True
