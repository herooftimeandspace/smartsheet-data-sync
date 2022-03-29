import logging
import re
import time

import app.config as config
import smartsheet

import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars
import uuid_module.get_data as get_data

project_columns = [app_vars.summary_col, app_vars.task_col, "Issue Type",
                   app_vars.jira_col,
                   "Parent Ticket", "Program", "Initiative", "Team", "UUID",
                   app_vars.predecessor_col, "ParentUUID", "Project Key",
                   "Parent Issue Type", "Inject", "KTLO"]
jira_index_columns = [app_vars.task_col, "Issue Type", app_vars.jira_col,
                      "Issue Links",
                      "Project Key", "Components", "Labels", "Epic Link",
                      "Epic Name", app_vars.summary_col, "Inject", "KTLO",
                      "UUID"]


def build_sub_indexes(sheet, col_map):
    """Build sub_indexes of UUIDs and Jira Tickets. Evaluates every row.
       Returns a dict and a list. The dict is all Jira Tickets that have
       UUIDs associated with them on the sheet. The list is all UUIDs that
       do not have a Jira Ticket.

    Args:
        sheet (smartsheet.models.Sheet): The sheet to build the index from.
        col_map (dict): The map of column names to column IDs

    Raises:
        TypeError: Index sheet must be dict or smartsheet Sheet object
        TypeError: Index Column Map must be a dict
        ValueError: Index Sheet should not be empty
        ValueError: Index Column map should not be empty

    Returns:
        dict: A subindex of all Jira Tickets: UUIDs
        list: A subindex of all UUIDs without Jira Tickets
    """
    if not isinstance(sheet, (dict, smartsheet.models.Sheet)):
        msg = str("Index Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(sheet))
        raise TypeError(msg)
    if not isinstance(col_map, dict):
        msg = str("Index Column Map should be dict, not {}"
                  "").format(type(col_map))
        raise TypeError(msg)
    if not sheet:
        msg = str("Index Sheet should not be {}").format(sheet)
        raise ValueError(msg)
    if not col_map:
        msg = str("Index Col Map should not be {}").format(sheet)
        raise ValueError(msg)
    # UUID: Jira Ticket
    sub_index_dict = {}
    sub_index_list = []
    list_count = 0
    dict_count = 0
    for row in sheet.rows:
        uuid_cell = helper.get_cell_data(row, app_vars.uuid_col, col_map)
        jira_cell = helper.get_cell_data(row, app_vars.jira_col, col_map)

        if not uuid_cell:
            # Skip empty UUIDs
            continue

        if str(uuid_cell.value) == "None":
            # Skip None values returned as strings
            continue

        # Check if the UUID string matches our UUID pattern
        if bool(re.match(r"\d+-\d+-\d+-\d+", uuid_cell.value)):
            msg = str("Row Number: {} - UUID: {} type: {} - Jira Ticket: {} "
                      "type: {}").format(row.row_number, uuid_cell.value,
                                         type(uuid_cell.value),
                                         jira_cell.value,
                                         type(jira_cell.value))
            logging.debug(msg)
        else:
            msg = str("UUID does not match the pattern. UUID value: {}"
                      "").format(uuid_cell.value)
            logging.debug(msg)
            continue

        if str(jira_cell.value) is None or jira_cell is None:
            list_count += 1
            sub_index_list.append(str(uuid_cell.value))
        else:
            dict_count += 1
            sub_index_list.append(str(uuid_cell.value))
            # Add the UUID (str): Jira Ticket (str)
            sub_index_dict[str(uuid_cell.value)] = jira_cell.value
    msg = str("Added {} UUIDS to the sub-index list and {} UUID:Jira pairs "
              "to the sub-index dict.").format(list_count, dict_count)
    logging.debug(msg)
    return sub_index_dict, sub_index_list


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
            if col_name == app_vars.jira_col and value in ("Create", "create"):
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

        # Create labels for program, initiative and team
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
        # Add standard components for syncing
        components = ["Autogenerated by Smartsheet", "Sync to Smartsheet"]
        new_row.cells.append({
            'column_id': col_map['Components'],
            'object_value': {
                'objectType': "MULTI_PICKLIST",
                'values': components
            }
        })
        # If the issue type is an epic, set the Epic Name = Tasks column value
        if data['Issue Type'] == "Epic":
            epic_name = data['Tasks']
            new_row.cells.append({
                'column_id': col_map['Epic Name'],
                'object_value': epic_name
            })

        # if the issue type is an epic and the parent is a project or epic
        # use the 'implenets' issue link to connect the tickets because epics
        # can't use the Epic Link field.
        if data['Issue Type'] == "Epic":
            if data['Parent Issue Type'] in ("Project", "Epic"):
                ticket = data['Parent Ticket']
                issue_link = str("implements {}").format(ticket)
                new_row.cells.append({
                    'column_id': col_map['Issue Links'],
                    'object_value': issue_link
                })

        # If the issue type is a story, task or project, and the parent is
        # an epic, set the Epic link instead of issue link
        if data['Issue Type'] in ("Story", "Task", "Project"):
            if data['Parent Issue Type'] == "Epic":
                epic_link = data['Parent Ticket']
                new_row.cells.append({
                    'column_id': col_map['Epic Link'],
                    'object_value': epic_link
                })

            # But if the parent is also a story, task or project, use
            # Issue links instead
            if data['Parent Issue Type'] in ("Story", "Task", "Project"):
                ticket = data['Parent Ticket']
                issue_link = str("implements {}").format(ticket)
                new_row.cells.append({
                    'column_id': col_map['Issue Links'],
                    'object_value': issue_link
                })

        rows_to_add.append(new_row)
    return rows_to_add


def get_push_tickets_sheet():
    """Helper function to get the Push Jira Tickets sheet and build the column
       map

    Returns:
        smartsheet.models.Sheet: The sheet object
        dict: The column map of Column Names: Column IDs
    """
    push_ticket_sheet = smartsheet_api.get_sheet(
        config.push_tickets_sheet, config.minutes)
    push_tickets_col_map = helper.get_column_map(push_ticket_sheet)
    return push_ticket_sheet, push_tickets_col_map


# TODO: Handle the same UUID connected to multiple Jira Tickets.
def copy_jira_tickets_to_sheets(source_sheets, index_sheet, index_col_map):
    """Uses the UUID column to identify the row that originally pushed data
       into Jira. Copies the Jira Ticket back into the Program Plan

    Args:
        source_sheets (list): A list of Smartsheet Sheet objects push the
                              Jira Tickets into
        index_sheet (smartsheet.models.Sheet): The Jira Index Sheet that
           contains the UUID of the originating row and the Jira Ticket
           that we want to copy to the source sheet.
        index_col_map (dict): The column map of Column Names: Column IDs
           for the Jira Index Sheet

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
    if not index_col_map:
        msg = str("Index Column Map must not be empty."
                  "").format()
        raise ValueError(msg)

    def get_jira_cell(row_id, sheet, col_map):
        """Parse through the sheet's rows, see if the sheet's row.id is a
           match to the given row_id. If there's a match, get the Jira cell
           data. Return None if the row ID was not found.

        Args:
            row_id (int): The row ID that we want to copy data to
            sheet (smartsheet.models.Sheet): The sheet that may contain the
               row_id to copy data to
            col_map (dict): _description_

        Returns:
            smartsheet.models.Cell: A cell object containing the Jira Ticket
            None: No matching row_id was found in the sheet.
        """
        for row in sheet.rows:
            if not row_id == row.id:
                continue

            jira_cell = helper.get_cell_data(
                row, app_vars.jira_col, col_map)
            return jira_cell
        else:
            return None

    def contains_uuid(uuid_list, index_dict):
        """Check to see if the sheet contains any UUIDs from the Jira Index
           Sheet. Return a subset of matches.

        Args:
            uuid_list (list): A list of UUIDs (str) from the source sheet
            index_dict (dict): A dict of UUIDs (str): Jira Ticket (str) from
               the Jira Index Sheet

        Returns:
            dict: A dict of UUIDs: Jira Tickets
        """
        tiny_jira_index = {}
        # For each UUID in the sheet UUID list, check to see if that UUID
        # is in the index dict keys. If it is not, move on. If it is,
        # add it to the tiny dict.
        for sheet_uuid in uuid_list:
            if sheet_uuid not in index_dict.keys():
                continue
            else:
                # Create new entry with Sheet UUID, index_dict Jira Ticket
                tiny_jira_index[sheet_uuid] = index_dict[sheet_uuid]
        return tiny_jira_index

    sheets_updated = 0

    # Build an index of UUID (str): Jira Ticket (str) from the Jira Index Sheet
    # At this point we don't know if the tickets have been cell linked yet.
    jira_sub_index, _ = build_sub_indexes(index_sheet, index_col_map)
    if not jira_sub_index:
        msg = str("Sub-index of Jira Tickets to link is empty")
        logging.debug(msg)
        return sheets_updated

    # For each Jira Ticket with a UUID in the index sheet, check to see if
    # that ticket has been linked to the sheet and row in the UUID.
    for sheet in source_sheets:
        sheet_col_map = helper.get_column_map(sheet)
        rows_to_update = []

        # Validate that the sheet we're checking has both UUID and Jira
        # Ticket columns. If they don't exist, skip the sheet.
        if app_vars.uuid_col not in sheet_col_map.keys():
            continue
        if app_vars.jira_col not in sheet_col_map.keys():
            continue

        # Build a list of UUIDs from the sheet.
        _, sheet_uuid_list = build_sub_indexes(sheet, sheet_col_map)

        # These are all the UUIDs that had a match in the Jira Index Sheet,
        # with the associated Jira Ticket from the Index Sheet.
        tiny_index = contains_uuid(sheet_uuid_list, jira_sub_index)
        if not tiny_index:
            # The index is empty and we didn't actually match any UUIDs
            continue

        # Check the sheet and row for each UUID, validate that the ticket is
        # not already present
        for uuid, ticket in tiny_index.items():
            split = uuid.split("-")
            row_id = int(split[1])
            jira_cell = get_jira_cell(row_id, sheet, sheet_col_map)

            if not jira_cell:
                # Jira column and cell data should exist on this sheet but
                # don't for some reason?
                msg = str("Jira Cell not found on Sheet Name {} | "
                          "Sheet ID {} | Row ID {}").format(sheet.name,
                                                            sheet.id, row_id)
                logging.warning(msg)
                continue
            if jira_cell.value == ticket:
                # Jira Ticket has already been copied to the sheet
                continue
            if jira_cell.value is None or jira_cell.value == "None":
                # Jira Ticket cell isn't "Pending..." so it's not ready for
                # a new Jira Ticket. Skip.
                continue
            if jira_cell.value == "Pending...":
                # Jira Ticket column for this row is "Pending...", copy back
                # the ticket from the Index sheet into the row.
                new_row = smartsheet.models.Row()
                new_row.id = row_id
                new_row.cells.append({
                    'column_id': sheet_col_map[app_vars.jira_col],
                    'object_value': ticket
                })
                rows_to_update.append(new_row)

        if rows_to_update:
            msg = str("Updating Sheet Name: {} | Sheet ID {} with {} rows of "
                      "newly created Jira Tickets."
                      "").format(sheet.name, sheet.id, len(rows_to_update))
            logging.debug(msg)
            smartsheet_api.write_rows_to_sheet(rows_to_update, sheet,
                                               write_method="update")
            sheets_updated += 1
        else:
            msg = str("No new Jira Tickets are ready for copy to "
                      "Sheet Name: {} | Sheet ID: {}").format(sheet.name,
                                                              sheet.id)
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


def copy_errors_to_sheet():
    """Copies any sync errors back to the original sheet so that the end user
       knows if/when/why a ticket creation failed.
    """
    push_sheet, push_col_map = get_push_tickets_sheet()
    success_count = 0
    failure_count = 0
    skip_count = 0
    for row in push_sheet.rows:
        uuid_cell = helper.get_cell_data(row, app_vars.uuid_col, push_col_map)
        sync_cell = helper.get_cell_data(row, "Sync Status", push_col_map)

        # Skip empty UUID or Sync Error cells or None cell values.
        if not uuid_cell:
            skip_count += 1
            continue
        if not sync_cell:
            skip_count += 1
            continue
        if not uuid_cell.value:
            skip_count += 1
            continue
        if not sync_cell.value:
            skip_count += 1
            continue

        # Get the sheet ID and row ID from the UUID
        split = uuid_cell.value.split("-")
        sheet_id = int(split[0])
        row_id = int(split[1])

        # Get the Jira Cell value in the sheet and validate that it should
        # be written to.
        sheet = smartsheet_api.get_sheet(sheet_id, config.minutes)
        col_map = helper.get_column_map(sheet)
        dest_row = smartsheet_api.get_row(sheet.id, row_id)
        jira_cell = helper.get_cell_data(dest_row, app_vars.jira_col, col_map)

        if bool(re.match(r"[a-zA-Z]+-\d+", jira_cell.value)):
            # Cell value matches the Jira Ticket pattern, skip.
            skip_count += 1
            continue
        if "reasonPhrase" in jira_cell.value:
            # Sync Cell has already been copied.
            logging.info("reasonPhrase in Jira Cell, skipping.")
            skip_count += 1
            continue

        # Write the sync error cell to the row
        new_row = smartsheet.models.Row()
        new_row.id = row_id
        sync_cell.column_id = col_map[app_vars.jira_col]
        sync_cell.hyperlink = smartsheet.models.ExplicitNull()
        new_row.cells.append(sync_cell)
        result = smartsheet_api.write_rows_to_sheet([new_row], sheet, "update")
        logging.debug(result)

        if not result.message == "SUCCESS":
            failure_count += 1
        else:
            success_count += 1
    return success_count, failure_count, skip_count


def copy_uuid_to_index_sheet(index_sheet, index_col_map):
    """Copy the UUID from the Push Data Sheet into the Jira Index Sheet after
       the ticket is created in Jira and synced in to the Index Sheet so that
       we can push the Jira Ticket back into the Program Plan that triggered
       the ticket creation.

    Args:
        index_sheet (smartsheet.models.Sheet): The Jira Index Sheet
        index_col_map (dict): The map of Column Names to Column IDs

    Returns:
        bool: True if UUIDs were copied, False if they were not.
    """
    if not isinstance(index_sheet, (dict, smartsheet.models.Sheet)):
        msg = str("Index Sheet should be dict or smartsheet.Sheet, not {}"
                  "").format(type(index_sheet))
        raise TypeError(msg)
    if not isinstance(index_col_map, dict):
        msg = str("Index Column Map should be dict, not {}"
                  "").format(type(index_col_map))
        raise TypeError(msg)
    if not index_col_map:
        msg = str("Index Column Map must not be empty."
                  "").format()
        raise ValueError(msg)

    rows_to_write = []
    push_ticket_sheet, push_tickets_col_map = get_push_tickets_sheet()
    # Build an index of all rows on the Push Ticket Sheet that have UUIDs
    # AND Jira tickets
    sub_index, _ = build_sub_indexes(
        push_ticket_sheet, push_tickets_col_map)

    # For each row in the index sheet, get the cell data for the Jira Ticket
    # cell and the UUID cell.
    for row in index_sheet.rows:
        jira_ticket = helper.get_cell_data(
            row, app_vars.jira_col, index_col_map)
        uuid_value = helper.get_cell_data(
            row, app_vars.uuid_col, index_col_map)
        if uuid_value.value:
            # Skip rows with UUIDs.
            continue
        for uuid, sub_ticket in sub_index.items():
            if sub_ticket == jira_ticket.value:
                msg = str("Push ticket {} matches Index ticket {}, writing "
                          "UUID: {}").format(sub_ticket, jira_ticket.value,
                                             uuid.value)
                logging.debug(msg)
                new_row = smartsheet.models.Row()
                new_row.id = row.id
                new_row.cells.append({
                    'column_id': index_col_map[app_vars.uuid_col],
                    'object_value': uuid
                })
                rows_to_write.append(new_row)
    if rows_to_write:
        smartsheet_api.write_rows_to_sheet(rows_to_write, index_sheet,
                                           write_method="update")
        return True
    else:
        msg = str("No UUIDs copied to Sheet ID: {}, Sheet Name: {}"
                  "").format(index_sheet.id, index_sheet.name)
        logging.info(msg)
        return False


def build_row_data(row, col_map):
    """Builds the row data necessary to create new tickets in Jira. Manually
       parses a row from a Program Plan and copies select data into the Push
       Jira Ticket Sheet

    Args:
        row (smartsheet.models.Row): The row to parse
        col_map (dict): The column map of Column Name: Column ID

    Raises:
        TypeError: Row must be a dict or smartsheet.models.Row
        TypeError: Column map must be a dict
        ValueError: Row must not be empty
        ValueError: Column map must not be empty

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
    if not row:
        msg = str("Row must not be empty."
                  "").format()
        raise ValueError(msg)
    if not col_map:
        msg = str("Column Map must not be empty."
                  "").format()
        raise ValueError(msg)

    row_data = {}
    for col in project_columns:
        try:
            cell = helper.get_cell_data(row, col, col_map)
            row_data[col] = cell.value
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
        ValueError: Column map must not be empty

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
    if not index_col_map:
        msg = str("Column Map must not be empty."
                  "").format()
        raise ValueError(msg)

    tickets_to_create = {}
    pending_count = 0
    parent_pending_count = 0

    for sheet in source_sheets:
        col_map = helper.get_column_map(sheet)
        msg = str("Loaded {} rows from Sheet ID: {} | Sheet Name: {}"
                  "").format(len(sheet.rows), sheet.id, sheet.name)
        logging.info(msg)
        if app_vars.uuid_col not in col_map.keys():
            msg = str("Sheet ID {} | Sheet Name {} doesn't have UUID column. "
                      "Skipping sheet.").format(sheet.id, sheet.name)
            logging.debug(msg)
            continue

        sheet_rows_to_update = []
        for row in sheet.rows:
            logging.debug("------------------------")
            logging.debug("New Row")
            logging.debug("------------------------")
            row_data = build_row_data(row, col_map)
            if row_data[app_vars.summary_col] == "True":
                # Skip summary rows
                msg = str("Row {} skipped because Summary column was true"
                          "").format(row_data["row_num"])
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["Team"] is None:
                # Need team defined (so we can get project key). Skip.
                msg = str("Row {} skipped because Team column was empty."
                          "").format(row_data["row_num"])
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data[app_vars.uuid_col] is None:
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
            if bool(re.match(r"[a-zA-Z]+-\d+", row_data[app_vars.jira_col])):
                # Skip tickets that match the Jira Ticket pattern
                msg = str("Jira Ticket {} on row {} matches the Jira Ticket"
                          "pattern").format(row_data[app_vars.jira_col],
                                            row_data["row_num"])
                logging.debug(msg)
                continue
            if "reasonPhrase" in row_data["Parent Ticket"]:
                # Skip rows where the parent ticket has a sync error
                msg = str("Parent ticket for row {} has a Jira Sync error: "
                          "{}. Skipping.").format(row_data["row_num"],
                                                  row_data[app_vars.jira_col])
                logging.debug(msg)
                continue
            if "reasonPhrase" in row_data[app_vars.jira_col]:
                # Skip rows where the Jira ticket has a sync error
                msg = str("Jira ticket for row {} is a Jira Sync error: "
                          "{}. Skipping.").format(row_data["row_num"],
                                                  row_data[app_vars.jira_col])
                logging.debug(msg)
                continue
            if row_data["Parent Ticket"] is None and \
                    row_data[app_vars.jira_col] in ("Create", "create"):
                tickets_to_create[row_data[app_vars.uuid_col]] = row_data
                # Set these rows to "Pending..."
                new_row = smartsheet.models.Row()
                new_row.id = row.id
                new_row.cells.append({
                    'column_id': col_map[app_vars.jira_col],
                    'object_value': "Pending..."
                })
                sheet_rows_to_update.append(new_row)
                msg = str("Appended row UUID: {} and associated data to the "
                          "list of rows to update and set the Jira Ticket "
                          "column in Sheet Name: {} to Pending..."
                          "").format(row_data[app_vars.uuid_col], sheet.name)
                logging.debug(msg)
                # logging.debug(row_data)
                continue
            if row_data[app_vars.jira_col] == "Pending...":
                # Skip any row that's already in process
                msg = str("Skipped because Jira Ticket or Parent Ticket "
                          "column was set to Pending...")
                logging.debug(msg)
                # logging.debug(row_data)
                pending_count += 1
                continue
            if row_data['Parent Ticket'] == "Pending...":
                # Skip any row that's already in process
                msg = str("Skipped because Parent Ticket column was set to "
                          "Pending...")
                logging.debug(msg)
                # logging.debug(row_data)
                parent_pending_count += 1
                continue
            if row_data['Parent Ticket'] not in ('Create', 'create',
                                                 'Pending...', None):
                if not bool(re.match(r"[a-zA-Z]+-\d+",
                                     row_data["Parent Ticket"])):
                    msg = str("Parent Ticket {} on row {} does not match the "
                              "Jira Ticket pattern. Skipping"
                              "").format(row_data[app_vars.jira_col],
                                         row_data["row_num"])
                    logging.debug(msg)
                    continue

                if row_data[app_vars.jira_col] in ('Create', 'create'):
                    # Add row data to create tickets.
                    tickets_to_create[row_data[app_vars.uuid_col]] = row_data

                    # Set these rows to "Pending..." in the Plan sheet.
                    new_row = smartsheet.models.Row()
                    new_row.id = row.id
                    new_row.cells.append({
                        'column_id': col_map[app_vars.jira_col],
                        'object_value': "Pending..."
                    })
                    sheet_rows_to_update.append(new_row)
                    pending_count += 1
                    continue
            # TODO: Validate Jira ticket so that comments don't
            # cause errors.
            msg = str("Parent Ticket isn't 'Create' or 'Pending...' "
                      "but it does have a value. Dumping data.")
            logging.debug(msg)
            logging.debug(row_data)

        # Validate that there are rows to write.
        if sheet_rows_to_update:
            smartsheet_api.write_rows_to_sheet(sheet_rows_to_update, sheet,
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
def create_tickets(minutes=app_vars.dev_minutes):
    """Main function passed to the scheduler to parse and upload data to
       Smartsheet so that new Jira Tickets can be created. Logs a warning
       if the process takes longer than the interval.

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

    sheet_ids = get_data.get_all_sheet_ids(minutes, config.workspace_id,
                                           config.index_sheet)
    msg = str("Sheet IDs object type {}, object values {}").format(
        type(sheet_ids), sheet_ids)
    logging.debug(msg)
    source_sheets = get_data.refresh_source_sheets(sheet_ids, minutes)

    # Load the index sheet and create a column map.
    index_sheet = smartsheet_api.get_sheet(config.index_sheet, minutes)
    index_col_map = helper.get_column_map(index_sheet)

    # Copy UUIDs from Push sheet to Index Sheet
    logging.info("Starting to copy UUIDs from the Push Sheet to the "
                 "Index Sheet.")
    result = copy_uuid_to_index_sheet(index_sheet, index_col_map)

    # Refresh the index sheet since we just wrote data
    if result:
        index_sheet = smartsheet_api.get_sheet(config.index_sheet,
                                               config.minutes)

    logging.info("Starting to push sync error messages to the Program Plans.")
    success_count, failure_count, skip_count = copy_errors_to_sheet()
    if success_count:
        msg = str("Successfully pushed {} sync error messages to "
                  "their respective source sheets.").format(success_count)
        logging.info(msg)

    if failure_count:
        msg = str("Failed to push {} sync error messages to "
                  "their respective source sheets.").format(failure_count)
        logging.info(msg)

    if skip_count:
        msg = str("{} rows skipped.").format(skip_count)
        logging.info(msg)

    # Copy Jira Tickets from the index sheet back to the source sheets
    logging.info("Starting to copy Jira Tickets from the Index Sheet to the "
                 "Program Plans.")
    sheets_updated = copy_jira_tickets_to_sheets(
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

    # If there are rows that need tickets, write the rows to the Push Ticket
    # Sheet. Return true once the rows have been written.
    if tickets_to_create:
        _, push_tickets_col_map = get_push_tickets_sheet()
        rows_to_write = form_rows(tickets_to_create, push_tickets_col_map)
        smartsheet_api.write_rows_to_sheet(rows_to_write,
                                           config.push_tickets_sheet)
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 2)
        logging.info("Create new tickets from Program Plan line items "
                     "took: {} seconds.".format(elapsed))
        if elapsed > 120:
            elapsed_warning = helper.truncate(elapsed, 2)
            msg = str("Create Jira Tickets took {} seconds longer than "
                      "the interval").format(elapsed_warning)
            logging.warning(msg)
        return True
    elif not tickets_to_create:
        msg = str("No parent or child rows remain to be written to the "
                  "Push Tickets Sheet.")
        logging.info(msg)
        end = time.time()
        elapsed = end - start
        elapsed = helper.truncate(elapsed, 2)
        logging.info("Create new tickets from Program Plan line items "
                     "took: {} seconds.".format(elapsed))
        if elapsed > 120:
            elapsed_warning = elapsed - 120
            elapsed_warning = helper.truncate(elapsed, 2)
            msg = str("Create Jira Tickets took {} seconds longer than "
                      "the interval").format(elapsed_warning)
            logging.warning(msg)
        return False
    else:
        msg = str("Looping through rows rows to create Jira Tickts "
                  "failed with an unknown error.")
        logging.warning(msg)
        return None
