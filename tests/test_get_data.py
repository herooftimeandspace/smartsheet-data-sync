import json
import logging
import os
from unittest.mock import patch

import pytest
import pytz
import smartsheet
from freezegun import freeze_time
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


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


# Type testing. Separate tests needed for integraiton.
@freeze_time("2021-11-18 21:23:54")
def test_refresh_source_sheets(sheet_ids, dev_fixture, sheet_fixture):
    import uuid_module.get_data as get_data
    sheet, _, _, _ = sheet_fixture
    sheet_ids = [sheet.id]
    dev_minutes, _, _ = dev_fixture
    with pytest.raises(TypeError):
        get_data.refresh_source_sheets(sheet_ids, "dev_minutes")
    with pytest.raises(TypeError):
        get_data.refresh_source_sheets(7, dev_minutes)
    with pytest.raises(ValueError):
        get_data.refresh_source_sheets(["One", "Two", "Three"], dev_minutes)
    with pytest.raises(ValueError):
        get_data.refresh_source_sheets(sheet_ids, -1)

    with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
        func_mock.return_value = sheet
        source_sheets = get_data.refresh_source_sheets(sheet_ids, dev_minutes)
        assert isinstance(source_sheets, list)

        source_sheets = get_data.refresh_source_sheets(sheet_ids, 5)
        assert isinstance(source_sheets, list)


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data(sheet_fixture, columns, dev_fixture):
    import uuid_module.get_data as get_data
    dev_minutes, _, _ = dev_fixture
    _, sheet_list, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        get_data.get_all_row_data("source_sheets", columns, dev_minutes)
    with pytest.raises(TypeError):
        get_data.get_all_row_data(sheet_list, "columns", dev_minutes)
    with pytest.raises(TypeError):
        get_data.get_all_row_data(sheet_list, columns, "dev_minutes")
    with pytest.raises(ValueError):
        get_data.get_all_row_data(sheet_list, columns, -1)

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
    import uuid_module.get_data as get_data
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
        get_data.get_blank_uuids("source_sheets")
    blank_uuids = get_data.get_blank_uuids(sheet_list)
    # with open(cwd + '/blank_uuids.txt') as f:
    #     print(f)
    assert blank_uuids is not None
    no_uuids = get_data.get_blank_uuids([])
    assert no_uuids is None


# TODO: Static return and check for actual values
def test_load_jira_index(jira_index_sheet_fixture):
    import uuid_module.get_data as get_data
    jira_idx_sheet, jira_idx_col_map, jira_idx_rows = jira_index_sheet_fixture
    jira_index_id = jira_idx_sheet.id
    with pytest.raises(TypeError):
        get_data.load_jira_index("index_sheet")
    with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
        func_mock.return_value = jira_idx_sheet
        dev_idx_sheet, dev_idx_col_map, \
            dev_idx_rows = get_data.load_jira_index(
                jira_index_id)

        assert isinstance(dev_idx_sheet, smartsheet.models.sheet.Sheet)
        assert isinstance(dev_idx_rows, dict)
        assert isinstance(dev_idx_col_map, dict)
        assert dev_idx_sheet.id == jira_idx_sheet.id
        # assert dev_idx_sheet == jira_idx_sheet
        assert dev_idx_col_map == jira_idx_col_map
        # assert len(dev_idx_rows) == len(jira_idx_rows)


# TODO: Static return and check for actual values
@freeze_time("2021-11-18 21:23:54")
def test_get_sub_indexes(sheet_fixture, columns):
    import uuid_module.get_data as get_data
    with pytest.raises(TypeError):
        get_data.get_sub_indexes("project_data")
    _, sheet_list, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data(sheet_list, columns, 65)
    jira_sub_index, project_sub_index = get_data.get_sub_indexes(
        project_uuid_index)
    assert jira_sub_index is not None
    assert project_sub_index is not None


# TODO: Static return and check for actual values
def test_get_all_sheet_ids(dev_fixture, workspace_fixture):
    import uuid_module.get_data as get_data
    set_init_fixture()
    dev_minutes, dev_workspace_id, dev_jira_idx_sheet = dev_fixture
    workspace, ws_ids = workspace_fixture
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids("dev_minutes",
                                   dev_workspace_id, dev_jira_idx_sheet)
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids(dev_minutes, "dev_workspace_id",
                                   dev_jira_idx_sheet)
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids(dev_minutes, dev_workspace_id,
                                   "dev_jira_idx_sheet")
    with pytest.raises(ValueError):
        get_data.get_all_sheet_ids(-1337, dev_workspace_id, dev_jira_idx_sheet)
    with patch('uuid_module.smartsheet_api.get_workspace') as func_mock:
        func_mock.return_value = workspace
        sheet_ids = get_data.get_all_sheet_ids(
            dev_minutes, dev_workspace_id, dev_jira_idx_sheet)
        for id in sheet_ids:
            assert id in ws_ids
        assert 5786250381682564 not in ws_ids


# TODO: Failing pynguin test
# Automatically generated by Pynguin.
# import uuid_module.get_data as module_0


# def test_case_0():
#     var_0 = module_0.load_jira_index()


# def test_case_1():
#     var_0 = module_0.get_all_sheet_ids()
#     assert var_0 == [775947692599172, 5279547319969668, 3027747506284420,
#         7531347133654916]
#     assert module_0.dev_jira_idx_sheet == 5786250381682564
#     assert module_0.dev_minutes == 525600
#     assert module_0.dev_workspace_id == [2618107878500228]
#     assert module_0.jira_col == 'Jira Ticket'
#     assert module_0.summary_col == 'Summary'
#     assert module_0.uuid_col == 'UUID'
#     assert module_0.logger.filters == []
#     assert module_0.logger.name == 'uuid_module.get_data'
#     assert module_0.logger.level == 0
#     assert module_0.logger.propagate is True
#     assert module_0.logger.handlers == []
#     assert module_0.logger.disabled is False
#     assert module_0.utc is not None


# def test_case_2():
#     bool_0 = True
#     var_0 = module_0.get_all_sheet_ids(bool_0)
#     assert var_0 == []
#     assert module_0.dev_jira_idx_sheet == 5786250381682564
#     assert module_0.dev_minutes == 525600
#     assert module_0.dev_workspace_id == [2618107878500228]
#     assert module_0.jira_col == 'Jira Ticket'
#     assert module_0.summary_col == 'Summary'
#     assert module_0.uuid_col == 'UUID'
#     assert module_0.logger.filters == []
#     assert module_0.logger.name == 'uuid_module.get_data'
#     assert module_0.logger.level == 0
#     assert module_0.logger.propagate is True
#     assert module_0.logger.handlers == []
#     assert module_0.logger.disabled is False
#     assert module_0.utc is not None
#     str_0 = '_\\mUlWQ>d@"|cds_.*Z'
#     var_1 = module_0.load_jira_index()
#     set_0 = {str_0}
#     var_2 = module_0.load_jira_index()
#     float_0 = -28.951
#     list_0 = [set_0, set_0, str_0, float_0]
#     tuple_0 = ()
#     var_3 = module_0.get_all_row_data(float_0, list_0, tuple_0)


# def test_case_3():
#     bool_0 = True
#     var_0 = module_0.get_all_sheet_ids(bool_0)
#     assert var_0 == []
#     assert module_0.dev_jira_idx_sheet == 5786250381682564
#     assert module_0.dev_minutes == 525600
#     assert module_0.dev_workspace_id == [2618107878500228]
#     assert module_0.jira_col == 'Jira Ticket'
#     assert module_0.summary_col == 'Summary'
#     assert module_0.uuid_col == 'UUID'
#     assert module_0.logger.filters == []
#     assert module_0.logger.name == 'uuid_module.get_data'
#     assert module_0.logger.level == 0
#     assert module_0.logger.propagate is True
#     assert module_0.logger.handlers == []
#     assert module_0.logger.disabled is False
#     assert module_0.utc is not None
#     str_0 = 'G9/iyF0hV*uo!&'
#     var_1 = module_0.load_jira_index()
#     set_0 = {str_0}
#     var_2 = module_0.load_jira_index()
#     float_0 = -28.951
#     list_0 = [set_0, set_0, str_0, float_0]
#     tuple_0 = ()
#     var_3 = module_0.get_all_row_data(float_0, list_0, tuple_0)


# def test_case_4():
#     try:
#         bool_0 = False
#         var_0 = module_0.refresh_source_sheets(bool_0)
#     except BaseException:
#         pass


# def test_case_5():
#     try:
#         int_0 = 302
#         list_0 = [int_0]
#         float_0 = 10.0
#         var_0 = module_0.get_all_row_data(list_0, int_0, float_0)
#     except BaseException:
#         pass


# def test_case_6():
#     try:
#         bytes_0 = b'`\x14\xca\xf4Yi\x14\xee\xb7O:\xa8\x10\x1e\x8aKN\xb4'
#         int_0 = -1106
#         int_1 = -3049
#         var_0 = module_0.get_all_row_data(bytes_0, int_0, int_1)
#     except BaseException:
#         pass


# def test_case_7():
#     try:
#         str_0 = '7\'\'6"qd'
#         bool_0 = True
#         list_0 = [bool_0, str_0]
#         var_0 = module_0.get_blank_uuids(list_0)
#     except BaseException:
#         pass


# def test_case_8():
#     try:
#         str_0 = 'Parent Length: {}'
#         var_0 = module_0.get_blank_uuids(str_0)
#     except BaseException:
#         pass


# def test_case_9():
#     try:
#         dict_0 = None
#         var_0 = module_0.get_all_sheet_ids()
#         assert var_0 == [775947692599172, 5279547319969668,
#             3027747506284420, 7531347133654916]
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.jira_col == 'Jira Ticket'
#         assert module_0.summary_col == 'Summary'
#         assert module_0.uuid_col == 'UUID'
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.get_data'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.utc is not None
#         var_1 = module_0.load_jira_index(dict_0)
#     except BaseException:
#         pass


# def test_case_10():
#     try:
#         var_0 = module_0.get_all_sheet_ids()
#         assert var_0 == [775947692599172, 5279547319969668,
#             3027747506284420, 7531347133654916]
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.jira_col == 'Jira Ticket'
#         assert module_0.summary_col == 'Summary'
#         assert module_0.uuid_col == 'UUID'
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.get_data'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.utc is not None
#         str_0 = '[nO(KA<c+!()\\Z8+E='
#         var_1 = module_0.get_sub_indexes(str_0)
#     except BaseException:
#         pass


# def test_case_11():
#     try:
#         float_0 = 2280.20976
#         str_0 = None
#         var_0 = module_0.get_all_sheet_ids(float_0, str_0)
#     except BaseException:
#         pass


# def test_case_12():
#     try:
#         bool_0 = False
#         dict_0 = {bool_0: bool_0, bool_0: bool_0, bool_0: bool_0, bool_0:
#             bool_0}
#         bool_1 = False
#         var_0 = module_0.get_sub_indexes(dict_0)
#         assert var_0 is None
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.jira_col == 'Jira Ticket'
#         assert module_0.summary_col == 'Summary'
#         assert module_0.uuid_col == 'UUID'
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.get_data'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.utc is not None
#         var_1 = module_0.get_blank_uuids(bool_1)
#     except BaseException:
#         pass


# def test_case_13():
#     try:
#         bool_0 = True
#         var_0 = module_0.get_all_sheet_ids(bool_0)
#         assert var_0 == []
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.jira_col == 'Jira Ticket'
#         assert module_0.summary_col == 'Summary'
#         assert module_0.uuid_col == 'UUID'
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.get_data'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.utc is not None
#         var_1 = module_0.load_jira_index()
#         float_0 = -28.951
#         list_0 = [bool_0, var_0, float_0]
#         var_2 = module_0.refresh_source_sheets(list_0)
#     except BaseException:
#         pass
