import logging

import smartsheet

import uuid_module.helper as helper
import uuid_module.variables as app_vars


def set_smartsheet_client():
    """Set the SMARTSHEET_ACCESS_TOKEN by pulling from the AWS Secrets API,
       based on the environment variable passed in.
       Defer importing the token and secrets until all modules are loaded.
    """
    global smartsheet_client
    import app.config as config
    smartsheet_client = config.smartsheet_client


def write_rows_to_sheet(rows_to_write, sheet, write_method="add"):
    """
    Args:
        rows_to_write (list): A list of rows and their data to write back to
            the sheet
        sheet (dict, int, smartsheet.models.sheet): The sheet that contains
            the rows that need to be added or updated
        write_method (str, optional): Whether to add new rows or update
            existing rows. Defaults to "add".

    Raises:
        TypeError: Rows to Write must be a list of row data
        TypeError: Row in Rows to Write must be a smartsheet.model.Row
        TypeError: Sheet must be either a sheet object (dict) or a sheet ID
            (int)
        TypeError: Write method should be a str, or none if not passed
        ValueError: Write method must be either 'add' or 'update'. Method is
            case sensitive
        ValueError: Rows to write must not be an empty list
    """
    if not isinstance(rows_to_write, list):
        msg = str("Rows to write must be type: list not type {}"
                  "").format(type(rows_to_write))
        raise TypeError(msg)
    if not isinstance(sheet, (dict, int, smartsheet.models.sheet.Sheet)):
        msg = str("Sheet must be type: smartsheet.models.Sheet, dict or int, "
                  "not type {}").format(type(sheet))
        raise TypeError(msg)
    if not isinstance(write_method, (str, type(None))):
        msg = str("Write method must be type: str or None, not type {}"
                  "").format(type(write_method))
        raise TypeError(msg)
    if write_method not in ["add", "update"]:
        msg = str("Write method must be 'add' or 'update', not {}. "
                  "Write method is case-sensitive").format(write_method)
        raise ValueError(msg)
    if not rows_to_write:
        msg = str("Rows to write must have 1 or more rows in the list, "
                  "not {}").format(len(rows_to_write))
        raise ValueError(msg)
    for row in rows_to_write:
        if not isinstance(row, smartsheet.models.Row):
            msg = "Rows must be a smartsheet.models.Row object"
            raise TypeError(msg)

    # Set friendly names and correct types
    if isinstance(sheet, (dict, smartsheet.models.Sheet)):
        sheet_id = int(sheet.id)
        sheet_name = str(sheet.name)
    elif isinstance(sheet, int):
        sheet_id = sheet
        sheet_name = "Sheet Name not provided."

    if rows_to_write:
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet_id, sheet_name)
        logging.info(msg)
        # TODO: Handle results better (get HTTP codes, messages)
        if rows_to_write and write_method == "add":
            # If over 125 rows need to be written to a single sheet, chunk
            # the rows into segments of 125. Anything over 125 will cause
            # the API to fail.
            if len(rows_to_write) > 125:
                chunked_cells = helper.chunks(rows_to_write, 125)
                for i in chunked_cells:
                    try:
                        result = smartsheet_client.Sheets.add_rows(sheet_id,
                                                                   i)
                        msg = str("Smartsheet API responded with the "
                                  "following message: {} | Result Code: {}."
                                  "").format(result.message,
                                             result.result_code)
                        logging.info(msg)
                    except Exception as result:
                        logging.warning(result.message)
                        return result
                return result
            else:
                try:
                    result = smartsheet_client.Sheets.add_rows(sheet_id,
                                                               rows_to_write)
                    msg = str("Smartsheet API responded with the "
                              "following message: {} | Result Code: {}."
                              "").format(result.message,
                                         result.result_code)
                    logging.info(msg)
                    return result
                except Exception as result:
                    logging.warning(result.message)
                    return result
        # TODO: Handle results better (get HTTP codes, messages)
        elif rows_to_write and write_method == "update":
            # If over 125 rows need to be written to a single sheet, chunk
            # the rows into segments of 125. Anything over 125 will cause
            # the API to fail.
            if len(rows_to_write) > 125:
                chunked_cells = helper.chunks(rows_to_write, 125)
                for i in chunked_cells:
                    try:
                        result = smartsheet_client.Sheets.\
                            update_rows(sheet_id, i)
                        msg = str("Smartsheet API responded with the "
                                  "following message: {} | Result Code: {}."
                                  "").format(result.message,
                                             result.result_code)
                        logging.info(msg)
                    except Exception as result:
                        logging.warning(result.message)
                        return result
                return result
            else:
                try:
                    result = smartsheet_client.Sheets.\
                        update_rows(sheet_id, rows_to_write)
                    msg = str("Smartsheet API responded with the "
                              "following message: {} | Result Code: {}."
                              "").format(result.message, result.result_code)
                    logging.info(msg)
                    return result
                except Exception as result:
                    logging.warning(result.message)
                    return result

    else:
        msg = str("No rows added to Sheet ID: "
                  "{} | Sheet Name: {}").format(sheet_id, sheet_name)
        logging.info(msg)
        return None


def get_workspace(workspace_id=app_vars.dev_workspace_id):
    """Gets all reports, sheets, and dashboards from a given Workspace ID.
    LoadAll = True to get objects from all nested folders in the Workspace.

    Args:
        workspace_id (int, optional): The workspace ID to get data from.
        Defaults to dev_workspace_id.

    Raises:
        TypeError: Workspace ID must be an INT to query the API correctly
        ValueError: Workspace ID must not be an empty list.
        ValueError: Workspace ID must be a positive integer

    Returns:
        smartsheet.models.Workspace: An application/json object of all objects
        in the workspace
    """
    if not isinstance(workspace_id, (int, list)):
        msg = str("Workspace ID must be type: int or list"
                  "not type: {}").format(type(workspace_id))
        raise TypeError(msg)
    if not workspace_id:
        msg = str("Workspace ID must not be an empty list.")
        raise ValueError(msg)
    if isinstance(workspace_id, int):
        if not workspace_id > 0:
            msg = str("Workspace ID must be a positive integer.")
            raise ValueError(msg)
    if isinstance(workspace_id, list):
        for i in workspace_id:
            if not isinstance(i, int):
                msg = str("Workspace ID must be type: int "
                          "not type: {}").format(type(workspace_id))
                raise TypeError(msg)
            if not i > 0:
                msg = str("Workspace ID must be a positive integer.")
                raise ValueError(msg)

    if isinstance(workspace_id, int):
        workspace = smartsheet_client.Workspaces.get_workspace(
            workspace_id, load_all=True)
        return workspace
    elif isinstance(workspace_id, list):
        workspaces = []
        for ws_id in workspace_id:
            workspace = smartsheet_client.Workspaces.get_workspace(
                ws_id, load_all=True)
            workspaces.append(workspace)
        return workspaces


def get_sheet(sheet_id, minutes=app_vars.dev_minutes):
    """Gets a sheet from the Smartsheet API via Sheet ID.

    Args:
        sheet_id (int): The ID of the sheet to pull from the API
        minutes (int, optional): Limits sheets pulled from the API to the
        number of mintes in the past that the sheet was last modified. Defaults
        to dev_minutes.

    Raises:
        TypeError: Sheet ID must be an INT to query the API correctly
        TypeError: Minutes must be an INT to calculate how far in the past
        the API should pull data

    Returns:
        smartsheet.models.Sheet: Returns the sheet in dict/json format for
        further manipulation
    """
    if not isinstance(sheet_id, int):
        msg = str("Sheet ID must be type: int "
                  "not type: {}").format(type(sheet_id))
        raise TypeError(msg)
    if not isinstance(minutes, int):
        msg = str("Minutes must be type: int "
                  "not type: {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Time travel to the future not supported. Minutes must be "
                  "greater than or equal to zero.").format(type(minutes))
        raise ValueError(msg)

    # If minutes is greater than zero, calculate n minutes into the past and
    # return the datetime. Pass that to the API to only get rows modified
    # since the datetime.
    if minutes > 0:
        _, modified_since = helper.get_timestamp(minutes)

        sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2,
            rows_modified_since=modified_since)
    # If minutes is zero, get all rows regardless of modified date
    elif minutes == 0:
        sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2)
    # If somehow minutes is less than zero but doesn't raise a ValueError,
    # default to dev_minutes and return the sheet.
    else:
        modified_since, _ = helper.get_timestamp(app_vars.dev_minutes)
        sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2,
            rows_modified_since=modified_since)
    return sheet


def get_row(sheet_id, row_id):
    """Gets row data from a given sheet ID and row ID from the Smartsheet API

    Args:
        sheet_id (int): The ID of the sheet to query
        row_id (int): THe ID of the row to query

    Raises:
        TypeError: Sheet ID must be an INT to query the API correctly
        TypeError: Row ID must be an INT to query the API correctly
        ValueError: Sheet ID must be a positive integer
        ValueError: Row ID must be a positive integer

    Returns:
        smartsheet.models.Row: Returns the row data in dict/json format
        for further manipulation
    """
    if not isinstance(sheet_id, int):
        msg = str("Sheet ID must be type: int "
                  "not type: {}").format(type(sheet_id))
        raise TypeError(msg)
    if not isinstance(row_id, int):
        msg = str("Row ID must be type: int "
                  "not type: {}").format(type(row_id))
        raise TypeError(msg)
    if not sheet_id > 0:
        msg = str("Jira Index row ID must not be zero or negative."
                  "").format()
        raise ValueError(msg)
    if not row_id > 0:
        msg = str("Jira Index row ID must not be zero or negative."
                  "").format()
        raise ValueError(msg)

    row = smartsheet_client.Sheets.get_row(sheet_id, row_id,
                                           include='objectValue')
    return row


def get_cell_history(sheet_id, row_id, column_name, column_map,
                     page_size=1, page=1):
    cell_history = smartsheet_client.Cells.get_cell_history(
        sheet_id, row_id, column_map[column_name], page_size, page
    )
    history = cell_history.data
    return history
