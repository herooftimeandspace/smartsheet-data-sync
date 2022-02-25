import logging
import os

import smartsheet
from botocore.exceptions import NoCredentialsError

from uuid_module.helper import (chunks, get_secret, get_secret_name,
                                get_timestamp)
from uuid_module.variables import dev_minutes, dev_workspace_id

# Set the SMARTSHEET_ACCESS_TOKEN by pulling from the AWS Secrets API, based
# on the environment variable passed in.
secret_name = get_secret_name()
try:
    os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
except NoCredentialsError or TypeError:
    msg = str("Refresh Isengard credentials")
    logging.error(msg)
    exit()

# Initialize the Smartsheet client and make sure we don't miss any errors.
logging.debug("------------------------")
logging.debug("Initializing Smartsheet Client API")
logging.debug("------------------------")
smartsheet_client = smartsheet.Smartsheet()
smartsheet_client.errors_as_exceptions(True)


# TODO: Handle passing in smartsheet.Sheet objects
def write_rows_to_sheet(rows_to_write, sheet, write_method="add"):
    """
    Args:
        rows_to_write (list): A list of rows and their data to write back to
            the sheet
        sheet (dict): The sheet that contains the rows that need to be added
            or updated
        write_method (str, optional): Whether to add new rows or update
            existing rows. Defaults to "add".

    Raises:
        TypeError: Rows to Write must be a list of row data
        TypeError: Sheet must be either a sheet object (dict) or a sheet ID
            (int)
        TypeError: Write method should be a str, or none if not passed
        ValueError: Rows to write must not be an empty list
    """
    if not isinstance(rows_to_write, list):
        msg = str("Rows to write must be type: list not type {}"
                  "").format(type(rows_to_write))
        raise TypeError(msg)
    if not isinstance(sheet, (dict, int, smartsheet.models.sheet.Sheet)):
        msg = str("Sheet must be type: dict or int not type {}"
                  "").format(type(sheet))
        raise TypeError(msg)
    if not isinstance(write_method, (str, None)):
        msg = str("Write method must be type: str not type {}"
                  "").format(type(write_method))
        raise TypeError(msg)
    if len(rows_to_write) <= 0:
        msg = str("Rows to write must have 1 or more rows in the list, "
                  "not {}").format(len(rows_to_write))
        raise ValueError(msg)

    if isinstance(sheet, (dict, smartsheet.models.sheet.Sheet)):
        sheet_id = int(sheet.id)
        sheet_name = str(sheet.name)
    elif isinstance(sheet, int):
        sheet_id = sheet
        sheet_name = "Sheet Name not provided"
    else:
        msg = "Warning, Type checks passed but sheet is neither a"
        "Smartsheet sheet object, nor an INT."
        logging.warning(msg)
        logging.debug("Dumping data to log")
        msg = str("Rows to Write: {} | Sheet: {} | Write Method: {}"
                  "").format(rows_to_write, sheet, write_method)
        logging.debug(msg)

    if rows_to_write:
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet_id, sheet_name)
        logging.info(msg)

        if rows_to_write and write_method == "add":
            # If over 125 rows need to be written to a single sheet, chunk
            # the rows into segments of 125. Anything over 125 will cause
            # the API to fail.
            if len(rows_to_write) > 125:
                chunked_cells = chunks(rows_to_write, 125)
                for i in chunked_cells:
                    try:
                        result = smartsheet_client.Sheets.add_rows(sheet_id,
                                                                   i)
                    except Exception as e:
                        logging.warning(e.message)
            else:
                try:
                    result = smartsheet_client.Sheets.add_rows(sheet_id,
                                                               rows_to_write)
                except Exception as e:
                    logging.warning(e.message)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result)
            logging.info(msg)
            return result

        elif rows_to_write and write_method == "update":
            if len(rows_to_write) > 125:
                chunked_cells = chunks(rows_to_write, 125)
                for i in chunked_cells:
                    try:
                        result = smartsheet_client.Sheets.\
                            update_rows(sheet_id, i)
                    except Exception as e:
                        logging.warning(e.message)
            else:
                try:
                    result = smartsheet_client.Sheets.\
                        update_rows(sheet_id, rows_to_write)
                except Exception as e:
                    logging.warning(e.message)

            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
            logging.info(msg)
            return result
    else:
        msg = str("No rows added to Sheet ID: "
                  "{} | Sheet Name: {}").format(sheet_id, sheet_name)
        logging.info(msg)
        return None


def get_workspace(workspace_id=dev_workspace_id):
    """Gets all reports, sheets, and dashboards from a given Workspace ID.
    LoadAll = True to get objects from all nested folders in the Workspace.

    Args:
        workspace_id (int, optional): The workspace ID to get data from.
        Defaults to dev_workspace_id.

    Raises:
        TypeError: Workspace ID must be an INT to query the API correctly

    Returns:
        smartsheet.models.Workspace: An application/json object of all objects
        in the workspace
    """
    if not isinstance(workspace_id, (int, list)):
        msg = str("Sheet ID must be type: int or list"
                  "not type: {}").format(type(workspace_id))
        raise TypeError(msg)
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
        return workspace


def get_sheet(sheet_id, minutes=dev_minutes):
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

    if minutes > 0:
        _, modified_since = get_timestamp(minutes)

        sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2,
            rows_modified_since=modified_since)
    elif minutes == 0:
        sheet = smartsheet_client.Sheets.get_sheet(
            sheet_id, include='object_value', level=2)
    else:
        modified_since, _ = get_timestamp(minutes)
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

    row = smartsheet_client.Sheets.get_row(sheet_id, row_id,
                                           include='objectValue')
    return row
