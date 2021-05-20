import json
import logging
import os

import smartsheet
from uuid_module import get_cell_value, get_column_id, get_column_map
from uuid_module.build_module import build_row, dest_indexes
from uuid_module.get_module import get_all_sheet_ids, load_jira_index
from uuid_module.helper import (get_cell_value, get_column_id, get_column_map,
                                json_extract)
from uuid_module.variables import (assignee_col, jira_col, jira_idx_sheet,
                                   predecessor_col, sheet_columns, start_col,
                                   status_col, summary_col, task_col, uuid_col)

logger = logging.getLogger(__name__)

# assignee_col = os.getenv('ASSIGNEE_COL')
# jira_col = os.getenv('JIRA_COL')
# jira_idx_sheet = os.getenv('JIRA_IDX_SHEET')
# predecessor_col = os.getenv('PREDECESSOR_COL')
# sheet_columns = os.getenv('SHEET_COLUMNS')
# start_col = os.getenv('START_COL')
# status_col = os.getenv('STATUS_COL')
# summary_col = os.getenv('SUMMARY_COL')
# task_col = os.getenv('TASK_COL')
# uuid_col = os.getenv('UUID_COL')


# sheets_to_update is a dict in the format
def write_uuids(sheets_to_update, smartsheet_client):
    sheets_updated = 0
    for sheet_id, sheet_data in sheets_to_update.items():
        sheet_name = sheet_data['sheet_name']
        row_data = sheet_data['row_data']

        rows_to_write = []
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
            msg = str("No updates required for Sheet ID: "
                      "{} | Sheet Name: {}").format(sheet_id, sheet_name)
            logging.debug(msg)
    return sheets_updated


# Main function. For each Sheet in the destination sheet index,
# parse through rows, determine if cells need to be linked, create
# cell links and then write the rows back to the sheet.
def link_from_index(project_sub_index,
                    smartsheet_client):
    # index_data_copy = jira_index_data.copy()
    project_data_copy = project_sub_index.copy()

    columns_to_link = [jira_col, status_col, task_col, assignee_col]

    dest_sheet_index = dest_indexes(project_data_copy)[0]
    jira_index_sheet, jira_index_col_map, jira_index_rows = load_jira_index(
        smartsheet_client)

    for sheet_id in dest_sheet_index.keys():
        dest_sheet = smartsheet_client.Sheets.get_sheet(sheet_id)
        dest_col_map = get_column_map(dest_sheet)
        cell_links_to_update = []

        for row in dest_sheet.rows:
            jira_cell = get_column_id(
                row, jira_col, dest_col_map)
            if jira_cell is None or jira_cell.value is None:
                logging.debug(
                    "Jira Ticket not found in Dest Sheet row. Skipping")
                continue
            else:
                jira_value = jira_cell.value
                idx_row_id = jira_index_rows[jira_value]
                if not idx_row_id:
                    logging.debug(
                        "{} not found in Row Index. Skipping"
                        "".format(jira_value))
                    continue
                new_row = build_row(row, columns_to_link, dest_col_map,
                                    jira_index_sheet, jira_index_col_map,
                                    idx_row_id, smartsheet_client)
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
            result = smartsheet_client.Sheets.update_rows(dest_sheet.id,
                                                          cell_links_to_update)
            logging.debug(result)
        else:
            msg = str("No updates needed for Sheet ID: {} | "
                      "Sheet Name {}.").format(dest_sheet.id,
                                               dest_sheet.name)
            logging.debug(msg)

    return True


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
    """
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


def write_jira_uuids(jira_sub_index, project_sub_index, smartsheet_client):
    """Checks each row of the index sheet for the Jira ticket
       and UUID cells. Compares that against the UUIDs and Jira tickets of each
       destination sheet. If there is a match, do nothing. If there isn't a
       match, append or create the UUID value and write the UUID cell back to
       the Index Sheet.

    Args:
        jira_sub_index (dict): [description]
        project_sub_index (dict): [description]
        smartsheet_client (Object): [description]
    """
    # Make copies for safekeeping, yeeeesss
    index_data_copy = jira_sub_index.copy()
    # project_data_copy = project_sub_index.copy()

    jira_index_sheet = smartsheet_client.Sheets.get_sheet(jira_idx_sheet)
    jira_index_col_map = get_column_map(jira_index_sheet)
    idx_rows_to_update = []

    for row in jira_index_sheet.rows:
        jira_value = get_cell_value(row, jira_col, jira_index_col_map)
        uuid_value = get_cell_value(row, uuid_col, jira_index_col_map)

        if not jira_value:
            logging.debug("Jira value is {}. Skipping row.".format(jira_value))
            continue

        idx_new_row = smartsheet_client.models.Row()
        idx_new_row.id = row.id

        if jira_value in index_data_copy.keys():
            msg = str("Jira ticket {} matches a key in sheet index").format(
                jira_value)
            logging.debug(msg)
            uuid_new_cell = smartsheet_client.models.Cell()
            uuid_new_cell.column_id = int(
                jira_index_col_map[uuid_col])
            jira_data_values = index_data_copy[jira_value]
            for uuid_list in jira_data_values:
                uuid_new_value = check_uuid(uuid_value,
                                            jira_value,
                                            uuid_list,
                                            jira_data_values)

                if not uuid_new_value:
                    msg = str("Found {} within the index for Jira Ticket {}. "
                              "Moving to next row").format(uuid_list,
                                                           jira_value)
                    logging.debug(msg)
                elif uuid_new_value is not None:
                    # logging.debug("Check UUID returned TRUTHY")
                    # Strip [] and ' from the string for future parsing.
                    uuid_new_value = str(uuid_new_value).\
                        translate({ord(i): None for i in "[]'"})
                    uuid_new_cell.value = uuid_new_value
                    # Append the new cell to the row after all the parameters
                    # have been set
                    idx_new_row.cells.append(uuid_new_cell)
                    # Append the new row to the list of rows to update
                    idx_rows_to_update.append(idx_new_row)
                    break
                else:
                    msg = str("Unknown error determining if UUID list value "
                              "{} is in the Jira index at ticket {}."
                              "").format(uuid_list, jira_value)
                    logging.warning(msg)

    logging.debug("Done checking index sheet for UUID updates.")

    # Write back new UUIDs to the Index
    if idx_rows_to_update:
        msg = str("Writing {} index rows back to Sheet ID: {} "
                  "Sheet Name: {}").format(len(idx_rows_to_update),
                                           jira_index_sheet.id,
                                           jira_index_sheet.name)
        logging.info(msg)
        result = smartsheet_client.Sheets.update_rows(jira_idx_sheet,
                                                      idx_rows_to_update)
        logging.debug(result)
    else:
        msg = str("No updates needed for Sheet ID: {} | "
                  "Sheet Name {}.").format(jira_index_sheet.id,
                                           jira_index_sheet.name)
        logging.debug(msg)


def write_predecessor_dates(src_data, project_data_index, smartsheet_client):
    """Ensure predecessor start dates are updated across all linked sheets,
       but only if the new start date is != the existing start date.

    Args:
        src_data (dict): Row data from the write_uuid_cell_links.
                         See below for expected format.
        project_data_index (dict): The dict of UUIDs and row data pulled
                                   from every project sheet.
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        bool: True if the Start Date in the earliest predecessor was
              written back via API. False if the Start Date was not
              written due to failure.

    Format of the src_data should be:
    {
        "UUID": "7208979009955716-3683235938232196-
                7010994181433220-202105112138550000",  # Type: str
        "Tasks": "Retrospective", # Type: str
        "Description": "Thoughts on how the project went.",  # Type: str
        "Status": "In Progress",  # Type: str
        "Assigned To": "link@twitch.tv",  # Type: str
        "Jira Ticket": "ING-12342",  # Type: str
        "Duration": None,  # Type: str
        "Start": "2021-03-31T08:00:00",  # Type: str
        "Finish": "2021-03-31T08:00:00",  # Type: str
        "Predecessors": "38FS +1w",  # Type: str
        "Summary": "False"  # Type: str
    }
    """
    dest_sheet_id = src_data[uuid_col].split("-")[0]
    dest_row_id = src_data[uuid_col].split("-")[1]
    start_date = src_data[start_col]

    dest_sheet = smartsheet_client.Sheets.get_sheet(dest_sheet_id)
    dest_col_map = get_column_map(dest_sheet)
    dest_row = smartsheet_client.Sheets.get_row(dest_sheet_id,
                                                dest_row_id,
                                                include='objectValue')

    if not start_date:
        logging.debug("Start date is {}".format(start_date))
        return False
    pred_start_value = get_cell_value(dest_row, start_col, dest_col_map)
    if pred_start_value == start_date:
        msg = str("Start date {} matches the start date {} in the "
                  "predecessor row. No update needed"
                  "").format(start_date, pred_start_value)
        logging.debug(msg)
        return True

    pred_cell = get_column_id(dest_row, predecessor_col, dest_col_map)

    # Evaluate the value of the predecessor cell. If it has a value other than
    # None, get the predecessor row ID and loop. If the new pred_cell value
    # is None but there is no objectValue, the row doesn't have a predecessor
    # so we set the destination row ID to the final predecessor ID and break
    # the loop.
    while pred_cell.value is not None:
        predecessor_row = smartsheet_client.Sheets.get_row(
            dest_sheet_id, dest_row_id, include='objectValue')
        pred_cell = get_column_id(predecessor_row, predecessor_col,
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

    dest_start_cell = get_column_id(dest_row, start_col, dest_col_map)

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
            dest_sheet = smartsheet_client.Sheets.get_sheet(dest_sheet_id)
            dest_col_map = get_column_map(dest_sheet)
            dest_row = smartsheet_client.Sheets.get_row(dest_sheet_id,
                                                        dest_row_id)
            dest_uuid = get_column_id(dest_row, uuid_col, dest_col_map)
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
