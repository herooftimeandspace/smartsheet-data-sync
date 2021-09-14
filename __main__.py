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

# from uuid_module.cell_link_sheet_data import write_uuid_cell_links
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes)
from uuid_module.helper import get_timestamp, truncate
from uuid_module.variables import (log_location, minutes, module_log_name,
                                   sheet_columns)
from uuid_module.write_data import write_jira_index_cell_links, write_uuids

start = time.time()

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample
# code, visit the AWS docs:
# https://aws.amazon.com/developers/getting-started/python/


cwd = os.path.dirname(os.path.abspath(__file__))
log_location = os.path.join(cwd, log_location)


def set_logging_config(env):
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
    for e in env:
        if e in ("-s", "--staging", "-staging"):
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
        elif e in ("-p", "--prod", "-prod"):
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
        elif e in ("-d", "--debug", "-debug"):
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

for e in env:
    if e in ("--", None):
        logging.error("No environment flag set. Please use --debug, --staging "
                      "or --prod. Terminating app.")
        quit()
    else:
        msg = str("The {} flag was passed from the command line").format(env)
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


def full_jira_sync(minutes):
    start = time.time()
    msg = str("Starting refresh of Smartsheet project data. "
              "Looking back {} minutes from {}"
              "").format(minutes,
                         time.strftime('%Y-%m-%d %H:%M:%S',
                                       time.localtime(start)))
    logging.debug(msg)

    global sheet_id_lock
    with sheet_id_lock:
        sheet_ids = get_all_sheet_ids(smartsheet_client, minutes)
        sheet_ids = list(set(sheet_ids))

    global sheet_index_lock
    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.

    def refresh_source_sheets(minutes):
        _, modified_since = get_timestamp(minutes)
        source_sheets = []
        with sheet_index_lock:
            source_sheets = []
            # Iterate through each sheet ID.
            for sheet_id in sheet_ids:
                # Query the Smartsheet API for the sheet details
                sheet = smartsheet_client.\
                    Sheets.get_sheet(
                        sheet_id, rows_modified_since=modified_since)
                source_sheets.append(sheet)
                logging.debug("Loading Sheet ID: {} | "
                              "Sheet Name: {}".format(sheet.id, sheet.name))
        return source_sheets

    source_sheets = refresh_source_sheets(minutes)

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


def track_time(function, **args):
    """Helper function to track how long each task takes

    Args:
        function (function): The function to time

    Returns:
        float: The amount of time in seconds, truncated to 3 decimal places.
    """
    start = time.time()
    function(**args)
    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    return elapsed


def main():
    """Configures the scheduler to run two jobs. One job runs every 30 seconds
       and looks back based on the minutes defined in variables. The second
       job runs every day at 1:00am UTC and looks back 1 week.

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
    """Runs main() and then starts the scheduler.
    """
    main = main()
    if main:
        try:
            logging.debug("------------------------")
            logging.debug("Starting job scheduler.")
            logging.debug("------------------------")
            scheduler.start()
        except KeyboardInterrupt:
            logging.info("------------------------")
            logging.info("Scheduled Jobs shut down due "
                         "to Keyboard Interrupt.")
            logging.info("------------------------")
            scheduler.shutdown()
    else:
        logging.error("Issue with running MAIN. Process terminated.")
