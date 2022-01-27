import logging
import os

import smartsheet

from uuid_module.variables import (dev_jira_idx_sheet, dev_minutes,
                                   dev_workspace_id)

smartsheet_client = smartsheet.Smartsheet()
# Make sure we don't miss any error
smartsheet_client.errors_as_exceptions(True)


def write_to_sheet(rows_to_write, sheet,
                   write_method="add"):
    """Writes rows back to a given sheet

    Args:
        rows_to_write (list): A list of rows and their data to write back to
            the sheet
        sheet (dict): The sheet that contains the rows that need to be added
            or updated
        smartsheet_client (smartsheet.smartsheet()): The Smartsheet client
            required for interacting with the API
        write_method (str, optional): Whether to add new rows or update
            existing rows. Defaults to "add".
    """
    if not isinstance(rows_to_write, list):
        msg = ""

    if rows_to_write and write_method == "add":
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet.id, sheet.name)
        logging.debug(msg)

        try:
            result = smartsheet_client.Sheets.add_rows(int(sheet.id),
                                                       rows_to_write)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
        except smartsheet.exceptions.ApiError as result:
            msg = result
    elif rows_to_write and write_method == "update":
        try:
            result = smartsheet_client.Sheets.update_rows(
                int(sheet.id), rows_to_write)
            msg = str("Smartsheet API responded with the "
                      "following message: {}").format(result.result)
        except smartsheet.exceptions.ApiError as result:
            msg = result
    else:
        msg = str("No rows added to Sheet ID: "
                  "{} | Sheet Name: {}").format(sheet.id, sheet.name)

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
    workspace = smartsheet_client.Workspaces.get_workspace(
        workspace_id, load_all=True)
    return workspace


def get_sheet(sheet_id, modified_since=dev_minutes):
    sheet = smartsheet_client.Sheets.get_sheet(
        sheet_id, include='object_value', level=2,
        rows_modified_since=modified_since)
    return sheet


def get_row(sheet_id, row_id):
    row = smartsheet_client.Sheets.get_row(sheet_id,
                                           row_id,
                                           include='objectValue')
    return row
