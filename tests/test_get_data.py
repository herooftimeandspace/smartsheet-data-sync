import json
import logging
import os
from unittest.mock import Mock, patch

import pytest
import pytz
import smartsheet
from freezegun import freeze_time
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_sub_indexes,
                                  load_jira_index, refresh_source_sheets)
from uuid_module.helper import get_column_map
from uuid_module.variables import (dev_jira_idx_sheet, dev_minutes,
                                   dev_workspace_id, sheet_columns)

logger = logging.getLogger(__name__)

utc = pytz.UTC
cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col_fixture(sheet_json):
        sheet_json['columns'][20]['name'] = "Not UUID"
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
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    with open(cwd + '/dev_jira_idx_rows.json') as f:
        dev_idx_rows = json.load(f)
    dev_idx_col_map = get_column_map(dev_idx_sheet)
    return dev_idx_sheet, dev_idx_col_map, dev_idx_rows


@pytest.fixture(scope="module")
def workspace_fixture():
    with open(cwd + '/dev_workspaces.json') as f:
        dev_workspace = json.load(f)
        dev_workspace = smartsheet.models.Workspace(dev_workspace)
    ws_ids = [2125936310151044, 7754886088550276, 775947692599172,
              5279547319969668, 3027747506284420, 7531347133654916,
              1901847599441796, 6405447226812292, 4153647413127044,
              8657247040497540]
    return dev_workspace, ws_ids


@pytest.fixture(scope="module")
def row():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    row_list = [row]
    return row, row_list


@pytest.fixture()
def dev_fixture():
    return dev_minutes, dev_workspace_id, dev_jira_idx_sheet


@pytest.fixture
def env():
    return "--debug"


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
def test_refresh_source_sheets(sheet_ids, dev_fixture, sheet_fixture):
    sheet, sheet_list, _, _ = sheet_fixture
    sheet_ids = [sheet.id]
    dev_minutes, _, _ = dev_fixture
    with pytest.raises(TypeError):
        refresh_source_sheets(sheet_ids, "dev_minutes")
    with pytest.raises(TypeError):
        refresh_source_sheets(7, dev_minutes)
    with pytest.raises(ValueError):
        refresh_source_sheets(["One", "Two", "Three"], dev_minutes)
    with pytest.raises(ValueError):
        refresh_source_sheets(sheet_ids, -1)

    with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
        func_mock.return_value = sheet
        source_sheets = refresh_source_sheets(sheet_ids, dev_minutes)
        assert isinstance(source_sheets, list)

        source_sheets = refresh_source_sheets(sheet_ids, 5)
        assert isinstance(source_sheets, list)


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data(sheet_fixture, columns, dev_fixture):
    dev_minutes, _, _ = dev_fixture
    _, sheet_list, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        get_all_row_data("source_sheets", columns, dev_minutes)
    with pytest.raises(TypeError):
        get_all_row_data(sheet_list, "columns", dev_minutes)
    with pytest.raises(TypeError):
        get_all_row_data(sheet_list, columns, "dev_minutes")
    with pytest.raises(ValueError):
        get_all_row_data(sheet_list, columns, -1)

    # with open(cwd + '/dev_all_row_data.json') as f:
    #     row_json = json.load(f)
    #     row_json = dict(row_json)
    # mock_object = Mock()

    # Need to create assertions for data structure and valid return row values
    # row_data = get_all_row_data(sheet_list, columns, dev_fixture)
    # assert row_data == row_json
    # no_sheet_data = get_all_row_data([], columns, dev_fixture)
    # assert no_sheet_data is None


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


# TODO: Static return and check for actual values
def test_load_jira_index(jira_index_sheet_fixture):
    jira_idx_sheet, jira_idx_col_map, jira_idx_rows = jira_index_sheet_fixture
    jira_index_id = jira_idx_sheet.id
    with pytest.raises(TypeError):
        load_jira_index("index_sheet")
    with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
        func_mock.return_value = jira_idx_sheet
        dev_idx_sheet, dev_idx_col_map, dev_idx_rows = load_jira_index(
            jira_index_id)

        assert isinstance(dev_idx_sheet, smartsheet.models.sheet.Sheet)
        assert isinstance(dev_idx_rows, dict)
        assert isinstance(dev_idx_col_map, dict)
        assert dev_idx_sheet.id == jira_idx_sheet.id
        # assert dev_idx_sheet == jira_idx_sheet
        assert dev_idx_col_map == jira_idx_col_map
        assert dev_idx_rows == jira_idx_rows


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
def test_get_all_sheet_ids(dev_fixture, workspace_fixture):
    dev_minutes, dev_workspace_id, dev_jira_idx_sheet = dev_fixture
    workspace, ws_ids = workspace_fixture
    with pytest.raises(TypeError):
        get_all_sheet_ids("dev_minutes",
                          dev_workspace_id, dev_jira_idx_sheet)
    with pytest.raises(TypeError):
        get_all_sheet_ids(dev_minutes, "dev_workspace_id",
                          dev_jira_idx_sheet)
    with pytest.raises(TypeError):
        get_all_sheet_ids(dev_minutes, dev_workspace_id,
                          "dev_jira_idx_sheet")
    with pytest.raises(ValueError):
        get_all_sheet_ids(-1337, dev_workspace_id, dev_jira_idx_sheet)
    with patch('uuid_module.smartsheet_api.get_workspace') as func_mock:
        func_mock.return_value = workspace
        sheet_ids = get_all_sheet_ids(
            dev_minutes, dev_workspace_id, dev_jira_idx_sheet)
        for id in sheet_ids:
            assert id in ws_ids
        assert 5786250381682564 not in ws_ids
