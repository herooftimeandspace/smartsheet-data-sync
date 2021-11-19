import base64
import json
import logging
import os
from collections import defaultdict
from datetime import datetime

import boto3
import pytest
import pytz
import smartsheet
from botocore.exceptions import ClientError
from tests.test_helper import row, sheet
from uuid_module.get_data import (get_all_row_data, get_secret,
                                  get_secret_name, refresh_source_sheets)
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, json_extract)
from uuid_module.variables import (jira_col, jira_idx_sheet, sheet_columns,
                                   summary_col, uuid_col, workspace_id)

logger = logging.getLogger(__name__)

utc = pytz.UTC


@pytest.fixture
def env():
    return "-debug"


# Need Mock
@pytest.fixture
def smartsheet_client(env):
    secret_name = get_secret_name(env)
    print(secret_name)
    os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
    smartsheet_client = smartsheet.Smartsheet()
    # Make sure we don't miss any error
    smartsheet_client.errors_as_exceptions(True)
    return smartsheet_client


@pytest.fixture
def sheet_ids():
    return [3027747506284420]


@pytest.fixture
def minutes():
    return 5


@pytest.fixture
def source_sheets(smartsheet_client, sheet_ids):
    source_sheets = refresh_source_sheets(smartsheet_client, sheet_ids)
    return source_sheets


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


# Type testing. Separate tests needed for integraiton.
def test_refresh_source_sheets(smartsheet_client, sheet_ids, minutes=0):
    # Validate Smartsheet client.
    # with pytest.raises(TypeError):
    #     test_source_sheets = refresh_source_sheets(
    #         "smartsheet_client", sheet_ids, 0)
    with pytest.raises(TypeError):
        test_source_sheets = refresh_source_sheets(
            smartsheet_client, sheet_ids, "minutes")
    with pytest.raises(TypeError):
        test_source_sheets = refresh_source_sheets(
            smartsheet_client, 7, minutes)
    with pytest.raises(ValueError):
        test_source_sheets = refresh_source_sheets(
            smartsheet_client, ["One", "Two", "Three"], -1)


def test_get_all_row_data(source_sheets, columns, minutes):
    with pytest.raises(TypeError):
        get_all_row_data("source_sheets", columns, minutes)
    with pytest.raises(TypeError):
        get_all_row_data(source_sheets, "columns", minutes)
    with pytest.raises(TypeError):
        get_all_row_data(source_sheets, columns, "minutes")
    with pytest.raises(ValueError):
        get_all_row_data(source_sheets, columns, -1)
    row_data = get_all_row_data(source_sheets, columns, minutes)
    print(row_data)
    # assert row_data is not None


# def test_get_blank_uuids(source_sheets):
#     assert 0 == 0


# def test_load_jira_index(smartsheet_client):
#     assert 0 == 0


# def test_get_sub_indexes(project_data):
#     assert 0 == 0


# def test_get_all_sheet_ids(smartsheet_client, minutes):
#     assert 0 == 0


# def test_get_secret(secret_name):
#     assert 0 == 0


def test_get_secret_name(env):
    with pytest.raises(TypeError):
        actual = get_secret_name(1)
    with pytest.raises(ValueError):
        actual = get_secret_name('')

    expected = "staging/smartsheet-data-sync/svc-api-token"
    actual = get_secret_name(env)
    assert expected == actual
