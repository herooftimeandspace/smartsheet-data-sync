import base64
import json
import logging
import os
import threading
import time
from logging.config import dictConfig
import gc

import boto3
import smartsheet
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BlockingScheduler
from botocore.exceptions import ClientError

from uuid_module.cell_link_sheet_data import write_uuid_cell_links
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_sub_indexs)
from uuid_module.helper import get_timestamp, json_extract, truncate
from uuid_module.variables import (log_location, minutes, module_log_name,
                                   sheet_columns)
from uuid_module.write_data import write_jira_index_cell_links, write_uuids

start = time.time()

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample
# code, visit the AWS docs:
# https://aws.amazon.com/developers/getting-started/python/


def get_secret():
    """Gets the API token from AWS Secrets Manager

    Raises:
        e: DecryptionFailureException.
        e: InternalServiceErrorException
        e: InvalidParameterException
        e: InvalidRequestException
        e: ResourceNotFoundException

    Returns:
        str: The Smartsheet API key
    """
    secret_name = "prod/smartsheet-data-sync/api-token"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the
    # 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/
    # apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using
            # the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current
            # state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these
        # fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']

            api_key = json.loads(str(secret))
            api_key = json_extract(api_key, "SMARTSHEET_ACCESS_TOKEN")
            api_key = ''.join(map(str, api_key))
            return api_key
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
            return decoded_binary_secret


cwd = os.path.dirname(os.path.abspath(__file__))
log_location = os.path.join(cwd, log_location)
logging_config = dict(
    version=1,
    formatters={
        'f': {'format':
              "%(asctime)s - %(levelname)s - %(message)s"}
    },
    handlers={
        # 'console': {
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'f',
        #     'level': logging.INFO
        # },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'f',
            'level': logging.DEBUG,
            'filename': log_location + module_log_name
        },
        'docker': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.INFO,
            'stream': 'ext://sys.stdout'
        }
    },
    root={
        'handlers': ['file', 'docker'],  # 'console'
        'level': logging.DEBUG,
        'disable_existing_loggers': False
    },
)

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

logging.debug("------------------------")
logging.debug("Initializing Smartsheet Client API")
logging.debug("------------------------")
# Initialize client. Uses the API token in the environment variable
# "SMARTSHEET_ACCESS_TOKEN"
os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret()
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


def full_jira_sync():
    start = time.time()
    msg = str("Starting refresh of Smartsheet project data.")
    logging.info(msg)

    global sheet_id_lock
    with sheet_id_lock:
        sheet_ids = get_all_sheet_ids(smartsheet_client)
        sheet_ids = list(set(sheet_ids))

    global sheet_index_lock
    # Calculate a number minutes ago to get only the rows that were modified
    # since the last run.

    def refresh_source_sheets(minutes):
        _, modified_since = get_timestamp(minutes)
        source_sheets = []
        with sheet_index_lock:
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

    blank_uuid_index = get_blank_uuids(source_sheets, smartsheet_client)
    if blank_uuid_index:
        logging.info("There are {} project sheets to be updated".format(
            len(blank_uuid_index)))
        sheets_updated = write_uuids(blank_uuid_index, smartsheet_client)
        if sheets_updated > 0:
            logging.info("{} project sheet(s) updated".format(sheets_updated))
            source_sheets = refresh_source_sheets(minutes)
        else:
            logging.info("No UUIDs to update.")

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
                source_sheets, sheet_columns, smartsheet_client)
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
        jira_sub_index, project_sub_index = get_sub_indexs(
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

    logging.info("Writing Jira cell links.")
    write_jira_index_cell_links(project_sub_index, smartsheet_client)
    logging.debug("Writing UUID cell links.")
    write_uuid_cell_links(project_uuid_index,
                          source_sheets, smartsheet_client)

    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    logging.info(
        "Retrieving everything took: {} seconds.".format(elapsed))
    gc.collect()


def track_time(function):
    """Helper function to track how long each task takes

    Args:
        function (function): The function to time

    Returns:
        float: The amount of time in seconds, truncated to 3 decimal places.
    """
    start = time.time()
    function()
    end = time.time()
    elapsed = end - start
    elapsed = truncate(elapsed, 3)
    return elapsed


def main():
    """Runs a one time instance of all tasks to pre-cache data for the
       scheduler. Afterwards, adds each task to the scheduler at a set
       interval.

    Returns:
        bool: Returns True if main successfully initialized and scheduled jobs,
              False if not.
    """
    start_total = time.time()
    msg = str("Starting first time initialization of Smartsheet project data.")
    logging.info(msg)

    elapsed1 = track_time(full_jira_sync)
    logging.info(
        "Initial run took: {} seconds.".format(elapsed1))

    end_total = time.time()
    total = end_total - start_total
    total = truncate(total, 3)
    logging.info("Total time: {} seconds.".format(total))

    logging.debug("------------------------")
    logging.debug("Adding job to refresh everything. "
                  "Interval = every 1 minute.")
    logging.debug("------------------------")
    scheduler.add_job(full_jira_sync,
                      'interval',
                      seconds=30)
    return True


if __name__ == '__main__':
    """Runs main() and then starts the scheduler.
    """
    # main()
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
            scheduler.shutdown()
            logging.debug("------------------------")
            logging.debug("Scheduled Jobs ended without interruption.")
            logging.debug("------------------------")
    else:
        logging.error("Issue with running MAIN. Process terminated.")
