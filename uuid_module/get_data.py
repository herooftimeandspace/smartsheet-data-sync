import json
import logging
from collections import defaultdict
from datetime import datetime
import pytz

from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp)
from uuid_module.variables import (jira_col, jira_idx_sheet, summary_col,
                                   uuid_col, workspace_id, minutes)

logger = logging.getLogger(__name__)

utc = pytz.UTC


def get_all_row_data(source_sheets, columns, smartsheet_client):
    """Parses through all source sheets and gets specific data from the
       columns provided.

    Args:
        source_sheets (list): A list of Sheet objects to parse
        columns (list): A list of column names to extract data from.
        smartsheet_client (Object): The Smartsheeet client, required for
                                    reading and writing to the Smartsheet API

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
    if source_sheets is None:
        raise ValueError
    elif columns is None:
        raise ValueError

    # Create the empty dict we'll pass back
    all_row_data = {}

    for sheet in source_sheets:
        # Iterate through the columns and map the column ID to the column name
        col_map = get_column_map(sheet)

        for row in sheet.rows:
            summary_cell = get_cell_value(
                row, summary_col, col_map)
            uuid_cell = get_cell_data(row, uuid_col, col_map)

            if summary_cell is None:
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell))
                continue
            elif summary_cell == "True":
                logging.debug("Summary row is {}. Continuing to next "
                              "row.".format(summary_cell))
                continue

            if uuid_cell is None:
                logging.debug("Sheet ID {} | Sheet Name {} "
                              "doesn't have UUID column. "
                              "Skipping sheet.".format(sheet.id, sheet.name))
                break

            row_data = {}
            all_row_data[uuid_cell.value] = row_data

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


def get_blank_uuids(source_sheets, smartsheet_client):
    """For all rows that need a UUID generated, creates nested dicts with the
       necessary data to generate the UUID.

    Args:
        source_sheets (list): A list of Sheet objects
        smartsheet_client (Object): The Smartsheet client to call the API

    Returns:
        dict: A nested set of dictionaries
        none: There are no sheets to update.
    """
    # TODO: Write a test to validate the dict.
    # 7637702645442436,  (Sheet ID, int)
    # {
    #     "sheet_name": "Cloudwatch: Distribution Project Plan", # type: str
    #     "row_data": {  # type: dict
    #         4733217466279812: { (Row ID, int)
    #             "column_id": 2745267022784388, (int)
    #             "uuid": "7637702645442436-4733217466279812-
    #                      2745267022784388-202105112340380000" (str)
    #         }
    #     }
    # }
    if source_sheets is None:
        raise ValueError

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
                msg = str("Cell at Column Name: {} and Row ID: "
                          "{} matches existing UUID. Cell skipped."
                          "").format(uuid_col, row.id)
                logging.debug(msg)
            elif uuid_value != uuid:
                msg = str("Cell at column name: {} and row ID: {} has an "
                          "existing value of {}. Tagging for update."
                          "{}.").format(uuid_col, row.id, uuid_value, uuid)
                logging.debug(msg)
                rows_to_update[row.id] = {
                    "column_id": col_map[uuid_col], "uuid": uuid}
            else:
                msg = str("There was an issue parsing rows in the sheet. "
                          "Sheet ID: {} | Row Data: {}").format(sheet.id, row)
                logging.warning(msg)

        # Collect all rows to update and parse them into a dict of sheets
        # to update.
        if rows_to_update:
            sheets_to_update[sheet.id] = {
                "sheet_name": sheet.name, "row_data": rows_to_update}
    if sheets_to_update:
        return sheets_to_update
    else:
        return None


def load_jira_index(smartsheet_client):
    """Create indexes on the Jira index rows. Pulls from the Smartsheet API
       every time to get the most up-to-date version of the sheet data.

    Args:
        smartsheet_client (Object): The Smartsheet client to query the API

    Returns:
        dict: A dictionary containing the Jira ticket as the key and the
              row ID as the value.
    """
    jira_index_sheet = smartsheet_client.Sheets.get_sheet(jira_idx_sheet)
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
        elif jira_cell.value is None:
            logging.debug("Jira value doesn't exist. Skipping.")
        else:
            jira_value = jira_cell.value
            jira_index_rows[jira_value] = row.id
    return jira_index_sheet, jira_index_col_map, jira_index_rows


def get_sub_indexs(project_data):
    """Read all rows from the full project data index. If the Jira
       column exists in the dict values, create two sub-indexes.

    Args:
        project_data (dict): The full set of UUIDs:Column data
                             pulled from the API.

    Returns:
        dict: jira_sub_index in the form of Jira Ticket: [UUID(s)] (list)
        dict: project_sub_index in the form of UUID: Jira Ticket (str)
    """

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


def get_all_sheet_ids(smartsheet_client):
    """Get all the sheet IDs from every sheet in every folder, subfolder and
       workspace as defined in the workspace_id.

    Args:
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        list: A list of all sheet IDs across every workspace
    """

    # Get the workspace Smartsheet object from the workspace_id
    # configured in our variables.
    modified_since, _ = get_timestamp(minutes)
    modified_since = utc.localize(modified_since)
    modified_since = modified_since.replace(tzinfo=utc)
    sheet_ids = []

    for ws_id in workspace_id:
        workspace = smartsheet_client.Workspaces.get_workspace(
            ws_id, load_all=True)

        if workspace.folders:
            ws = str(workspace)
            ws_json = json.loads(ws)
            for subfolder in ws_json['folders']:
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
                        msg = str("True | Cutoff: {} | Sheet Modified Date: "
                                  "{} | Sheet Name: {}").format(
                            modified_since, sheet_modified, sheet['name'])
                        logging.debug(msg)
                        sheet_ids.append(sheet['id'])
                    else:
                        msg = str("False | Cutoff: {} | Sheet Modified Date: "
                                  "{} | Sheet Name: {}").format(
                            modified_since, sheet_modified, sheet['name'])
                        logging.debug(msg)
                        continue

    # Don't include the JIRA index sheet as
    # part of the sheet collection, if present.
    try:
        sheet_ids.remove(jira_idx_sheet)
    except ValueError:
        logging.debug(
            "{} not found in Sheet IDs list".format(jira_idx_sheet))

    return sheet_ids


# def get_ws_folder_map(workspace):
#     """Get all of the folder IDs within the root Workspace, for each
#        workspace provided.

#     Args:
#         workspace (Workspace object): The workspace to parse for folder
#                                       IDs.

#     Returns:
#         list: A list of folder IDs found in the workspace.
#         none: There are no folders in the workspace.
#     """

#     # Create an empty list where we can store Workspace folder IDs.
#     ws_folder_map = []

#     # Check if there are folders in the Workspace. Append all folder IDs to
#     # the list.
#     if workspace.folders:
#         logging.debug("Importing Folders from Workspace ID: "
#                       + str(workspace.id) + " | " + workspace.name)
#         for folders in workspace.folders:
#             logging.debug("Appended Folder ID: " + str(folders.id) + " | "
#                           + folders.name + " to ws_folder_map.")
#             ws_folder_map.append(folders.id)
#         return ws_folder_map
#     else:
#         logging.debug("No folders in workspace.")
#         return None


# def get_folder_sheet_map(folder_map, smartsheet_client):
#     """Get all sheets from each folder in the folder map.

#     Args:
#         folder_map (list): A list of folder IDs found in the workspace
#         smartsheet_client (Object): The Smartsheet client to interact
#                                     with the API

#     Returns:
#         list: A list of sheet IDs from every folder in the workspace.
#         none: There are no sheets in the folder.
#     """

#     # Create an empty list where we can store the sheet IDs.
#     folder_sheet_map = []

#     # Check if we have folders to iterate through.
#     if not folder_map:
#         logging.debug("Folder map is empty. Skipping.")
#         return None
#     else:
#         # Iterate through each folder ID in the list.
#         for folder_id in folder_map:
#             try:
#                 # Get the contents of the folder
#                 folder = smartsheet_client.Folders.get_folder(folder_id)

#             except smartsheet_client.exceptions.ApiError as e:
#                 logging.debug("Error on API request.")
#                 logging.debug("Status Code: " + e.statusCode
#                               + " Reason: " + e.Reason
#                               + " Message: " + e.message())
#                 return

#             else:
#                 logging.debug("Importing SheetIDs from FolderID: "
#                               + str(folder_id) + " | Folder Name: "
#                               + folder.name)
#                 # Iterate through each sheet in the folder, and append it
#                 # to the list.
#                 minutes = 65
#                 modified_since, _ = get_timestamp(minutes)
#                 modified_since = utc.localize(modified_since)
#                 modified_since = modified_since.replace(tzinfo=utc)
#                 for sheet in folder.sheets:
#                     sheet_id = str(sheet.id)
#                     sheet_modified = sheet.modified_at
#                     sheet_modified = sheet_modified.replace(tzinfo=utc)

#                     # If the sheet was modified in the last N minutes, add it
#                     # to the index. Otherwise, skip it.
#                     if sheet_modified >= modified_since:
#                         folder_sheet_map.append(sheet_id)
#                     else:
#                         continue
#         logging.info("Loaded " + str(len(folder_sheet_map))
#                      + " sheets from " + str(len(folder_map)) + " folders.")
#     return folder_sheet_map


# def get_ws_sheet_map(workspace_id, smartsheet_client):
#     """Get all Sheet IDs from the root workspace, not located in a folder.

#     Args:
#         workspace_id (str): The ID or the workspace
#         smartsheet_client (Object): The Smartsheet client to interact
#                                     with the API

#     Returns:
#         list: A list of all sheet IDs in the root workspace
#         none: There are no sheets in the root of the workspace.
#     """

#     # Create an empty list for the workspace sheet IDs.
#     ws_sheet_map = []
#     workspace = smartsheet_client.Workspaces.get_workspace(workspace_id)
#     logging.info("Importing Sheet IDs from WorkspaceID: " + str(workspace_id)
#                  + " | Workspace Name: " + workspace.name)

#     # Check if there are sheets in the workspace
#     if workspace.sheets:
#         # Iterate through each sheet, and append its ID to the list.
#         for sheet in workspace.sheets:
#             sheet_id = str(sheet.id)
#             ws_sheet_map.append(sheet_id)
#         logging.info("Loaded " + str(len(ws_sheet_map))
#                      + " sheets from " + str(workspace_id)
#                      + " | Workspace Name: " + workspace.name)
#         return ws_sheet_map
#     else:
#         logging.debug("No sheets found in workspace.")
#         return None


# def get_subfolder_map(folder_ids, smartsheet_client):
#     """Loop through folder IDs and find any subfolders. Appends the new
#        folder ID to the list, if found. Flattens the list of folder IDs
#        from many nested IDs to a single list of all folders.

#     Args:
#         folder_ids (list): The List of folder IDs to parse through
#         smartsheet_client (Object): The Smartsheet client to interact
#                                     with the API

#     Returns:
#         list: A flat list of all folder IDs located within other
#               folders.
#     """

#     # Create an empty list for the subfolder IDs
#     subfolder_map = []

#     # Check if there are subfolders
#     if not folder_ids:
#         logging.debug("Sub-folder map is empty. Skipping.")
#         return None
#     else:
#         # Iterate through each folder ID
#         # TODO: Create a branch and fix this nonsense? It seems to work.
#         for folder in folder_ids:
#             try:
#                 # Query the API and return all the subfolders
#                 subfolders = smartsheet_client.\
#                     Folders.list_folders(folder,
#                                          include_all=True)
#             except smartsheet_client.exceptions.ApiError:
#                 logging.debug("Subfolder data is None")

#                 # Append the folder ID to the list
#                 subfolder_map.append(folder)
#             else:
#                 # Iterate through the subfolders and append the folder ID
#                 # to the list.
#                 for subfolder in subfolders.data:
#                     subfolder_map.append(subfolder.id)
#                     msg = str("Appended Folder ID: {} | Folder Name: {} to "
#                               "subfolder map.").format(subfolder.id,
#                                                        subfolder.name)
#                     logging.debug(msg)
#     return subfolder_map
