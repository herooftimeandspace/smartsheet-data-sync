import json
import logging
from collections import defaultdict
from datetime import datetime
import app.config as config
import pytz


from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp)
import uuid_module.helper as conf
from uuid_module.smartsheet_api import get_sheet, get_workspace
from uuid_module.variables import (dev_jira_idx_sheet, dev_minutes,
                                   dev_workspace_id, jira_col, summary_col,
                                   uuid_col)

logger = logging.getLogger(__name__)

utc = pytz.UTC


def refresh_source_sheets(sheet_ids, minutes=0):
    """Creates a dict of source sheets. If minutes is defined, only gathers
       sheets modified since the minutes value. Otherwise pulls all sheets
       from the workspaces.

    Args:
        smartsheet_client (client): Allows interaction with the Smartsheet API
        sheet_ids (list): The list of Smartsheet sheet IDs to parse
        minutes (int, optional): Number of minutes into the past that the API
                                 should pull sheet and row data, if greater
                                 than 0. Defaults to 0.

    Returns:
        source_sheets (list): The list of sheets, including row data for rows
                              modified since the minutes value, if greater
                              than 0
    """
    if not isinstance(sheet_ids, list):
        raise TypeError("Sheet IDs must be a list of IDs")
    if not all(isinstance(x, int) for x in sheet_ids):
        raise ValueError("One or more values in the list are not type: int")
    if minutes is not None and not isinstance(minutes, int):
        raise TypeError("Minutes must be type: int")
    if minutes is not None and minutes < 0:
        raise ValueError("Minutes must be >= zero")

    source_sheets = []
    for sheet_id in sheet_ids:
        # Query the Smartsheet API for the sheet details
        sheet = get_sheet(sheet_id, minutes)
        source_sheets.append(sheet)
        logging.debug("Loaded Sheet ID: {} | "
                      "Sheet Name: {}".format(sheet.id, sheet.name))
    return source_sheets


def get_all_row_data(source_sheets, columns, minutes):
    """Parses through all source sheets and gets specific data from the
       columns provided.

    Args:
        source_sheets (list): A list of Sheet objects to parse
        columns (list): A list of column names to extract data from.
        minutes (int): The number of minutes to look back when collecting
                       row data.

    Returns:
        dict: Returns a dict of UUIDs and the row values
        none: There is no row data in any source sheet.
    """
    # TODO: Write a test to validated the dictionary structure
    # 7208979009955716-3683235938232196-7010994181433220-202105112138550000,
    # {
    #   "UUID": "7208979009955716-3683235938232196-7010994181433220-
    #            202105112138550000",  # type: str
    #   "Tasks": "Retrospective", # type: str
    #   "Description": None, # type: str
    #   "Status": None, # type: str
    #   "Assigned To": None, # type: str
    #   "Jira Ticket": None, # type: str
    #   "Duration": None, # type: str
    #   "Start": None, # type: str
    #   "Finish": None, # type: str
    #   "Predecessors": "38FS +1w", # type: str
    #   "Summary": "False" # type: str
    #       }
    if not isinstance(source_sheets, list):
        msg = str("Source sheets should be type: list, not {}").format(
            type(source_sheets))
        raise TypeError(msg)
    if not isinstance(columns, list):
        msg = str("Columns should be type: list, not {}").format(type(columns))
        raise TypeError(msg)
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    # Create the empty dict we'll pass back
    all_row_data = {}

    modified_since, _ = get_timestamp(minutes)
    modified_since = utc.localize(modified_since)
    modified_since = modified_since.replace(tzinfo=utc)

    for sheet in source_sheets:
        # Iterate through the columns and map the column ID to the column name
        col_map = get_column_map(sheet)

        for row in sheet.rows:
            summary_cell = get_cell_value(
                row, summary_col, col_map)
            try:
                uuid_cell = get_cell_data(row, uuid_col, col_map)
            except KeyError:
                logging.debug("Sheet ID {} | Sheet Name {} "
                              "doesn't have UUID column. "
                              "Skipping sheet.".format(sheet.id, sheet.name))
                break

            if summary_cell is None:
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell))
                continue
            elif summary_cell == "True":
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell))
                continue

            row_modified = row.modified_at

            # If the row was modified in the last N minutes, add
            # it to the index. Otherwise, skip it.
            if row_modified >= modified_since:
                msg = str("True | Cutoff: {} | Row Modified Date: "
                          "{} | Row Number: {} |Sheet Name: {}").format(
                    modified_since, row_modified, row.row_number,
                    sheet.name)
                logging.debug(msg)
                row_data = {}
                all_row_data[uuid_cell.value] = row_data
            else:
                msg = str("False | Cutoff: {} | Row Modified Date: "
                          "{} | Row Number: {} |Sheet Name: {}").format(
                    modified_since, row_modified, row.row_number,
                    sheet.name)
                logging.debug(msg)
                continue

            # Iterate through each column passed in.
            for col_name in columns:
                if col_name in col_map.keys():
                    msg = str(
                        "{} found in Column Map keys".format(col_name))
                    logging.debug(msg)

                    # Check if the cell exists, using the row ID and the
                    # column name. If the cell exists, append its value
                    # to the row_data list.
                    cell = get_cell_value(row, col_name, col_map)
                    row_data[col_name] = cell

                    msg = str("Appending {}: {} to dict").format(
                        col_name, cell)
                    logging.debug(msg)

                else:
                    # Otherwise, log an error. There's a mismatch between
                    # the column names.
                    msg = str("Error. Sheet {} doesn't have a {} column. "
                              "Check column names to verify they match"
                              "").format(sheet.name, col_name)
                    logging.info(msg)
            if row_data:
                all_row_data[uuid_cell.value].update(row_data)
    if all_row_data:
        # Send the full list back.
        return all_row_data
    else:
        return None


def get_blank_uuids(source_sheets):
    """For all rows that need a UUID generated, creates nested dicts with the
       necessary data to generate the UUID.

    Args:
        source_sheets (list): A list of Sheet objects

    Returns:
        dict: A nested set of dictionaries
        none: There are no sheets to update.
    """
    if not isinstance(source_sheets, list):
        msg = str("Source Sheets should be type: list not type {}"
                  "").format(type(source_sheets))
        raise TypeError(msg)

    # Create an empty dict of sheets to update
    sheets_to_update = {}

    # Iterate through each sheet in the source_sheets dict
    for sheet in source_sheets:
        logging.debug("Loaded " + str(len(sheet.rows)) + " rows from sheet: "
                      + str(sheet.id) + " | Sheet Name: " + sheet.name)
        col_map = get_column_map(sheet)
        try:
            column_id = col_map[uuid_col]
        except KeyError:
            logging.debug("Sheet ID {} | Sheet Name {} "
                          "doesn't have UUID column. "
                          "Skipping sheet. (KeyError)".format(sheet.id,
                                                              sheet.name))
            continue
        # Create an empty dict for rows to update inside the sheet
        rows_to_update = {}

        # Iterate through each row in the sheet
        for row in sheet.rows:
            # Get the existing UUID value and the timestamp when the row was
            # created.
            uuid_value = get_cell_value(row, uuid_col, col_map)
            created_at = str(row.created_at)

            # Strip out all characters except the numbers in the timestamp.
            created_at = created_at.translate(
                {ord(i): None for i in '+-T:Z '})

            # Format the UUID as sheet_id, row_id, column_id, and modified
            # timestamp, separated by dashes.
            uuid = str("{}-{}-{}-{}").format(sheet.id,
                                             row.id, column_id, created_at)

            # Check if the UUID already exists. If there's a match, skip
            # updating the cell / row.
            if uuid_value == uuid:
                msg = str("Cell at Column Name: {} | Row ID: {} | "
                          "Row Number: {}, {} matches existing UUID. "
                          "Cell skipped.").format(uuid_col, row.id,
                                                  row.row_number, uuid)
                logging.debug(msg)
                continue
            elif uuid_value != uuid:
                msg = str("Cell at Column Name: {} | Row ID: {} | "
                          "Row Number: {} has an existing value of {}. "
                          "Tagging for update. "
                          "{}.").format(uuid_col, row.id, row.row_number,
                                        uuid_value, uuid)
                logging.debug(msg)
                rows_to_update[row.id] = {
                    "column_id": col_map[uuid_col], "uuid": uuid}
            else:
                msg = str("There was an issue parsing rows in the sheet. "
                          "Sheet ID: {} | Sheet Name: {}"
                          "").format(sheet.id, sheet.name)
                logging.warning(msg)
                msg = str("Dumping Row Data: {}").format(row)
                logging.debug(msg)
                continue

        # Collect all rows to update and parse them into a dict of sheets
        # to update.
        if rows_to_update:
            sheets_to_update[sheet.id] = {
                "sheet_name": sheet.name, "row_data": rows_to_update}
    if sheets_to_update:
        return sheets_to_update
    else:
        return None


def load_jira_index(index_sheet=dev_jira_idx_sheet):
    """Create indexes on the Jira index rows. Pulls from the Smartsheet API
       every time to get the most up-to-date version of the sheet data.

    Args:
        index_sheet (Sheet): The Jira index sheet to load. Defaults to Dev.

    Raises:
        TypeError: Validates smartsheet_client is a Smartsheet Client object.

    Returns:
        sheet: A Smartsheet Sheet object that includes all data for the Jira
               Index Sheet
        dict: A dictionary containing mapped column IDs to column names
        dict: A dictionary containing the Jira ticket as the key and the
              row ID as the value.

    """
    if not isinstance(index_sheet, int):
        msg = str("Index Sheet should be type: int not type {}"
                  "").format(type(index_sheet))
        raise TypeError(msg)

    jira_index_sheet = get_sheet(index_sheet, minutes=0)
    msg = str("{} rows loaded from sheet ID: {} | Sheet name: {}"
              "").format(len(jira_index_sheet.rows), jira_index_sheet.id,
                         jira_index_sheet.name)
    logging.debug(msg)
    jira_index_col_map = get_column_map(jira_index_sheet)

    # Create a dict of rows where the values are lists.
    jira_index_rows = defaultdict(list)

    # Iterate through the rows on the Index sheet. If there's a Jira ticket
    # in the row, return it and its details.
    for row in jira_index_sheet.rows:
        jira_cell = get_cell_data(
            row, jira_col, jira_index_col_map)
        if jira_cell is None:
            logging.debug("Jira cell doesn't exist. Skipping.")
            continue
        elif jira_cell.value is None:
            logging.debug("Jira value doesn't exist. Skipping.")
            continue
        else:
            jira_value = jira_cell.value
            jira_index_rows[jira_value] = row.id
    return jira_index_sheet, jira_index_col_map, jira_index_rows


def get_sub_indexes(project_data):
    """Read all rows from the full project data index. If the Jira
       column exists in the dict values, create two sub-indexes.

    Args:
        project_data (dict): The full set of UUIDs:Column data
                             pulled from the API.

    Returns:
        dict: jira_sub_index in the form of Jira Ticket: [UUID(s)] (list)
        dict: project_sub_index in the form of UUID: Jira Ticket (str)
    """
    if not isinstance(project_data, dict):
        msg = str("Project data must be type: dict not type: {}."
                  "").format(type(project_data))
        raise TypeError(msg)

    jira_sub_index = defaultdict(list)
    project_sub_index = defaultdict(list)

    try:
        for k, v in project_data.items():
            if jira_col in v.keys():
                if v[jira_col] is not None:
                    # UUID: Jira Ticket
                    project_sub_index[k] = v[jira_col]
                    ticket = v[jira_col]
                    jira_sub_index[ticket].append(k)
    except AttributeError as e:
        msg = str("Project Data is {}. Aborting "
                  "creating sub-indexes. {}").format(project_data, e)
        logging.warning(msg)
        return

    return jira_sub_index, project_sub_index


def get_all_sheet_ids(minutes=dev_minutes,
                      workspace_id=dev_workspace_id,
                      index_sheet=dev_jira_idx_sheet):
    """Get all the sheet IDs from every sheet in every folder, subfolder and
       workspace as defined in the workspace_id.

    Args:
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        list: A list of all sheet IDs across every workspace
    """
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if not isinstance(workspace_id, (int, list)):
        msg = str("Workspace ID should be type: int or list, not {}").format(
            type(workspace_id))
        raise TypeError(msg)
    if not isinstance(index_sheet, int):
        msg = str("Jira Index Sheet should be type: int, not {}").format(
            type(index_sheet))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    # Get the workspace Smartsheet object from the workspace_id
    # configured in our variables.
    modified_since, _ = get_timestamp(minutes)
    modified_since = utc.localize(modified_since)
    modified_since = modified_since.replace(tzinfo=utc)
    sheet_ids = []

    for ws_id in workspace_id:
        # TEST with smartsheet_api.py
        workspace = get_workspace(ws_id)

        if workspace.folders:
            ws = str(workspace)
            ws_json = json.loads(ws)

            for subfolder in ws_json['folders']:
                try:
                    for sheet in subfolder['sheets']:
                        modified_at = sheet['modifiedAt']
                        head, sep, tail = modified_at.partition('+')
                        sheet_modified = datetime.strptime(
                            head, '%Y-%m-%dT%H:%M:%S')
                        sheet_modified = utc.localize(sheet_modified)
                        sheet_modified = sheet_modified.replace(tzinfo=utc)

                        # If the sheet was modified in the last N minutes, add
                        # it to the index. Otherwise, skip it.
                        if sheet_modified >= modified_since:
                            msg = str("True | Cutoff: {} | Sheet Modified "
                                      "Date: {} | Sheet Name: {}").format(
                                modified_since, sheet_modified, sheet['name'])
                            logging.debug(msg)
                            sheet_ids.append(sheet['id'])
                        else:
                            msg = str("False | Cutoff: {} | Sheet Modified "
                                      "Date: {} | Sheet Name: {}").format(
                                modified_since, sheet_modified, sheet['name'])
                            logging.debug(msg)
                            continue
                # Handle empty workspaces
                except KeyError as e:
                    msg = str("Dictionary key {} not found in "
                              "subfolders for workspace ID {}").format(e,
                                                                       ws_id)
                    logging.debug(msg)

    # Don't include the JIRA index sheet or the Push Tickets sheet as part of
    # the sheet collection, if present.
    sheets_to_remove = [conf.index_sheet, conf.push_tickets_sheet]
    for sheet_id in sheets_to_remove:
        try:
            sheet_ids.remove(sheet_id)
            msg = str("{} removed from Sheet ID list").format(sheet_id)
            logging.debug(msg)
        except ValueError:
            logging.debug(
                "{} not found in Sheet IDs list".format(sheet_id))

    return sheet_ids
