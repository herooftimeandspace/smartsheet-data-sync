import json
import logging
from collections import defaultdict
from datetime import datetime

import app.config as config
import pytz
import smartsheet

import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars

logger = logging.getLogger(__name__)

utc = pytz.UTC


def refresh_source_sheets(sheet_ids, minutes=0):
    """Creates a dict of source sheets. If minutes is defined, only gathers
       sheets modified since the minutes value. Otherwise pulls all sheets
       from the workspaces.

    Args:
        sheet_ids (list): The list of Smartsheet sheet IDs to parse
        minutes (int, optional): Number of minutes into the past that the API
                                 should pull sheet and row data, if greater
                                 than 0. Defaults to 0.

    Raises:
        TypeError: Sheet IDs must be a list
        ValueError: Sheet IDs must not be an empty list
        ValueError: IDs in Sheet IDs must be an int
        ValueError: IDs in Sheet IDs must be positive integers
        TypeError: Minutes must be an int
        ValueError: Minutes must be greater than or equal to zero

    Returns:
        source_sheets (list): The list of sheets, including row data for rows
                              modified since the minutes value, if greater
                              than 0
    """
    if not isinstance(sheet_ids, list):
        raise TypeError("Sheet IDs must be a list of IDs")
    # if not sheet_ids:
    #     raise ValueError("Sheet IDs list must not be empty")
    if not all(isinstance(x, int) for x in sheet_ids):
        raise ValueError("One or more values in the list are not type: int")
    if not all(x > 0 for x in sheet_ids):
        raise ValueError("IDs in sheet_ids must be positive integers")
    if minutes is not None and not isinstance(minutes, int):
        raise TypeError("Minutes must be type: int")
    if minutes is not None and minutes < 0:
        raise ValueError("Minutes must be >= zero")

    source_sheets = []
    for sheet_id in sheet_ids:
        # Query the Smartsheet API for the sheet details
        sheet = smartsheet_api.get_sheet(sheet_id, minutes)
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

    Raises:
        TypeError: Source sheets must be a list
        TypeError: Columns must be a list
        TypeError: Minutes must be an int
        ValueError: Minutes must be greater than or equal to zero

    Returns:
        dict: Returns a dict of UUIDs and the row values
        None: There is no row data in any source sheet.
    """
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
    if not minutes >= 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)
    if not all(isinstance(x, smartsheet.models.Sheet) for x in source_sheets):
        raise ValueError("One or more values in the Source Sheets are not "
                         "type: smartsheet.models.Sheet")
    if not all(isinstance(x, str) for x in columns):
        raise ValueError("One or more values in Columns are not type: str")

    # Create the empty dict we'll pass back
    all_row_data = {}

    modified_since, _ = helper.get_timestamp(minutes)
    modified_since = utc.localize(modified_since)
    modified_since = modified_since.replace(tzinfo=utc)

    for sheet in source_sheets:
        # Iterate through the columns and map the column ID to the column name
        col_map = helper.get_column_map(sheet)
        if app_vars.uuid_col not in col_map.keys():
            msg = str("Sheet ID {} | Sheet Name {} "
                      "doesn't have UUID column. "
                      "Skipping sheet.").format(sheet.id, sheet.name)
            logging.debug(msg)
            continue

        for row in sheet.rows:
            summary_cell = helper.get_cell_data(
                row, app_vars.summary_col, col_map)
            uuid_cell = helper.get_cell_data(row, app_vars.uuid_col, col_map)

            # Get Cell Data returned None, skip this row.
            # TODO: Break on this sheet. None results mean there's no
            # Summary column.
            if not summary_cell:
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell))
                continue
            # Get Cell Data returned a cell, and the value is str True or
            # bool True. Skip summary rows.
            if summary_cell.value == "True" or summary_cell.value:
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell.value))
                continue

            # Get cell data returned a cell, and the value is either str None
            # or bool False. Use this row.
            if not summary_cell.value or summary_cell.value == "None":
                logging.debug("Summary row is {}. Using this row. "
                              "".format(summary_cell.value))
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
                if col_name not in col_map.keys():
                    msg = str("Error. Sheet {} doesn't have a {} column. "
                              "Check column names to verify they match"
                              "").format(sheet.name, col_name)
                    logging.debug(msg)
                    continue

                # Check if the cell exists, using the row ID and the
                # column name. If the cell exists, append its value
                # to the row_data list.
                cell = helper.get_cell_data(row, col_name, col_map)
                if not cell:
                    continue

                row_data[col_name] = cell.value

                msg = str("Appending {}: {} to row_data dict").format(
                    col_name, cell.value)
                logging.debug(msg)

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

    Raises:
        TypeError: Source sheets must be a list
        ValueError: Sheets in the list must be a smartsheet.models.Sheet object

    Returns:
        dict: A nested set of dictionaries
        None: There are no sheets to update.
    """
    if not isinstance(source_sheets, list):
        msg = str("Source Sheets should be type: list not type {}"
                  "").format(type(source_sheets))
        raise TypeError(msg)
    if not source_sheets:
        msg = str("Source Sheets list is empty.")
        logging.info(msg)
        return None
    for sheet in source_sheets:
        if not isinstance(sheet, smartsheet.models.Sheet):
            msg = "Sheets in Source Sheets must be Smartsheet Sheet objects"
            raise ValueError(msg)

    # Create an empty dict of sheets to update
    sheets_to_update = {}

    # Iterate through each sheet in the source_sheets dict
    for sheet in source_sheets:
        logging.debug("Loaded " + str(len(sheet.rows)) + " rows from sheet: "
                      + str(sheet.id) + " | Sheet Name: " + sheet.name)
        col_map = helper.get_column_map(sheet)
        try:
            column_id = col_map[app_vars.uuid_col]
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
            uuid_cell = helper.get_cell_data(row, app_vars.uuid_col, col_map)
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
            if uuid_cell.value == uuid:
                msg = str("Cell at Column Name: {} | Row ID: {} | "
                          "Row Number: {}, {} matches existing UUID. "
                          "Cell skipped.").format(app_vars.uuid_col, row.id,
                                                  row.row_number, uuid)
                logging.debug(msg)
                continue
            elif uuid_cell.value != uuid:
                msg = str("Cell at Column Name: {} | Row ID: {} | "
                          "Row Number: {} has an existing value of {}. "
                          "Tagging for update. "
                          "{}.").format(app_vars.uuid_col, row.id,
                                        row.row_number,
                                        uuid_cell.value, uuid)
                logging.debug(msg)
                rows_to_update[row.id] = {
                    "column_id": col_map[app_vars.uuid_col], "uuid": uuid}
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


def load_jira_index(index_sheet_id=app_vars.dev_jira_idx_sheet):
    """Create indexes on the Jira index rows. Pulls from the Smartsheet API
       every time to get the most up-to-date version of the sheet data.

    Args:
        index_sheet (int): The Jira index sheet to load. Defaults to Dev.

    Raises:
        TypeError: Index Sheet must be an int.
        ValueError: Index Sheet ID should be one of the sheet IDs defined in
            the variables.py file

    Returns:
        sheet: A Smartsheet Sheet object that includes all data for the Jira
               Index Sheet
        dict: A dictionary containing mapped column IDs to column names
        dict: A dictionary containing the Jira ticket as the key and the
              row ID as the value.

    """
    # TODO: Refactor for smartsheet.sheet object / dict instead of Int
    if not isinstance(index_sheet_id, int):
        msg = str("Index Sheet should be type: int not type {}"
                  "").format(type(index_sheet_id))
        raise TypeError(msg)
    if index_sheet_id not in [app_vars.dev_jira_idx_sheet,
                              app_vars.prod_jira_idx_sheet]:
        msg = str("Index Sheet ID is {} but it should be {} or {}"
                  "").format(index_sheet_id, app_vars.prod_jira_idx_sheet,
                             app_vars.dev_jira_idx_sheet)
        raise ValueError(msg)

    jira_index_sheet = smartsheet_api.get_sheet(index_sheet_id, minutes=0)
    msg = str("{} rows loaded from sheet ID: {} | Sheet name: {}"
              "").format(len(jira_index_sheet.rows), jira_index_sheet.id,
                         jira_index_sheet.name)
    logging.debug(msg)
    jira_index_col_map = helper.get_column_map(jira_index_sheet)

    # Create a dict of rows where the values are lists.
    jira_index_rows = {}

    # Iterate through the rows on the Index sheet. If there's a Jira ticket
    # in the row, return it and its details.
    for row in jira_index_sheet.rows:
        jira_cell = helper.get_cell_data(
            row, app_vars.jira_col, jira_index_col_map)
        if jira_cell is None:
            logging.debug("Jira cell doesn't exist. Skipping.")
            continue
        elif jira_cell.value is None:
            logging.debug("Jira value doesn't exist. Skipping.")
            continue
        else:
            # {Jira Ticket (str): Row ID (int)}
            jira_index_rows[jira_cell.value] = row.id
    return jira_index_sheet, jira_index_col_map, jira_index_rows


def get_sub_indexes(project_data):
    """Read all rows from the full project data index. If the Jira
       column exists in the dict values, create two sub-indexes.

    Args:
        project_data (dict): The full set of UUIDs:Column data
                             pulled from the API.

    Raises:
        TypeError: Project data must be a dictionary
        ValueError: Project data must not be empty

    Returns:
        dict: jira_sub_index in the form of Jira Ticket: [UUID(s)] (list)
        dict: project_sub_index in the form of UUID: Jira Ticket (str)
    """
    if not isinstance(project_data, dict):
        msg = str("Project data must be type: dict not type: {}."
                  "").format(type(project_data))
        raise TypeError(msg)
    if not project_data:
        msg = str("Project data cannot be empty")
        raise ValueError(msg)

    jira_sub_index = defaultdict(list)
    project_sub_index = defaultdict(list)

    for k, v in project_data.items():
        if app_vars.jira_col in v.keys():
            if v[app_vars.jira_col] is not None:
                # UUID: Jira Ticket
                project_sub_index[k] = v[app_vars.jira_col]
                ticket = v[app_vars.jira_col]
                jira_sub_index[ticket].append(k)

    return jira_sub_index, project_sub_index


def get_all_sheet_ids(minutes=app_vars.dev_minutes,
                      workspace_id=app_vars.dev_workspace_id,
                      index_sheet=app_vars.dev_jira_idx_sheet):
    """Get all the sheet IDs from every sheet in every folder, subfolder and
       workspace as defined in the workspace_id.

    Args:
        minutes (int): Number of minutes into the past to filter sheets and
                       rows. Defaults to Dev
        workspace_id (int, list): One or more Workspaces to check for changes.
                                  Defaults to Dev
        index_sheet (int): The Index Sheet ID. Defaults to Dev

    Raises:
        TypeError: Minutes must be an Int
        TypeError: Workspace ID must be an Int or list of Ints
        TypeError: Index Sheet must be an Int
        ValueError: Minutes must be a positive integer or 0
        ValueError: IDs in the Workspace IDs list must be ints

    Returns:
        list: A list of Sheet IDs (Int) across every workspace
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
    for id in workspace_id:
        if not isinstance(id, int):
            msg = str("Workspace ID in list should be type: int, not {}"
                      "").format(type(id))
            raise ValueError(msg)
        if not id > 0:
            msg = str("Workspace ID in list should be a positive integer"
                      "").format(type(id))
            raise ValueError(msg)

    # Get the workspace Smartsheet object from the workspace_id
    # configured in our variables.
    modified_since, _ = helper.get_timestamp(minutes)
    modified_since = utc.localize(modified_since)
    modified_since = modified_since.replace(tzinfo=utc)
    sheet_ids = []

    for ws_id in workspace_id:
        workspace = smartsheet_api.get_workspace(ws_id)

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
    sheets_to_remove = [config.index_sheet, config.push_tickets_sheet]
    for id in sheets_to_remove:
        if id in sheet_ids:
            sheet_ids.remove(id)
            msg = str("{} removed from Sheet ID list").format(id)
            logging.debug(msg)
        else:
            msg = str("{} not found in Sheet IDs list").format(id)
            logging.debug(msg)

    return sheet_ids
