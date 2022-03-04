import logging
import re
import app.config as config
import smartsheet
import time

from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                has_cell_link, truncate)
from uuid_module.smartsheet_api import get_sheet, write_rows_to_sheet
from uuid_module.variables import (dev_minutes,
                                   uuid_col)

project_columns = ["Summary", "Tasks", "Issue Type", "Jira Ticket",
                   "Parent Ticket", "Program", "Initiative", "Team", "UUID",
                   "Predecessors", "ParentUUID", "Project Key",
                   "Parent Issue Type", "Inject", "KTLO"]
jira_index_columns = ["Tasks", "Issue Type", "Jira Ticket", "Issue Links",
                      "Project Key", "Components", "Labels", "Epic Link",
                      "Epic Name", "Summary", "Inject", "KTLO", "UUID"]


def refresh_sheets(minutes=dev_minutes):
    """Refreshes the list of sheets in all workspaces. Captures any sheet
       modified after 'minutes'

    Args:
        minutes (int, optional): The number of minutes used to filter out
        sheets. Defaults to dev_minutes.

    Raises:
        TypeError: Minutes must be an int
        ValueError: Minutes must be a positive integer or 0

    Returns:
        source_sheets (list): All sheets modified in the last N minutes
        index_sheet (smartsheet.Sheet): The Jira Index sheet
        index_col_map (dict): The column map of the Jira Index Sheet in the
                              form of Column Name: Column ID
    """
    from uuid_module.get_data import (get_all_sheet_ids,
                                      refresh_source_sheets)
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    sheet_ids = get_all_sheet_ids(minutes, config.workspace_id,
                                  config.index_sheet)
    msg = str("Sheet IDs object type {}, object values {}").format(
        type(sheet_ids), sheet_ids)
    logging.debug(msg)
    source_sheets = refresh_source_sheets(sheet_ids, minutes)

    # TODO: Load index sheet and kick off 2 functions. 1: Create new tickets
    # 2: Copy created tickets to program sheets via UUID
    index_sheet = get_sheet(config.index_sheet)
    index_col_map = get_column_map(index_sheet)
    return source_sheets, index_sheet, index_col_map


# TODO: Refactor for the full chain of issue types across multiple Jira
# projects
# TODO: Handle creating and linking the Bug issue type
# TODO: Handle indentation. See API docs
# https://smartsheet-platform.github.io/api-docs/#specify-row-location
# specifically parent_id, sibling_id
def form_rows(row_dict, col_map):
    """Forms new rows to write to the Jira Push Tickets Sheet

    Args:
        row_dict (dict): A dictionary of all rows to parse
        index_col_map (dict): The column map of the Jira Index Sheet in the
                              form of Column Name: Column ID

    Raises:
        TypeError: Row Dictionary should be a dict
        TypeError: Index Column Map should be a dict
        ValueError: Row Dictionary should not be empty
        ValueError: Index Column Map must not be empty

    Returns:
        list: A list of rows and the associated data to upload into
              Smartsheet.
    """
    if not isinstance(row_dict, dict):
        msg = str("Row Dictionary should be type dict, not type {}"
                  "").format(type(row_dict))
        raise TypeError(msg)
    if not isinstance(col_map, dict):
        msg = str("Index Col Map should be type dict, not type {}"
                  "").format(type(col_map))
        raise TypeError(msg)
    if not row_dict:
        msg = str("Row Dictionary should not be empty")
        raise ValueError(msg)
    if not col_map:
        msg = str("Index Column Map should not be empty")
        raise ValueError(msg)

    rows_to_add = []
    for _, data in row_dict.items():
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        for col_name, value in data.items():
            if col_name not in jira_index_columns:
                # Skip writting columns the Index sheet doesn't have
                continue
            if not value:
                # Skip null value columns
                continue
            if col_name == "Jira Ticket" and value in ("Create", "create"):
                # Skip the Jira Ticket column we're trying to create
                # when adding to the Index sheet
                continue

            try:
                col_id = col_map[col_name]
            except KeyError:
                msg = str("KeyError when looking up column name {} in "
                          "the Jira Index Column Map").format(col_name)
                logging.debug(msg)
                # Move to next data set, create the row with data that works
                continue
            new_row.cells.append({
                'column_id': col_id,
                'object_value': value
            })
            msg = str("ColName: {}, ColID: {}, Value: {}"
                      "").format(col_name, col_id, value)
            logging.debug(msg)

        # Manually create labels, epic name, epic link, all other data for
        # use in Jira here
        labels = [data['Program'], data['Initiative'], data['Team']]
        if data['Inject']:
            labels.append("Inject")
        if data['KTLO']:
            labels.append("KTLO")
        # Spaces are not supported in Labels. Replace with dashes. For labels
        # that already have dashes, replace with a single dash rather than the
        # previous pattern.
        if labels:
            labels = [sub.replace(' ', '-') for sub in labels]
            labels = [sub.replace('---', '-') for sub in labels]
            new_row.cells.append({
                'column_id': col_map['Labels'],
                'object_value': {
                    'objectType': "MULTI_PICKLIST",
                    'values': labels
                }
            })
        if data['Issue Type'] in ("Story", "Task") and \
                data['Parent Issue Type'] == "Epic":
            epic_link = data['Parent Ticket']
            new_row.cells.append({
                'column_id': col_map['Epic Link'],
                'object_value': epic_link
            })
        elif data['Parent Issue Type'] in ("Epic", "Story", "Project", "Task"):
            ticket = data['Parent Ticket']
            issue_link = str("implements {}").format(ticket)
            new_row.cells.append({
                'column_id': col_map['Issue Links'],
                'object_value': issue_link
            })
        if data['Issue Type'] == "Epic":
            epic_name = data['Tasks']
            new_row.cells.append({
                'column_id': col_map['Epic Name'],
                'object_value': epic_name
            })
        components = ["Autogenerated by Smartsheet", "Sync to Smartsheet"]
        new_row.cells.append({
            'column_id': col_map['Components'],
            'object_value': {
                'objectType': "MULTI_PICKLIST",
                'values': components
            }
        })

        rows_to_add.append(new_row)
    return rows_to_add


def link_jira_index_to_sheet(source_sheets, index_sheet, index_col_map):
    """Uses the UUID column to identify the row that originally pushed data
       into Jira. Copies the Jira Ticket back into the Program Plan

    Args:
        sheet (smartsheet.Sheet): The Sheet to push the Jira Ticket into
        # sheet_col_map (dict): The column map of the destination sheet
        index_sheet (smartsheet.Sheet): The Jira Index Sheet
        index_col_map (dict): The column map of the Jira Index Sheet

    Raises:
        TypeError: Sheet must be a list of sheets
        TypeError: Index Sheet must be a dict or smartsheet.Sheet object
        TypeError: Index Column Map must be a dict
    """
    if not isinstance(source_sheets, list):
        msg = str("Sheet should be a list, not {}"
                  "").format(type(source_sheets))
        raise TypeError(msg)
    if not isinstance(index_sheet, (dict, smartsheet.models.Sheet)):
        msg = str("Index Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(index_sheet))
        raise TypeError(msg)
    if not isinstance(index_col_map, dict):
        msg = str("Index Column Map should be dict, not {}"
                  "").format(type(index_col_map))
        raise TypeError(msg)

    sheets_updated = 0
    sub_index = build_index_sheet_sub_index(index_sheet, index_col_map)
    if not sub_index:
        msg = str("Sub-index of Jira Tickets to link is empty")
        logging.debug(msg)
        return sheets_updated

    for sheet in source_sheets:
        sheet_col_map = get_column_map(sheet)
        rows_to_update = []

        for uuid_value, jira_ticket in sub_index.items():
            if not int(uuid_value.split("-")[0]) == sheet.id:
                msg = str("UUID does not match the Sheet ID. UUID value: {} | "
                          "Sheet ID: {} | Sheet Name: {}"
                          "").format(uuid_value, sheet.id, sheet.name)
                logging.debug(msg)
                continue
            elif int(uuid_value.split("-")[0]) == sheet.id:
                msg = str("UUID and Sheet ID match")
                logging.debug(msg)
            else:
                logging.error("Something went wrong pushing tickets back to "
                              "plan sheets")

            new_row = smartsheet.models.Row()
            new_row.id = int(uuid_value.split("-")[1])
            new_row.cells.append({
                'column_id': sheet_col_map['Jira Ticket'],
                'object_value': jira_ticket
            })
            rows_to_update.append(new_row)
        if rows_to_update:
            msg = str("Updating {} rows with newly created Jira Tickets"
                      "").format(len(rows_to_update))
            logging.debug(msg)
            write_rows_to_sheet(rows_to_update, sheet, write_method="update")
            sheets_updated += 1
        else:
            msg = str("All Jira Tickets have pre-existing links to "
                      "Sheet ID: {} | Sheet Name: {}").format(sheet.id,
                                                              sheet.name)
            logging.info(msg)
    return sheets_updated

# def link_predecessor_tickets(parent):
#     Follow predecessor tree, link issues as you go
#     Roll up the predecessor chain and then
#     1. Find top level Jira Ticket -> Create if "Create"
#     2. Find top level Jira Ticket -> If no Jira value, roll
#        down
#        the chain until you find "Create" -> Create
#     3. Find parent Jira ticket, use to create Issue Link
#     4. Form row, add to list of rows to create and push to Jira
#        Index
#     return parent


def build_index_sheet_sub_index(index_sheet, index_col_map):
    if not isinstance(index_sheet, (dict, smartsheet.models.Sheet)):
        raise TypeError
    if not isinstance(index_col_map, dict):
        raise TypeError
    if not index_sheet:
        raise ValueError
    if not index_col_map:
        raise ValueError
    # UUID: Jira Ticket
    sub_index = {}
    for row in index_sheet.rows:

        uuid_value = get_cell_data(row, 'UUID', index_col_map)
        jira_value = get_cell_data(row, 'Jira Ticket', index_col_map)

        if uuid_value is None or jira_value is None:
            # Skip empty Jira Tickets or UUIDs
            continue
        uuid = str(uuid_value.value)
        jira_ticket = str(jira_value.value)
        if uuid == "None" or jira_ticket == "None":
            # Skip None values returned as strings
            continue

        if bool(re.match(r"\d+-\d+-\d+-\d+", uuid)):
            msg = str(
                "UUID column has a value and matches the UUID pattern.")
            logging.debug(msg)
        else:
            msg = str("UUID does not match the pattern. UUID value: {}"
                      "").format(uuid)
            logging.debug(msg)
            continue

        msg = str("Row Number: {} - UUID: {} type: {} - Jira Ticket: {} "
                  "type: {}").format(row.row_number, uuid,
                                     type(uuid), jira_ticket,
                                     type(jira_ticket))
        logging.debug(msg)
        sheet_id = uuid.split("-")[0]
        row_id = uuid.split("-")[1]
        msg = str("Sheet ID: {} | Row ID: {}").format(sheet_id, row_id)
        logging.debug(msg)

        try:
            cell_link_status = has_cell_link(jira_value, "Out")
            if cell_link_status in ('Linked', 'OK'):
                # Skip linked rows
                msg = str("Jira Ticket: {} has already been pushed to "
                          "Sheet ID: {} | Row ID: {}"
                          "").format(jira_ticket, sheet_id, row_id)
                logging.debug(msg)
                continue
            elif cell_link_status == "Unlinked":
                # Jira Ticket cell is unlinked, add to index
                logging.debug(cell_link_status).format()
                sub_index[uuid_value] = jira_ticket
        except KeyError as e:
            msg = str("Error getting linked status: {}").format(e)
            logging.warning(msg)
            continue
    return sub_index


def build_row_data(row, col_map):
    """Builds the row data necessary to create new tickets in Jira. Manually
       parses a row from a Program Plan and copies select data into the Push
       Jira Ticket Sheet

    Args:
        row (smartsheet.Row): The Row to parse
        col_map (dict): The column map of Column Name: Column ID

    Raises:
        TypeError: Row must be a dict or smartsheet.models.Row
        TypeError: Column map must be a dict

    Returns:
        dict: A dictionary of the subest of row data to upload to Smartsheet
    """
    if not isinstance(row, (dict, smartsheet.models.Row)):
        msg = str("Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(row))
        raise TypeError(msg)
    if not isinstance(col_map, dict):
        msg = str("Sheet Column Map should be dict, not {}"
                  "").format(type(col_map))
        raise TypeError(msg)

    row_data = {}
    for col in project_columns:
        try:
            cell_value = get_cell_value(row, col, col_map)
            row_data[col] = cell_value
        except KeyError:
            continue
    row_data["row_num"] = row.row_number
    return row_data


def create_ticket_index(source_sheets, index_sheet, index_col_map):
    """Loads in all sheets recently modified and creates an index of any rows
       that are ready to create a Jira Ticket or are pending an existing Jira
       Ticket creation.

    Args:
        source_sheets (list): A list of all Smartsheet Sheet objects
        index_sheet (smartsheet.Sheet): The Jira Index Sheet
        index_col_map (dict): The Jira Index Sheet column map in the form of
                              Column Name: Column ID

    Raises:
        TypeError: Source Sheets must be a list of sheets
        TypeError: Index Sheet must be a dict or Smartsheet Sheet object
        TypeError: Index Column Map must be a dict

    Returns:
        dict: A dictionary of all tickets that should be created across all
              Program Plans
    """
    if not isinstance(source_sheets, list):
        msg = str("Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(source_sheets))
        raise TypeError(msg)
    if not isinstance(index_sheet, (dict, smartsheet.models.Sheet)):
        msg = str("Index Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(index_sheet))
        raise TypeError(msg)
    if not isinstance(index_col_map, dict):
        msg = str("Index Column Map should be dict, not {}"
                  "").format(type(index_col_map))
        raise TypeError(msg)

    tickets_to_create = {}
    pending_count = 0
    parent_pending_count = 0

    for sheet in source_sheets:
        col_map = get_column_map(sheet)
        msg = str("Loaded {} rows from Sheet ID: {} | Sheet Name: {}"
                  "").format(len(sheet.rows), sheet.id, sheet.name)
        logging.info(msg)
        try:
            _ = col_map[uuid_col]
        except KeyError:
            msg = str("Sheet ID {} | Sheet Name {} doesn't have UUID column. "
                      "Skipping sheet. (KeyError)").format(sheet.id,
                                                           sheet.name)
            logging.debug(msg)
            continue

        sheet_rows_to_update = []
        for row in sheet.rows:
            logging.debug("------------------------")
            logging.debug("New Row")
            logging.debug("------------------------")
            row_data = build_row_data(row, col_map)
            if row_data["Summary"] == "True":
                # Skip summary rows
                msg = str("Row {} skipped because Summary column was true"
                          "").format(row_data["row_num"])
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["Team"] is None:
                # Need team defined (so we can get project key). Skip
                msg = str("Row {} skipped because Team column was empty."
                          "").format(row_data["row_num"])
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["UUID"] is None:
                # No UUID means we can't push the created ticket IDs back
                # into the program sheets. Skip.
                msg = str("Row {} skipped because UUID column was empty."
                          "").format(row_data["row_num"])
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data['Issue Type'] == "Sub-Task":
                # Skip Subtasks, we can't create them with the connector
                msg = str("Row {} skipped because Parent Issue Type is {}."
                          "").format(row_data["row_num"],
                                     row_data["Parent Issue Type"])
                logging.debug(msg)
                continue
            if row_data['Parent Issue Type'] == "Sub-Task":
                # Skip Subtasks, we can't create them with the connector
                msg = str("Row {} skipped because Parent Issue Type is {}."
                          "").format(row_data["row_num"],
                                     row_data["Parent Issue Type"])
                logging.debug(msg)
                continue
            if row_data["Parent Ticket"] is None and row_data["Jira Ticket"]\
                    in ("Create", "create"):
                tickets_to_create[row_data['UUID']] = row_data
                # Set these rows to "Pending..."
                new_row = smartsheet.models.Row()
                new_row.id = row.id
                new_row.cells.append({
                    'column_id': col_map['Jira Ticket'],
                    'object_value': "Pending..."
                })
                sheet_rows_to_update.append(new_row)
                msg = str("Appended row UUID: {} and associated data to the "
                          "list of rows to update and set the Jira Ticket "
                          "column in Sheet Name: {} to Pending..."
                          "").format(row_data['UUID'], sheet.name)
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["Jira Ticket"] == "Pending...":
                # Skip any row that's already in process
                msg = str("Skipped because Jira Ticket or Parent Ticket "
                          "column was set to Pending...")
                logging.debug(msg)
                logging.debug(row_data)
                pending_count += 1
                continue
            if row_data['Parent Ticket'] == "Pending...":
                # Skip any row that's already in process
                msg = str("Skipped because Parent Ticket column was set to "
                          "Pending...")
                logging.debug(msg)
                logging.debug(row_data)
                parent_pending_count += 1
                continue
            if row_data['Parent Ticket'] not in ('Create', 'create',
                                                 'Pending...', None):
                if row_data['Jira Ticket'] in ('Create', 'create'):
                    # Add row data to create tickets.
                    tickets_to_create[row_data['UUID']] = row_data

                    # Set these rows to "Pending..." in the Plan sheet.
                    new_row = smartsheet.models.Row()
                    new_row.id = row.id
                    new_row.cells.append({
                        'column_id': col_map['Jira Ticket'],
                        'object_value': "Pending..."
                    })
                    sheet_rows_to_update.append(new_row)
                    pending_count += 1
                    # TODO: Validate Jira ticket so that comments don't
                    # cause errors.
                    msg = str("Parent Ticket isn't 'Create' or 'Pending...' "
                              "but it does have a value. Adding row_data to "
                              "tickets_to_create and setting Jira Ticket "
                              "to Pending...")
                    logging.debug(msg)
                    logging.debug(row_data)
                    continue
            logging.debug("Made it past all IFs without triggering")
            logging.debug(row_data)

        # Validate that there are rows to write.
        if sheet_rows_to_update:
            write_rows_to_sheet(sheet_rows_to_update, sheet,
                                write_method="update")
        else:
            msg = str("No rows to update for Sheet ID: {}, Sheet Name: {}"
                      "").format(sheet.id, sheet.name)
            logging.info(msg)

        msg = str("Sheet ID: {} | Sheet Name: {} has {} rows pending ticket "
                  "creation. {} rows are waiting on parent ticket "
                  "creation.").format(sheet.id, sheet.name, pending_count,
                                      parent_pending_count)
        logging.info(msg)

    logging.debug("Top-level Rows to create first")
    logging.debug("------------------------")
    for k, v in tickets_to_create.items():
        msg = str("{}: {}").format(k, v)
        logging.debug(msg)

    return tickets_to_create


# TODO: Drop parent rows once written to index sheet by removing the "Create"
# from the Jira Ticket field and/or filtering out UUID matches + nonNull
# Jira Ticket field on the Index sheet
def create_tickets(minutes=dev_minutes):
    """Main function passed to the scheduler to parse and upload data to
       Smartsheet so that new Jira Tickets can be created.

    Args:
        minutes (int, optional): Number of minutes in the past used to filter
                                 sheets and sheet data. Defaults to
                                 dev_minutes.

    Raises:
        TypeError: Minutes must be an int
        ValueError: Minutes must be a positive integer or 0
    """
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)
    start = time.time()
    source_sheets, index_sheet, index_col_map = refresh_sheets(minutes)
    # Link back created tickets first
    sheets_updated = link_jira_index_to_sheet(
        source_sheets, index_sheet, index_col_map)
    msg = str("Updated {} Plan sheets with newly created Jira tickets."
              "").format(sheets_updated)
    logging.info(msg)

    # Create an index of rows pending ticket creation.
    tickets_to_create = create_ticket_index(
        source_sheets, index_sheet, index_col_map)
    logging.debug("Parent Dict")
    logging.debug("------------------------")
    logging.debug(tickets_to_create)
    msg = str("Parent Length: {}").format(len(tickets_to_create))
    logging.debug(msg)
    if tickets_to_create:
        # Write parent rows
        push_ticket_sheet = get_sheet(
            config.push_tickets_sheet, config.minutes)
        push_tickets_col_map = get_column_map(push_ticket_sheet)
        rows_to_write = form_rows(tickets_to_create, push_tickets_col_map)
        write_rows_to_sheet(rows_to_write, config.push_tickets_sheet)
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 2)
        logging.info("Create new tickets from Program Plan line items "
                     "took: {} seconds.".format(elapsed))
        return True
    elif not tickets_to_create:
        msg = str("No parent or child rows remain to be written to the "
                  "Push Tickets Sheet.")
        logging.info(msg)
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 2)
        logging.info("Create new tickets from Program Plan line items "
                     "took: {} seconds.".format(elapsed))
        return False
    else:
        msg = str("Looping through rows rows to create Jira Tickts "
                  "failed with an unknown error.")
        logging.warning(msg)
        return None
