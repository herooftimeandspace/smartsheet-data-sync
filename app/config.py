import base64
import json
import logging
import os
import time
from logging.config import dictConfig

import boto3
import smartsheet
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BlockingScheduler
from botocore.exceptions import ClientError
import data_module.helper as helper
import app.variables as app_vars

cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_location = os.path.join(cwd, app_vars.log_location)
logger = logging.getLogger(__name__)


def get_secret(secret_name):
    """Gets the API token from AWS Secrets Manager.

    Raises:
        e: DecryptionFailureException.
        e: InternalServiceErrorException
        e: InvalidParameterException
        e: InvalidRequestException
        e: ResourceNotFoundException

    Returns:
        str: The Smartsheet API key
    """

    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
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
            api_key = helper.json_extract(api_key, "SMARTSHEET_ACCESS_TOKEN")
            api_key = ''.join(map(str, api_key))
            return api_key
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
            return decoded_binary_secret


def get_secret_name(env="--dev"):
    """Gets the name of the secret name to query based on the environmental
       variable set when the app is loaded

    Args:
        env (str, optional): The environment variable. Defaults to "--dev".

    Raises:
        TypeError: Must be a string
        ValueError: Must be on of the approved flags

    Returns:
        str: The Name of the secret to use with the AWS Secrets API.
    """
    if not isinstance(env, str):
        raise TypeError("Env is not type: str")
    elif env not in ("-d", "--debug", "-debug", "--dev", "-dev",
                     "-s", "--staging", "-staging",
                     "-p", "--prod", "-prod"):
        msg = str("Invalid argument passed. Value passed was {}").format(env)
        raise ValueError(msg)

    if env in ("-s", "--staging", "-staging"):
        secret_name = "staging/smartsheet-data-sync/svc-api-token"
        return secret_name
    elif env in ("-p", "--prod", "-prod"):
        secret_name = "prod/smartsheet-data-sync/svc-api-token"
        return secret_name
    elif env in ("-d", "--debug", "-debug", "--dev", "-dev"):
        secret_name = "staging/smartsheet-data-sync/svc-api-token"
        return secret_name


def set_env_vars(env):
    """Sets certain variables based on the flag passed in at the command line.
    Defaults to the development / debug environment variables if not specified

    Args:
        env (str): The environment variable to set

    Raises:
        TypeError: The environment variable must be a str

    Returns:
        dict: All the environment variables as a config.
    """
    if not isinstance(env, str):
        msg = str("Env should be a string, not {}.").format(env)
        raise TypeError(msg)

    global workspace_id
    global index_sheet
    global minutes
    global env_msg
    global push_tickets_sheet

    if env in ("--debug", "-debug", "--dev", "-dev"):
        workspace_id = app_vars.dev_workspace_id
        index_sheet = app_vars.dev_jira_idx_sheet
        minutes = app_vars.dev_minutes
        push_tickets_sheet = app_vars.dev_push_jira_tickets_sheet
        env_msg = str("Using Dev variables for workspace_id "
                      "and Jira index sheet. Set workspace_id to: {}, "
                      "index_sheet to: {}, and minutes to: {}. "
                      "Pushing tickets to {}"
                      "").format(workspace_id, index_sheet, minutes,
                                 push_tickets_sheet)
    elif env in ("-s", "--staging", "-staging"):
        workspace_id = app_vars.stg_workspace_id
        index_sheet = app_vars.stg_jira_idx_sheet
        minutes = app_vars.stg_minutes
        push_tickets_sheet = app_vars.dev_push_jira_tickets_sheet
        env_msg = str("Using Staging variables for workspace_id "
                      "and Jira index sheet. Set workspace_id to: {}, "
                      "index_sheet to: {}, and minutes to: {}. "
                      "Pushing tickets to {}"
                      "").format(workspace_id, index_sheet, minutes,
                                 push_tickets_sheet)
    elif env in ("-p", "--prod", "-prod"):
        workspace_id = app_vars.prod_workspace_id
        index_sheet = app_vars.prod_jira_idx_sheet
        minutes = app_vars.prod_minutes
        push_tickets_sheet = app_vars.prod_push_jira_tickets_sheet
        env_msg = str("Using Prod environment variables for workspace_id "
                      "and Jira index sheet. Set workspace_id to: {}, "
                      "index_sheet to: {}, and minutes to: {}. "
                      "Pushing tickets to {}"
                      "").format(workspace_id, index_sheet, minutes,
                                 push_tickets_sheet)
    else:
        flag = env
        workspace_id = app_vars.dev_workspace_id
        index_sheet = app_vars.dev_jira_idx_sheet
        minutes = app_vars.dev_minutes
        push_tickets_sheet = app_vars.dev_push_jira_tickets_sheet
        env_msg = str("Invalid flag: {}. Using Dev variables. Set "
                      "workspace_id to: {}, index_sheet to: {}, and minutes "
                      "to: {}. Pushing tickets to {}"
                      "").format(flag, workspace_id, index_sheet, minutes,
                                 push_tickets_sheet)
        env = "--dev"
    env_dict = {'env': env, 'env_msg': env_msg, 'workspace_id': workspace_id,
                'index_sheet': index_sheet, 'minutes': minutes,
                'push_tickets_sheet': push_tickets_sheet}
    return env_dict


def set_logging_config(env):
    """Sets the logging config based on the environment variable passed in
       from the command line.

    Args:
        env (str): The environment variable passed in

    Raises:
        TypeError: Env should be a string
        ValueError: Env should be some iteration of prod, staging, dev or debug

    Returns:
        dict: The logging configuration to use
    """
    if not isinstance(env, str):
        msg = str("Environment should be type: str, not {}").format(
            type(env))
        raise TypeError(msg)
    if env not in ("-d", "--debug", "-debug", "--dev", "-dev",
                   "-s", "--staging", "-staging",
                   "-p", "--prod", "-prod"):
        msg = str("Invalid environment flag. '{}' was passed but it should "
                  "be '--dev', '--staging' or '--prod'").format(env)
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
    if env in ("-d", "--debug", "-debug"):
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
                    'filename': log_location + app_vars.module_log_name
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
    elif env in ("--dev", "-dev"):
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
                    'filename': log_location + app_vars.module_log_name
                },
                'docker': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f',
                    'level': logging.DEBUG,
                    'stream': 'ext://sys.stdout'
                }
            },
            root={
                'handlers': ['docker'],  # 'console', 'file'
                'level': logging.DEBUG,
                'disable_existing_loggers': False
            },
        )
    elif env in ("-s", "--staging", "-staging"):
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

    return logging_config


def init(args):
    """Initializes the app and creates global environment variables to use
       elsewhere in the app based on the flag passed in on the command line.

    Args:
        args (list): List of args passed by sys.args[1:]

    Returns:
        dict: The total configuration dict with all global variables
    """
    start = time.time()
    global config
    global env
    global logging_config
    global scheduler
    global logger
    global smartsheet_client

    try:
        env = args[0]
    except IndexError:
        env = '--dev'
    config = set_env_vars(env)

    # Get the logging config and try to create a new file for logs if the
    # config requires it.
    logging_config = set_logging_config(env)
    try:
        os.mkdir(log_location)
        f = open(log_location + app_vars.module_log_name, "w")
        f.close
        dictConfig(logging_config)
    except FileExistsError:
        dictConfig(logging_config)

    logger = logging.getLogger(__name__)

    # Set parameters for the task scheduler
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(2)
    }
    job_defaults = {
        'coalesce': True,
        'max_instances': 5,
        'misfire_grace_time': None
    }
    scheduler = BlockingScheduler(
        executors=executors, job_defaults=job_defaults)

    secret_name = get_secret_name(env)
    token = get_secret(secret_name)
    try:
        os.environ["SMARTSHEET_ACCESS_TOKEN"] = token
    except TypeError:
        msg = str("Refresh Isengard credentials")
        logging.error(msg)
        exit()
    smartsheet_client = smartsheet.Smartsheet()
    smartsheet_client.errors_as_exceptions(True)

    # Defer setting the token until all modules are loaded
    import data_module.smartsheet_api as ss
    ss.set_smartsheet_client()

    config['scheduler'] = scheduler
    config['logging'] = logging_config
    config['token'] = token

    end = time.time()
    elapsed = end - start
    elapsed = helper.truncate(elapsed, 2)
    logging.debug("[Initialization] took {} seconds".format(elapsed))

    return config
