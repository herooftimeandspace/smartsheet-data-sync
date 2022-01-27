import logging
import os
from typing import Type

import smartsheet

from uuid_module.variables import (dev_jira_idx_sheet, dev_minutes,
                                   dev_workspace_id)
from uuid_module.helper import get_timestamp

smartsheet_client = smartsheet.Smartsheet()
# Make sure we don't miss any error
smartsheet_client.errors_as_exceptions(True)


def write_rows_to_sheet(rows_to_write, sheet,
                        write_method="add"):
    """Writes rows back to a given sheet

    Args:
        rows_to_write (list): A list of rows and their data to write back to
            the sheet
        sheet (dict): The sheet that contains the rows that need to be added
            or updated
        write_method (str, optional): Whether to add new rows or update
            existing rows. Defaults to "add".
    """
    if not isinstance(rows_to_write, list):
        msg = ""
        raise TypeError(msg)
    if not isinstance(sheet, (dict, int)):
        msg = ""
        raise TypeError(msg)
    if not isinstance(write_method, (str, None)):
        msg = ""
        raise TypeError(msg)

    if isinstance(sheet, dict):
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

    if rows_to_write and write_method == "add":
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet_id, sheet_name)
        logging.debug(msg)

        try:
            result = smartsheet_client.Sheets.add_rows(sheet_id,
                                                       rows_to_write)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
        except smartsheet.exceptions.ApiError as result:
            msg = result
    elif rows_to_write and write_method == "update":
        try:
            result = smartsheet_client.Sheets.update_rows(
                sheet_id, rows_to_write)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
        except smartsheet.exceptions.ApiError as result:
            msg = result
    else:
        msg = str("No rows added to Sheet ID: "
                  "{} | Sheet Name: {}").format(sheet_id, sheet_name)

    logging.info(msg)


# def get_jira_index_sheet(smartsheet_client, index_sheet=dev_jira_idx_sheet):
#     if not isinstance(smartsheet_client, smartsheet.Smartsheet):
#         msg = str("Smartsheet Client must be type: smartsheet.Smartsheet, "
#                   "not type: {}").format(type(smartsheet_client))
#         raise TypeError(msg)
#     index_sheet = smartsheet_client.Sheets.get_sheet(
#         index_sheet, include='object_value', level=2)
#     return index_sheet


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
    if not isinstance(workspace_id, int):
        msg = str("Sheet ID must be type: int "
                  "not type: {}").format(type(workspace_id))
        raise TypeError(msg)
    workspace = smartsheet_client.Workspaces.get_workspace(
        workspace_id, load_all=True)
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

    row = smartsheet_client.Sheets.get_row(sheet_id,
                                           row_id,
                                           include='objectValue')
    return row
