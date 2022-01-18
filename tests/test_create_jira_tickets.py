import smartsheet
import pytest
import json
import logging
import os
from uuid_module.create_jira_tickets import create_tickets
from uuid_module.get_data import get_secret, get_secret_name

logger = logging.getLogger(__name__)
cwd = os.path.dirname(os.path.abspath(__file__))


# Need Mock
@pytest.fixture(scope="module")
def smartsheet_client(env):
    secret_name = get_secret_name(env)
    try:
        os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
    except TypeError:
        raise ValueError("Refresh Isengard Auth")
    smartsheet_client = smartsheet.Smartsheet()
    # Make sure we don't miss any error
    smartsheet_client.errors_as_exceptions(True)
    return smartsheet_client


# TODO: Mock API calls to Smartsheet for getting new test
def test_create_tickets(smartsheet_client):
    with pytest.raises(TypeError):
        create_tickets("smartsheet_client")

    assert type(smartsheet_client) == smartsheet.Smartsheet()
