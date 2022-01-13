import logging
import os
from logging.config import dictConfig

import pytz
import smartsheet
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BlockingScheduler

from uuid_module.get_data import (get_all_sheet_ids, get_jira_index_sheet,
                                  get_secret, get_secret_name,
                                  refresh_source_sheets)
from uuid_module.helper import get_cell_value, get_column_map
from uuid_module.variables import (dev_jira_idx_sheet, dev_workspace_id,
                                   log_location, module_log_name,
                                   prod_jira_idx_sheet, prod_workspace_id,
                                   uuid_col)

cwd = os.path.dirname(os.path.abspath(__file__))
log_location = os.path.join(cwd, log_location)
utc = pytz.UTC
minutes = 525600


def set_logging_config(env):
    if not isinstance(env, str):
        msg = str("Environment should be type: str, not {}").format(
            type(env))
        raise TypeError(msg)
    if env not in ("-s", "--staging", "-staging", "-p", "--prod", "-prod",
                   "-d", "--debug", "-debug"):
        msg = str("Invalid environment flag. '{}' was passed but it should "
                  "be '--debug', '--staging' or '--prod'").format(
            type(env))
        raise ValueError(msg)

    logging_config = dict(
        version=1,
        formatters={
            'f': {'format':
                  "%(asctime)s - %(levelname)s - %(message)s"}
        },
        handlers={
            'docker': {
                'class': 'logging.StreamHandler',
                'formatter': 'f',
                'level': logging.INFO,
                'stream': 'ext://sys.stdout'
            }
        },
        root={
            'handlers': ['docker'],  # 'console', 'file'
            'level': logging.DEBUG,
            'disable_existing_loggers': False
        },
    )
    if env in ("-s", "--staging", "-staging"):
        logging_config = dict(
            version=1,
            formatters={
                'f': {'format':
                      "%(asctime)s - %(levelname)s - %(message)s"}
            },
            handlers={
                'docker': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f',
                    'level': logging.INFO,
                    'stream': 'ext://sys.stdout'
                }
            },
            root={
                'handlers': ['docker'],  # 'console', 'file'
                'level': logging.DEBUG,
                'disable_existing_loggers': False
            },
        )
    elif env in ("-p", "--prod", "-prod"):
        logging_config = dict(
            version=1,
            formatters={
                'f': {'format':
                      "%(asctime)s - %(levelname)s - %(message)s"}
            },
            handlers={
                'docker': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f',
                    'level': logging.INFO,
                    'stream': 'ext://sys.stdout'
                }
            },
            root={
                'handlers': ['docker'],  # 'console', 'file'
                'level': logging.DEBUG,
                'disable_existing_loggers': False
            },
        )
    elif env in ("-d", "--debug", "-debug"):
        logging_config = dict(
            version=1,
            formatters={
                'f': {'format':
                      "%(asctime)s - %(levelname)s - %(message)s"}
            },
            handlers={
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'f',
                    'level': logging.DEBUG,
                    'filename': log_location + module_log_name
                },
                'docker': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f',
                    'level': logging.DEBUG,
                    'stream': 'ext://sys.stdout'
                }
            },
            root={
                'handlers': ['docker', 'file'],  # 'console', 'file'
                'level': logging.DEBUG,
                'disable_existing_loggers': False
            },
        )

    return logging_config


# Initialize client. Uses the API token in the environment variable
# "SMARTSHEET_ACCESS_TOKEN", which is pulled from the AWS Secrets API.
env = '--debug'
logging_config = set_logging_config(env)
try:
    os.mkdir(log_location)
    f = open(log_location + module_log_name, "w")
    f.close
    dictConfig(logging_config)
except FileExistsError:
    dictConfig(logging_config)

logger = logging.getLogger()

executors = {
    'default': ThreadPoolExecutor(1),
    'processpool': ProcessPoolExecutor(1)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 5
}
scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)

if env in ("--", None):
    logging.error("No environment flag set. Please use --debug, --staging "
                  "or --prod. Terminating app.")
    quit()
else:
    msg = str("The {} flag was passed from the command line").format(env)
    logging.info(msg)
    if env in ("-s", "--staging", "-staging", "-d", "--debug", "-debug"):
        msg = str("Using default debug/staging variables for workspace_id "
                  "and Jira index sheet").format()
        logging.info(msg)
    elif env in ("-p", "--prod", "-prod"):
        workspace_id = prod_workspace_id
        index_sheet = prod_jira_idx_sheet
        msg = str("Set workspace_id to: {} and index_sheet to: {} "
                  "for Prod environment").format(workspace_id, index_sheet)
        logging.info(msg)

logging.debug("------------------------")
logging.debug("Initializing Smartsheet Client API")
logging.debug("------------------------")
secret_name = get_secret_name(env)
try:
    os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
except TypeError:
    msg = str("Refresh Isengard credentials")
    logging.error(msg)
    exit()
smartsheet_client = smartsheet.Smartsheet()
# Make sure we don't miss any error
smartsheet_client.errors_as_exceptions(True)

sheet_ids = get_all_sheet_ids(
    smartsheet_client, minutes, workspace_id=dev_workspace_id,
    index_sheet=dev_jira_idx_sheet)
msg = str("Sheet IDs object type {}, object values {}").format(
    type(sheet_ids), sheet_ids)
logging.debug(msg)
source_sheets = refresh_source_sheets(smartsheet_client, sheet_ids, minutes)

# TODO: Load index sheet and kick off 2 functions. 1: Create new tickets
# 2: Copy created tickets to program sheets via UUID
dev_index_sheet = get_jira_index_sheet(smartsheet_client, dev_jira_idx_sheet)
dev_index_col_map = get_column_map(dev_index_sheet)
project_columns = ["Summary", "Tasks", "Issue Type", "Jira Ticket",
                   "Parent Ticket", "Program", "Initiative", "Team", "UUID",
                   "Predecessors", "ParentUUID", "Project Key"]
jira_index_columns = ["Tasks", "Issue Type", "Jira Ticket", "Issue Links",
                      "Project Key", "Components", "Labels", "Epic Link",
                      "Epic Name", "Summary"]


def form_rows(row_dict, index_col_map=dev_index_col_map):
    index_rows_to_add = []
    for _, data in row_dict.items():
        new_row = smartsheet_client.models.Row()
        new_row.to_bottom = True
        if data['Jira Created'] is True:
            continue
        for col_name, value in data.items():
            if col_name == 'Summary':
                # Skip writting summary column, Index Sheet doesn't have it
                continue

            try:
                col_id = index_col_map[col_name]
            except KeyError:
                msg = str("KeyError when looking up column name {} in "
                          "the Jira Index Column Map").format(col_name)
                logging.info(msg)
                # Move to next data set, create the row with data that works
                continue
            new_row.cells.append({
                'column_id': col_id,
                'value': value
            })
        # Set Jira Created to True so that when we loop back through, we skip
        # This row
        data['Jira Created'] = True
        index_rows_to_add.append(new_row)
    return index_rows_to_add, data


def write_to_index(rows_to_write, sheet=dev_index_sheet):
    if rows_to_write:
        msg = str("Writing {} rows back to Sheet ID: {} "
                  "| Sheet Name: {}").format(len(rows_to_write),
                                             sheet.id, sheet.name)
        logging.debug(msg)

        msg = 'OK'
        # result = smartsheet_client.Sheets.add_rows(int(sheet.id),
        #                                               rows_to_write)
        # msg = str("Smartsheet API responded with the "
        #           "following message: {}").format(result.result)
        logging.debug(msg)
    else:
        msg = str("No rows added to Sheet ID: "
                  "{} | Sheet Name: {}").format(sheet.id, sheet.name)
        logging.debug(msg)
    return


def create_new_tickets():
    true_count = 0
    false_count = 0
    ticket_exists = 0
    pred_count = 0
    create_parent_first = 0
    child_row_data = {}
    parent_row_data = {}

    for sheet in source_sheets:
        col_map = get_column_map(sheet)
        logging.debug("Loaded " + str(len(sheet.rows)) + " rows from sheet: "
                      + str(sheet.id) + " | Sheet Name: " + sheet.name)
        try:
            if col_map[uuid_col]:
                pass
        except KeyError:
            logging.debug("Sheet ID {} | Sheet Name {} "
                          "doesn't have UUID column. "
                          "Skipping sheet. (KeyError)".format(sheet.id,
                                                              sheet.name))
            continue

        for row in sheet.rows:
            row_data = {}
            for col in project_columns:
                try:
                    cell_value = get_cell_value(row, col, col_map)
                    row_data[col] = cell_value
                except KeyError:
                    continue

            if row_data["Summary"] == "True":
                # Skip summary rows
                false_count += 1
                continue
            elif row_data["Parent Ticket"] is None and row_data["Jira Ticket"]\
                    in ("Create", "create"):
                try:
                    if row_data["Jira Created"]:
                        # Skip rows that have been pushed to the index already
                        continue
                except KeyError:
                    row_data["Jira Created"] = False
                parent_row_data[row.id] = row_data
                create_parent_first += 1
                # Re run loop with parent row (via ParentUUID)
                continue
            elif row_data["Jira Ticket"] not in ("Create", "create"):
                if row_data["Jira Ticket"] is not None:
                    # Anything other than None or Create is treated as
                    # an existing ticket
                    ticket_exists += 1
                    continue
                else:
                    # Field isn't Create, don't need to create a ticket
                    false_count += 1
                    continue
            elif row_data["Predecessors"] is not None:
                pred_count += 1
                # Follow predecessor tree, link issues as you go
                # Roll up the predecessor chain and then
                # 1. Find top level Jira Ticket -> Create if "Create"
                # 2. Find top level Jira Ticket -> If no Jira value, roll
                #    down
                #    the chain until you find "Create" -> Create
                # 3. Find parent Jira ticket, use to create Issue Link
                # 4. Form row, add to list of rows to create and push to Jira
                #    Index
                continue
            elif row_data["Team"] is None:
                # Need team defined (so we can get project key). Skip
                continue

            # elif row_data["UUID"] is None:
            # # No UUID means we can't push the created ticket IDs back
            # # into the program sheets. Skip.
            #     continue

            # Append the row data to the dict
            # TODO: Changes the key to UUID, not row.id
            # Don't process child data until parent_data_rows is false
            child_row_data[row.id] = row_data
            # logging.info(all_row_data[row.id])
            true_count += 1

    msg = str("True Count: {}").format(true_count)
    logging.debug(msg)
    msg = str("False Count: {}").format(false_count)
    logging.debug(msg)
    msg = str("Predecessor Count: {}").format(pred_count)
    logging.debug(msg)
    msg = str("Ticket Exists: {}").format(ticket_exists)
    logging.debug(msg)
    msg = str("Parents to Create first: {}").format(create_parent_first)
    logging.debug(msg)
    logging.debug("Parent Rows to create first")
    logging.debug("------------------------")
    for k, v in parent_row_data.items():
        msg = str("{}: {}").format(k, v)
        logging.debug(msg)

    logging.debug("Child Rows to skip")
    logging.debug("------------------------")
    for k, v in child_row_data.items():
        msg = str("{}: {}").format(k, v)
        logging.debug(msg)

    return parent_row_data, child_row_data


def loop(parent, child):
    if parent:
        # Write parent rows
        # TODO: toggle hidden flag to prevent pushing again (filter
        # above)
        rows_to_write, looped_parent = form_rows(parent)
        write_to_index(rows_to_write, dev_index_sheet)
        loop(looped_parent, child)
    elif parent is None and child:
        rows_to_write = form_rows(child)
        write_to_index(rows_to_write, dev_index_sheet)
        loop(parent, child)
    elif parent is None and child is None:
        msg = str("No parent or child rows remain to be written to the "
                  "Jira Index Sheet.")
        logging.debug(msg)
        exit()
    else:
        msg = str("Looping through parent/child rows to create Jira Tickts "
                  "failed with an unknown error.")
        logging.warning(msg)
        exit()


parent, child = create_new_tickets()
loop(parent, child)
