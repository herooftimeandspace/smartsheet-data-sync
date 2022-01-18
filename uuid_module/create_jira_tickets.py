import logging
# import os
import re
# import sys
# from logging.config import dictConfig
# from time import sleep

# import pytz
import smartsheet
# from apscheduler.executors.pool import ProcessPoolExecutor,
#                                        ThreadPoolExecutor
# from apscheduler.schedulers.background import BlockingScheduler
# from uuid_module.get_data import(get_secret, get_secret_name)
from uuid_module.get_data import (get_all_sheet_ids, get_jira_index_sheet,
                                  refresh_source_sheets)
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                has_cell_link)
from uuid_module.variables import (dev_jira_idx_sheet, dev_workspace_id,
                                   uuid_col, dev_minutes)

# cwd = os.path.dirname(os.path.abspath(__file__))
# log_location = os.path.join(cwd, log_location)
# utc = pytz.UTC
# minutes = 525600


# def set_logging_config(env):
#     if not isinstance(env, str):
#         msg = str("Environment should be type: str, not {}").format(
#             type(env))
#         raise TypeError(msg)
#     if env not in ("-s", "--staging", "-staging", "-p", "--prod", "-prod",
#                    "-d", "--debug", "-debug"):
#         msg = str("Invalid environment flag. '{}' was passed but it should "
#                   "be '--debug', '--staging' or '--prod'").format(
#             type(env))
#         raise ValueError(msg)

#     logging_config = dict(
#         version=1,
#         formatters={
#             'f': {'format':
#                   "%(asctime)s - %(levelname)s - %(message)s"}
#         },
#         handlers={
#             'docker': {
#                 'class': 'logging.StreamHandler',
#                 'formatter': 'f',
#                 'level': logging.INFO,
#                 'stream': 'ext://sys.stdout'
#             }
#         },
#         root={
#             'handlers': ['docker'],  # 'console', 'file'
#             'level': logging.DEBUG,
#             'disable_existing_loggers': False
#         },
#     )
#     if env in ("-s", "--staging", "-staging"):
#         logging_config = dict(
#             version=1,
#             formatters={
#                 'f': {'format':
#                       "%(asctime)s - %(levelname)s - %(message)s"}
#             },
#             handlers={
#                 'docker': {
#                     'class': 'logging.StreamHandler',
#                     'formatter': 'f',
#                     'level': logging.INFO,
#                     'stream': 'ext://sys.stdout'
#                 }
#             },
#             root={
#                 'handlers': ['docker'],  # 'console', 'file'
#                 'level': logging.DEBUG,
#                 'disable_existing_loggers': False
#             },
#         )
#     elif env in ("-p", "--prod", "-prod"):
#         logging_config = dict(
#             version=1,
#             formatters={
#                 'f': {'format':
#                       "%(asctime)s - %(levelname)s - %(message)s"}
#             },
#             handlers={
#                 'docker': {
#                     'class': 'logging.StreamHandler',
#                     'formatter': 'f',
#                     'level': logging.INFO,
#                     'stream': 'ext://sys.stdout'
#                 }
#             },
#             root={
#                 'handlers': ['docker'],  # 'console', 'file'
#                 'level': logging.DEBUG,
#                 'disable_existing_loggers': False
#             },
#         )
#     elif env in ("-d", "--debug", "-debug"):
#         logging_config = dict(
#             version=1,
#             formatters={
#                 'f': {'format':
#                       "%(asctime)s - %(levelname)s - %(message)s"}
#             },
#             handlers={
#                 'file': {
#                     'class': 'logging.FileHandler',
#                     'formatter': 'f',
#                     'level': logging.DEBUG,
#                     'filename': log_location + module_log_name
#                 },
#                 'docker': {
#                     'class': 'logging.StreamHandler',
#                     'formatter': 'f',
#                     'level': logging.DEBUG,
#                     'stream': 'ext://sys.stdout'
#                 }
#             },
#             root={
#                 'handlers': ['docker', 'file'],  # 'console', 'file'
#                 'level': logging.DEBUG,
#                 'disable_existing_loggers': False
#             },
#         )

#     return logging_config


# # Initialize client. Uses the API token in the environment variable
# # "SMARTSHEET_ACCESS_TOKEN", which is pulled from the AWS Secrets API.
# env = sys.argv[1:]
# env = env[0]
# logging_config = set_logging_config(env)
# try:
#     os.mkdir(log_location)
#     f = open(log_location + module_log_name, "w")
#     f.close
#     dictConfig(logging_config)
# except FileExistsError:
#     dictConfig(logging_config)

# logger = logging.getLogger()

# executors = {
#     'default': ThreadPoolExecutor(1),
#     'processpool': ProcessPoolExecutor(1)
# }
# job_defaults = {
#     'coalesce': True,
#     'max_instances': 5
# }
# scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)

# if env in ("--", None):
#     logging.error("No environment flag set. Please use --debug, --staging "
#                   "or --prod. Terminating app.")
#     quit()
# else:
#     msg = str("The {} flag was passed from the command line").format(env)
#     logging.info(msg)
#     if env in ("-s", "--staging", "-staging", "-d", "--debug", "-debug"):
#         msg = str("Using default debug/staging variables for workspace_id "
#                   "and Jira index sheet").format()
#         logging.info(msg)
#     elif env in ("-p", "--prod", "-prod"):
#         workspace_id = prod_workspace_id
#         index_sheet = prod_jira_idx_sheet
#         msg = str("Set workspace_id to: {} and index_sheet to: {} "
#                   "for Prod environment").format(workspace_id, index_sheet)
#         logging.info(msg)

# logging.debug("------------------------")
# logging.debug("Initializing Smartsheet Client API")
# logging.debug("------------------------")
# secret_name = get_secret_name(env)
# try:
#     os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
# except TypeError:
#     msg = str("Refresh Isengard credentials")
#     logging.error(msg)
#     exit()
# smartsheet_client = smartsheet.Smartsheet()
# # Make sure we don't miss any error
# smartsheet_client.errors_as_exceptions(True)


project_columns = ["Summary", "Tasks", "Issue Type", "Jira Ticket",
                   "Parent Ticket", "Program", "Initiative", "Team", "UUID",
                   "Predecessors", "ParentUUID", "Project Key",
                   "Parent Issue Type", "Inject", "KTLO"]
jira_index_columns = ["Tasks", "Issue Type", "Jira Ticket", "Issue Links",
                      "Project Key", "Components", "Labels", "Epic Link",
                      "Epic Name", "Summary", "Inject", "KTLO", "UUID"]


def refresh_sheets(smartsheet_client, minutes=dev_minutes):
    sheet_ids = get_all_sheet_ids(
        smartsheet_client, minutes, workspace_id=dev_workspace_id,
        index_sheet=dev_jira_idx_sheet)
    msg = str("Sheet IDs object type {}, object values {}").format(
        type(sheet_ids), sheet_ids)
    logging.debug(msg)
    source_sheets = refresh_source_sheets(
        smartsheet_client, sheet_ids, minutes)

    # TODO: Load index sheet and kick off 2 functions. 1: Create new tickets
    # 2: Copy created tickets to program sheets via UUID
    index_sheet = get_jira_index_sheet(smartsheet_client, dev_jira_idx_sheet)
    index_col_map = get_column_map(index_sheet)
    return source_sheets, index_sheet, index_col_map


def form_rows(row_dict, index_col_map):
    index_rows_to_add = []
    for uuid, data in row_dict.items():
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        if data['Parent Issue Type'] == "Sub-Task":
            # Skip Subtasks, we can't create them with the connector
            continue
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
                col_id = index_col_map[col_name]
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
        labels = [sub.replace(' ', '_') for sub in labels]
        # logging.debug(labels)
        new_row.cells.append({
            'column_id': index_col_map['Labels'],
            'object_value': {
                'objectType': "MULTI_PICKLIST",
                'values': labels
            }
        })
        if data['Parent Issue Type'] in ("Epic, Story"):
            ticket = data['Parent Ticket']
            issue_link = str("implements {}").format(ticket)
            new_row.cells.append({
                'column_id': index_col_map['Issue Links'],
                'object_value': issue_link
            })
        if data['Issue Type'] == "Epic":
            epic_name = data['Tasks']
            new_row.cells.append({
                'column_id': index_col_map['Epic Name'],
                'object_value': epic_name
            })
        if data['Issue Type'] == "Story" and \
                data['Parent Issue Type'] == "Epic":
            epic_link = data['Parent Ticket']
            new_row.cells.append({
                'column_id': index_col_map['Epic Link'],
                'object_value': epic_link
            })
        components = ["Autogenerated by Smartsheet", "Sync to Smartsheet"]
        new_row.cells.append({
            'column_id': index_col_map['Components'],
            'object_value': {
                'objectType': "MULTI_PICKLIST",
                'values': components
            }
        })

        index_rows_to_add.append(new_row)
    return index_rows_to_add


def push_jira_ticket_to_sheet(sheet, sheet_col_map,
                              index_sheet,
                              index_col_map):
    rows_to_update = []
    for row in index_sheet.rows:
        uuid_value = get_cell_value(row, 'UUID', index_col_map)
        jira_ticket = get_cell_value(row, 'Jira Ticket', index_col_map)

        if not uuid_value:
            msg = str("UUID is {} in Row ID: {} | Sheet ID: {} "
                      "| Sheet Name: {}").format(uuid_value, row.id,
                                                 index_sheet.id,
                                                 index_sheet.name)
            logging.debug(msg)
            continue
        elif not jira_ticket:
            msg = str("Jira Value is {} in Row ID: {} | Sheet ID: {} "
                      "| Sheet Name: {}").format(jira_ticket, row.id,
                                                 index_sheet.id,
                                                 index_sheet.name)
            logging.debug(msg)
            continue

        jira_link = get_cell_data(row, 'Jira Ticket', index_col_map)
        try:
            if has_cell_link(jira_link, "Out") == 'Linked':
                # Skip linked rows
                msg = str("Jira Ticket: {} has already been pushed to "
                          "Row ID: {} | Sheet ID: {} "
                          "| Sheet Name: {}").format(jira_ticket, row.id,
                                                     sheet.id, sheet.name)
                logging.debug(msg)
                continue
        except KeyError as e:
            msg = str("Error getting linked status: {}").format(e)
            logging.warning(msg)

        if bool(re.match(r"\d+-\d+-\d+-\d+", uuid_value)):
            msg = str("UUID column has a value and matches the UUID pattern.")
            logging.debug(msg)
        else:
            msg = str("UUID does not match the pattern. UUID value: {}"
                      "").format(uuid_value)
            logging.debug(msg)
            continue

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
        logging.info(msg)
        write_to_sheet(rows_to_update, sheet, write_method="update")
    else:
        msg = str("All Jira Tickets have pre-existing links to Sheet ID: {} "
                  "| Sheet Name: {}").format(sheet.id, sheet.name)
        logging.info(msg)


def link_predecessor_tickets(parent):
    # Follow predecessor tree, link issues as you go
    # Roll up the predecessor chain and then
    # 1. Find top level Jira Ticket -> Create if "Create"
    # 2. Find top level Jira Ticket -> If no Jira value, roll
    #    down
    #    the chain until you find "Create" -> Create
    # 3. Find parent Jira ticket, use to create Issue Link
    # 4. Form row, add to list of rows to create and push to Jira
    #    Index
    return parent


def write_to_sheet(rows_to_write, sheet, smartsheet_client,
                   write_method="add"):
    if rows_to_write and write_method == "add":
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet.id, sheet.name)
        logging.debug(msg)

        # msg = 'OK'
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


def build_row_data(row, col_map):
    row_data = {}
    for col in project_columns:
        try:
            cell_value = get_cell_value(row, col, col_map)
            row_data[col] = cell_value
        except KeyError:
            continue
    return row_data


def create_new_tickets(source_sheets, index_sheet, index_col_map):

    tickets_to_create = {}

    for sheet in source_sheets:
        col_map = get_column_map(sheet)
        msg = str("Loaded {} rows from Sheet ID: {} | Sheet Name: {}"
                  "").format(len(sheet.rows), sheet.id, sheet.name)
        logging.info(msg)
        try:
            if col_map[uuid_col]:
                pass
        except KeyError:
            msg = str("Sheet ID {} | Sheet Name {} doesn't have UUID column. "
                      "Skipping sheet. (KeyError)").format(sheet.id,
                                                           sheet.name)
            logging.debug(msg)
            continue
        push_jira_ticket_to_sheet(sheet, col_map, index_sheet, index_col_map)

        sheet_rows_to_update = []
        for row in sheet.rows:
            logging.debug("------------------------")
            logging.debug("New Row")
            logging.debug("------------------------")
            # row_data = {}
            # for col in project_columns:
            #     try:
            #         cell_value = get_cell_value(row, col, col_map)
            #         row_data[col] = cell_value
            #     except KeyError:
            #         continue
            row_data = build_row_data(row, col_map)
            if row_data["Summary"] == "True":
                # Skip summary rows
                msg = str("Skipped because Summary column was true")
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["Team"] is None:
                # Need team defined (so we can get project key). Skip
                msg = str("Skipped because Team column was empty.")
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["UUID"] is None:
                # No UUID means we can't push the created ticket IDs back
                # into the program sheets. Skip.
                msg = str("Skipped because UUID column was empty.")
                logging.debug(msg)
                logging.debug(row_data)
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
                msg = str("Added row_data to tickets_to_create and set"
                          "Jira Ticket column in Plan sheet to Pending...")
                logging.debug(msg)
                logging.debug(row_data)
                continue
            if row_data["Jira Ticket"] == "Pending..."\
                    or row_data['Parent Ticket'] == "Pending...":
                # Skip any row that's already in process
                msg = str("4Skipped because Jira Ticket or Parent Ticket "
                          "column was set to Pending...")
                logging.debug(msg)
                logging.debug(row_data)
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
                    msg = str("Parent Ticket isn't Create or Pending... but"
                              "it does have a value. Adding row_data to "
                              "tickets_to_create and setting Jira Ticket "
                              "to Pending...")
                    logging.debug(msg)
                    logging.debug(row_data)
                    continue
            logging.debug("Made it past all IFs without triggering")
            logging.debug(row_data)
        write_to_sheet(sheet_rows_to_update, sheet=sheet,
                       write_method="update")

    logging.debug("Top-level Rows to create first")
    logging.debug("------------------------")
    for k, v in tickets_to_create.items():
        msg = str("{}: {}").format(k, v)
        logging.debug(msg)

    return tickets_to_create


# TODO: Drop parent rows once written to index sheet by removing the "Create"
# from the Jira Ticket field and/or filtering out UUID matches + nonNull
# Jira Ticket field on the Index sheet
def create_tickets(smartsheet_client, minutes=dev_minutes):
    source_sheets, index_sheet, index_col_map = refresh_sheets(
        smartsheet_client, minutes)
    parent = create_new_tickets(source_sheets, index_sheet, index_col_map)
    logging.debug("Parent Dict")
    logging.debug("------------------------")
    logging.debug(parent)
    msg = str("Parent Length: {}").format(len(parent))
    logging.debug(msg)
    if parent:
        # Write parent rows
        # TODO: toggle hidden flag to prevent pushing again (filter
        # above)
        rows_to_write = form_rows(parent, index_col_map)
        write_to_sheet(rows_to_write, index_sheet, smartsheet_client)
    elif not parent:
        msg = str("No parent or child rows remain to be written to the "
                  "Jira Index Sheet.")
        logging.info(msg)
    else:
        msg = str("Looping through rows rows to create Jira Tickts "
                  "failed with an unknown error.")
        logging.warning(msg)
