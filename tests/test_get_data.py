import json
import logging
import os

import pytest
import pytz
import smartsheet
from freezegun import freeze_time
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes, load_jira_index,
                                  refresh_source_sheets)
from uuid_module.variables import sheet_columns

from tests.test_helper import row, sheet

# from collections import defaultdict
# from datetime import datetime
# from typing import Type


logger = logging.getLogger(__name__)

utc = pytz.UTC
cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/sheet_response.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col_fixture(sheet_json):
        sheet_json['columns'][22]['name'] = "Not UUID"
        no_uuid_col = smartsheet.models.Sheet(sheet_json)
        return no_uuid_col

    def no_summary_col_fixture(sheet_json):
        sheet_json['columns'][4]['name'] = "Not Summary"
        no_summary_col = smartsheet.models.Sheet(sheet_json)
        return no_summary_col

    sheet = smartsheet.models.Sheet(sheet_json)
    sheet_list = [sheet]
    sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
    sheet_no_summary_col = no_summary_col_fixture(sheet_json)
    return sheet, sheet_list, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture(scope="module")
def jira_index_sheet_fixture():
    with open(cwd + '/dev_jira_index_sheet_response.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    return dev_idx_sheet


@pytest.fixture(scope="module")
def row():
    with open(cwd + '/row_response.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


@pytest.fixture(scope="module")
def row_list():
    with open(cwd + '/row_response.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    row_list = [row]
    return row_list


@pytest.fixture
def env():
    return "-debug"


# Need Mock
@pytest.fixture
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


@pytest.fixture
def sheet_ids():
    return [3027747506284420]


@pytest.fixture
def minutes():
    return 5


# @pytest.fixture
# def source_sheets(smartsheet_client, sheet_ids):
#     source_sheets = refresh_source_sheets(smartsheet_client, sheet_ids)
#     return source_sheets


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


# Type testing. Separate tests needed for integraiton.
@freeze_time("2021-11-18 21:23:54")
def test_refresh_source_sheets(smartsheet_client, sheet_ids, minutes=0):
    # Validate Smartsheet client.
    with pytest.raises(TypeError):
        refresh_source_sheets(
            "smartsheet_client", sheet_ids, 0)
    with pytest.raises(TypeError):
        refresh_source_sheets(
            smartsheet_client, sheet_ids, "minutes")
    with pytest.raises(TypeError):
        refresh_source_sheets(
            smartsheet_client, 7, minutes)
    with pytest.raises(ValueError):
        refresh_source_sheets(
            smartsheet_client, ["One", "Two", "Three"], minutes)
    with pytest.raises(ValueError):
        refresh_source_sheets(
            smartsheet_client, sheet_ids, -1)

    source_sheets = refresh_source_sheets(
        smartsheet_client, sheet_ids, minutes)
    # TODO: Fix to == real value
    assert source_sheets is not None

    source_sheets = refresh_source_sheets(
        smartsheet_client, sheet_ids, 5)
    # TODO: Fix to == real value
    assert source_sheets is not None


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data(sheet_fixture, columns, minutes):
    _, sheet_list, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        get_all_row_data("source_sheets", columns, minutes)
    with pytest.raises(TypeError):
        get_all_row_data(sheet_list, "columns", minutes)
    with pytest.raises(TypeError):
        get_all_row_data(sheet_list, columns, "minutes")
    with pytest.raises(ValueError):
        get_all_row_data(sheet_list, columns, -1)

    with open(cwd + '/row_response.json') as f:
        row_json = json.load(f)
        row_json = dict(row_json)

    # Need to create assertions for data structure and valid return row values
    row_data = get_all_row_data(sheet_list, columns, minutes)
    assert row_data == {None: {'UUID': None, 'Tasks': 'Retrospective',
                               'Description': None, 'Status': None,
                               'Assigned To': None, 'Jira Ticket': None,
                               'Duration': None, 'Start': None,
                               'Finish': None, 'Predecessors': None,
                               'Summary': 'False'}}
    no_sheet_data = get_all_row_data([], columns, minutes)
    assert no_sheet_data is None


@freeze_time("2021-11-18 21:23:54")
def test_get_blank_uuids(sheet_fixture):
    # TODO: Write a test to validate the dict.
    # 7637702645442436,  (Sheet ID, int)
    # {
    #     "sheet_name": "Cloudwatch: Distribution Project Plan", # type: str
    #     "row_data": {  # type: dict
    #         4733217466279812: { (Row ID, int)
    #             "column_id": 2745267022784388, (int)
    #             "uuid": "7637702645442436-4733217466279812-
    #                      2745267022784388-202105112340380000" (str)
    #         }
    #     }
    # }
    _, sheet_list, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        get_blank_uuids("source_sheets")
    blank_uuids = get_blank_uuids(sheet_list)
    # with open(cwd + '/blank_uuids.txt') as f:
    #     print(f)
    assert blank_uuids is not None
    no_uuids = get_blank_uuids([])
    assert no_uuids is None


# import os
# import pytest
# from unittest.mock import patch

# class Worker:
#     def work_on(self):
#         path = os.getcwd()
#         print(f'Working on {path}')
#         return path

# @pytest.fixture()
# def mocked_worker(mocker):  # mocker is pytest-mock fixture
#     mocker.patch('test_file.os.getcwd', return_value="Testing")

# def test_work_on(mocked_worker):
#     worker = Worker()  # here we create instance of Worker, not mock itself!!
#     ans = worker.work_on()
#     assert ans == "Testing"


# TODO: Static return and check for actual values
def test_load_jira_index(smartsheet_client):
    with pytest.raises(TypeError):
        load_jira_index("smartsheet_client")
    dev_idx_sheet, dev_idx_col_map, dev_idx_rows = load_jira_index(
        smartsheet_client)

    assert dev_idx_sheet
    assert dev_idx_col_map
    assert dev_idx_rows


# TODO: Static return and check for actual values
@freeze_time("2021-11-18 21:23:54")
def test_get_sub_indexes(sheet_fixture, columns):
    with pytest.raises(TypeError):
        get_sub_indexes("project_data")
    _, sheet_list, _, _ = sheet_fixture
    project_uuid_index = get_all_row_data(sheet_list, columns, 65)
    jira_sub_index, project_sub_index = get_sub_indexes(project_uuid_index)
    assert jira_sub_index is not None
    assert project_sub_index is not None


# TODO: Static return and check for actual values
def test_get_all_sheet_ids(smartsheet_client, minutes):
    with pytest.raises(TypeError):
        get_all_sheet_ids("smartsheet_client", minutes)
    with pytest.raises(TypeError):
        get_all_sheet_ids(smartsheet_client, "minutes")
    with pytest.raises(ValueError):
        get_all_sheet_ids(smartsheet_client, -1)
    sheet_ids = get_all_sheet_ids(smartsheet_client, minutes)
    assert sheet_ids is not None


def test_get_secret(env):
    secret_name = get_secret_name(env)
    assert secret_name == "staging/smartsheet-data-sync/svc-api-token"
    retrieved_secret = get_secret(secret_name)
    assert retrieved_secret == os.environ["SMARTSHEET_ACCESS_TOKEN"]


def test_get_secret_name(env):
    with pytest.raises(TypeError):
        actual = get_secret_name(1)
    with pytest.raises(ValueError):
        actual = get_secret_name('')

    expected = "staging/smartsheet-data-sync/svc-api-token"
    actual = get_secret_name(env)
    assert expected == actual
