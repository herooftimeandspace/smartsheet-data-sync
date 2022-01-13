import gc
import logging
import os
import sys
import threading
import time
from logging.config import dictConfig

import smartsheet
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BlockingScheduler
from tests.test_build_data import jira_index_sheet

from uuid_module.cell_link_sheet_data import write_uuid_cell_links
# from uuid_module.cell_link_sheet_data import write_uuid_cell_links
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes, refresh_source_sheets)
from uuid_module.helper import truncate
from uuid_module.variables import (dev_jira_idx_sheet, dev_workspace_id,
                                   log_location, minutes, module_log_name,
                                   prod_jira_idx_sheet, prod_workspace_id,
                                   sheet_columns)
from uuid_module.write_data import write_jira_index_cell_links, write_uuids

start = time.time()

cwd = os.path.dirname(os.path.abspath(__file__))
log_location = os.path.join(cwd, log_location)


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
env = sys.argv[1:]
env = env[0]
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
os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
smartsheet_client = smartsheet.Smartsheet()
# Make sure we don't miss any error
smartsheet_client.errors_as_exceptions(True)

sheet_id_lock = threading.Lock()
sheet_index_lock = threading.Lock()
project_index_lock = threading.Lock()
end = time.time()
elapsed = end - start
elapsed = truncate(elapsed, 2)
logging.debug("Initialization took: {}".format(elapsed))

# TODO: Refactor so that dev_index_sheet and dev_workspace_id
# are used by default. Only if --prod is passed does the prod_index_sheet
# and prod_workspace_ids get used. Do this by making those variables
# optional inside the functions and defaul to the dev environment.


def full_jira_sync(minutes):
    if not isinstance(minutes, int):
        msg = str("Minutes should be type: int, not {}").format(type(minutes))
        raise TypeError(msg)
    if minutes < 0:
        msg = str("Minutes should be >= 0, not {}").format(minutes)
        raise ValueError(msg)

    start = time.time()
    msg = str("Starting refresh of Smartsheet project data. "
              "Looking back {} minutes from {}"
              "").format(minutes,
                         time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.localtime(start)))
    logging.debug(msg)

    global sheet_id_lock
    with sheet_id_lock:
        sheet_ids = get_all_sheet_ids(
            smartsheet_client, minutes, workspace_id, index_sheet)
        sheet_ids = list(set(sheet_ids))

    global sheet_index_lock
    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.

    with sheet_index_lock:
        source_sheets = refresh_source_sheets(
            smartsheet_client, sheet_ids, minutes)

    blank_uuid_index = get_blank_uuids(source_sheets)
    if blank_uuid_index:
        logging.info("There are {} project sheets to be updated "
                     "with UUIDs".format(len(blank_uuid_index)))
        sheets_updated = write_uuids(blank_uuid_index, smartsheet_client)
        if sheets_updated:
            logging.info("{} project sheet(s) updated with UUIDs"
                         "".format(sheets_updated))

    if not source_sheets:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Sheet index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    global project_index_lock
    with project_index_lock:
        try:
            project_uuid_index = get_all_row_data(
                source_sheets, sheet_columns, minutes)
        except ValueError as e:
            msg = str("Getting all row data returned an error. {}").format(e)
            logging.error(msg)

    if project_uuid_index:
        logging.info("Project Index is {} "
                     "items long".format(len(project_uuid_index)))

    if not project_uuid_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Project UUID Index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    try:
        jira_sub_index, project_sub_index = get_sub_indexes(
            project_uuid_index)
    except ValueError as e:
        msg = str("Getting sub-indexes returned an error. {}").format(e)
        logging.error(msg)

    if project_sub_index:
        logging.info("Project Sub Index is {} "
                     "items long".format(len(project_sub_index)))

    if not project_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Project sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    if jira_sub_index:
        logging.info("Jira Sub Index is {} "
                     "items long".format(len(jira_sub_index)))

    if not jira_sub_index:
        end = time.time()
        elapsed = end - start
        elapsed = truncate(elapsed, 3)
        msg = str("Jira sub-index is empty. "
                  "Aborting after {} seconds.").format(elapsed)
        logging.info(msg)
        return

    # TODO: Load Jira Index Sheet HERE by calling the API. Pass the object into
    # creating the Jira Index objects, then write the cell links
    # Centralize smartsheet_client calls, quit passing the object around
    logging.debug("Writing Jira cell links.")
    write_jira_index_cell_links(project_sub_index, smartsheet_client)
    # logging.debug("Writing UUID cell links.")
    # write_uuid_cell_links(project_uuid_index,
    #                       source_sheets, smartsheet_client)

    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    logging.info(
        "Full Jira sync took: {} seconds.".format(elapsed))
    gc.collect()


def full_smartsheet_sync():
    start = time.time()
    msg = str("Starting refresh of Smartsheet project data.").format()
    logging.debug(msg)

    global sheet_id_lock
    with sheet_id_lock:
        sheet_ids = get_all_sheet_ids(smartsheet_client, minutes, workspace_id)
        sheet_ids = list(set(sheet_ids))

    global sheet_index_lock
    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.

    with sheet_index_lock:
        source_sheets = refresh_source_sheets(
            smartsheet_client, sheet_ids, minutes)

    with project_index_lock:
        try:
            project_uuid_index = get_all_row_data(
                source_sheets, sheet_columns, minutes)
        except ValueError as e:
            msg = str("Getting all row data returned an error. {}").format(e)
            logging.error(msg)

    write_uuid_cell_links(project_uuid_index, source_sheets, smartsheet_client)

    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    logging.info(
        "Full Smartsheet cross-sheet sync took: {} seconds.".format(elapsed))
    gc.collect()


def track_time(func, **args):
    if not callable(func):
        msg = str("Func should be type: function, not {}").format(type(func))
        raise TypeError(msg)

    """Helper function to track how long each task takes

    Args:
        func (function): The function to time

    Raises:
        TypeError: If func isn't a function

    Returns:
        float: The amount of time in seconds, truncated to 3 decimal places.
    """
    start = time.time()
    func(**args)
    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    return elapsed


def main():
    """Configures the scheduler to run two jobs. One job runs full_jira_sync
       every 30 seconds and looks back based on the minutes defined in
       variables. The second job runs full_jira_sync every day at 1:00am UTC
       and looks back 1 week.

    Returns:
        bool: Returns True if main successfully initialized and scheduled jobs,
              False if not.
    """
    logging.debug("------------------------")
    logging.debug("Adding job to refresh Jira tickets in real time. "
                  "Interval = every 30 seconds.")
    logging.debug("------------------------")
    scheduler.add_job(full_jira_sync,
                      'interval',
                      args=[minutes],
                      seconds=30)

    logging.debug("------------------------")
    logging.debug("Adding job to get all data in the past week. "
                  "Cron = every day at 1:00am UTC.")
    logging.debug("------------------------")
    scheduler.add_job(full_jira_sync,
                      'cron',
                      args=[10080],
                      day='*/1',
                      hour='1')
    return True


if __name__ == '__main__':
    """Runs main(). If main returns True, starts the scheduler. If main
       returns False, logs an error and terminates the application.
    """
    main = main()
    if main:
        try:
            logging.debug("------------------------")
            logging.debug("Starting job scheduler.")
            logging.debug("------------------------")
            scheduler.start()
        except KeyboardInterrupt:
            logging.warning("------------------------")
            logging.warning("Scheduled Jobs shut down due "
                            "to Keyboard Interrupt.")
            logging.warning("------------------------")
            scheduler.shutdown()
    else:
        logging.error("Issue with running MAIN. Process terminated.")
        exit()
