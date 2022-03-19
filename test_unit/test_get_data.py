import json
import logging
from unittest.mock import patch

import pytest
import pytz
import smartsheet
import uuid_module.helper as helper
import uuid_module.variables as app_vars
import uuid_module.get_data as get_data
from freezegun import freeze_time

logger = logging.getLogger(__name__)

utc = pytz.UTC
_, cwd = helper.get_local_paths()


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col(sheet_json):
        sheet_json['columns'][20]['title'] = "Not UUID"
        no_uuid_col = smartsheet.models.Sheet(sheet_json)
        return no_uuid_col

    def no_summary_col(sheet_json):
        sheet_json['columns'][4]['title'] = "Not Summary"
        no_summary_col = smartsheet.models.Sheet(sheet_json)
        return no_summary_col

    sheet = smartsheet.models.Sheet(sheet_json)
    col_map = helper.get_column_map(sheet)
    sheet_no_uuid_col = no_uuid_col(sheet_json)
    sheet_no_summary_col = no_summary_col(sheet_json)
    return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture(scope="module")
def jira_index_sheet_fixture():
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    with open(cwd + '/dev_jira_idx_rows.json') as f:
        dev_idx_rows = json.load(f)
    dev_idx_col_map = helper.get_column_map(dev_idx_sheet)
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
    columns = app_vars.sheet_columns
    return columns


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


# Type testing. Separate tests needed for integraiton.
@freeze_time("2021-11-18 21:23:54")
def test_refresh_source_sheets_0(sheet_ids, sheet_fixture):
    import app.config as config
    sheet, _, _, _ = sheet_fixture
    sheet_ids = [sheet.id]
    with pytest.raises(TypeError):
        get_data.refresh_source_sheets(sheet_ids, "config.minutes")
    with pytest.raises(TypeError):
        get_data.refresh_source_sheets(7, config.minutes)
    with pytest.raises(ValueError):
        get_data.refresh_source_sheets(["One", "Two", "Three"], config.minutes)
    with pytest.raises(ValueError):
        get_data.refresh_source_sheets(sheet_ids, -1)
    with pytest.raises(ValueError):
        get_data.refresh_source_sheets([-1337, 123, 456], config.minutes)
    # with pytest.raises(ValueError):
    #     get_data.refresh_source_sheets([], config.minutes)


@freeze_time("2021-11-18 21:23:54")
def test_refresh_source_sheets_1(sheet_ids, sheet_fixture):
    import app.config as config
    sheet, _, _, _ = sheet_fixture

    @patch("uuid_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0):
        source_sheets = get_data.refresh_source_sheets(sheet_ids,
                                                       config.minutes)
        return source_sheets
    result_0 = test_0()
    result_sheet = result_0[0]
    assert isinstance(result_0, list)
    assert result_sheet.id == sheet.id
    assert result_sheet.name == sheet.name
    assert result_sheet.version == sheet.version
    assert result_sheet.created_at == sheet.created_at
    assert result_sheet.modified_at == sheet.modified_at


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_0(sheet_fixture):
    import app.config as config
    sheet, _, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        get_data.get_all_row_data("source_sheets", app_vars.sheet_columns,
                                  config.minutes)
    with pytest.raises(TypeError):
        get_data.get_all_row_data([sheet], "app_vars.sheet_columns",
                                  config.minutes)
    with pytest.raises(TypeError):
        get_data.get_all_row_data([sheet], app_vars.sheet_columns,
                                  "config.minutes")
    with pytest.raises(ValueError):
        get_data.get_all_row_data([sheet], app_vars.sheet_columns, -1337)
    with pytest.raises(ValueError):
        get_data.get_all_row_data([sheet, "sheet"],
                                  app_vars.sheet_columns, config.minutes)
    with pytest.raises(ValueError):
        get_data.get_all_row_data([sheet],
                                  ["Column One", 1337], config.minutes)


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_1(sheet_fixture):
    import app.config as config
    sheet, _, _, _ = sheet_fixture

    def prep_0():
        with open(cwd + '/dev_all_row_data.json') as f:
            all_row_data = json.load(f)
        return all_row_data

    def test_0():
        result_0 = get_data.get_all_row_data(
            [sheet], app_vars.sheet_columns, config.minutes)
        return result_0

    # TODO: Handle rows without UUID (Program Plan row 77)
    all_row_data = prep_0()
    result_1 = test_0()
    for k in result_1.keys():
        if k is None:
            continue
        else:
            assert k in all_row_data.keys()


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_2():
    import app.config as config

    def test_0():
        result_0 = get_data.get_all_row_data([], app_vars.sheet_columns,
                                             config.minutes)
        return result_0

    result_1 = test_0()
    assert result_1 is None


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_3(sheet_fixture):
    import app.config as config
    _, _, no_uuid, _ = sheet_fixture

    def test_0():
        result_0 = get_data.get_all_row_data(
            [no_uuid], app_vars.sheet_columns, config.minutes)
        return result_0

    result_1 = test_0()
    assert result_1 is None


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_4(sheet_fixture, columns):
    import app.config as config
    _, _, _, no_summary = sheet_fixture

    def test_0():
        result = get_data.get_all_row_data(
            [no_summary], columns, config.minutes)
        return result

    result_0 = test_0()
    assert result_0 is None


@freeze_time("2021-11-18 21:23:54")
def test_get_all_row_data_5(sheet_fixture):
    import app.config as config
    sheet, _, _, _ = sheet_fixture

    @patch("uuid_module.helper.get_cell_data", return_value=None)
    def test_0(mock_0):
        result = get_data.get_all_row_data(
            [sheet], app_vars.sheet_columns, config.minutes)
        return result

    # @patch("uuid_module.helper.get_cell_data", return_value=KeyError)
    # def test_1(mock_0):
    #     result = get_data.get_all_row_data(
    #         [sheet], app_vars.sheet_columns, config.minutes)
    #     return result

    result_0 = test_0()
    assert result_0 is None

    # result_1 = test_1()
    # assert result_1 is None


@freeze_time("2021-11-18 21:23:54")
def test_get_blank_uuids_0():
    with pytest.raises(TypeError):
        get_data.get_blank_uuids("source_sheets")
    with pytest.raises(ValueError):
        get_data.get_blank_uuids(["smartsheet.models.Sheet"])


@freeze_time("2021-11-18 21:23:54")
def test_get_blank_uuids_1(sheet_fixture):
    sheet, _, _, _ = sheet_fixture

    def test_0():
        result = get_data.get_blank_uuids([sheet])
        return result

    def test_1():
        result = get_data.get_blank_uuids([])
        return result

    def test_2(test_0_result):
        for sheet_id_key, values_0 in test_0_result.items():
            assert isinstance(sheet_id_key, int)
            assert isinstance(values_0["row_data"], dict)
            assert isinstance(values_0["sheet_name"], str)
            for row_id, values_1 in values_0["row_data"].items():
                assert isinstance(row_id, int)
                assert isinstance(values_1["column_id"], int)
                assert isinstance(values_1["uuid"], str)
        return True

    result_0 = test_0()
    assert result_0 is not None
    result_1 = test_1()
    assert result_1 is None
    result_2 = test_2(result_0)
    assert result_2 is True
    # with open(cwd + '/blank_uuids.txt') as f:
    #     print(f)


# TODO: Static return and check for actual values
def test_load_jira_index_0():
    with pytest.raises(TypeError):
        get_data.load_jira_index("index_sheet")
    with pytest.raises(ValueError):
        get_data.load_jira_index(1337)

# TODO: Static return and check for actual values


def test_load_jira_index_1(jira_index_sheet_fixture):
    jira_idx_sheet, jira_idx_col_map, _ = jira_index_sheet_fixture

    @patch("uuid_module.smartsheet_api.get_sheet", return_value=jira_idx_sheet)
    def test_0(mock_0):
        sheet, col_map, rows = get_data.load_jira_index(jira_idx_sheet.id)
        return sheet, col_map, rows

    sheet, col_map, rows = test_0()
    assert isinstance(sheet, smartsheet.models.sheet.Sheet)
    assert isinstance(rows, dict)
    assert isinstance(col_map, dict)
    assert sheet.id == jira_idx_sheet.id
    assert sheet.name == jira_idx_sheet.name
    assert sheet == jira_idx_sheet
    assert col_map == jira_idx_col_map
    for col in app_vars.sync_columns:
        assert col in col_map.keys()


# TODO: Static return and check for actual values
@freeze_time("2021-11-18 21:23:54")
def test_get_sub_indexes_0():
    with pytest.raises(TypeError):
        get_data.get_sub_indexes("project_data")
    with pytest.raises(ValueError):
        get_data.get_sub_indexes({})


# TODO: Static return and check for actual values
@freeze_time("2021-11-18 21:23:54")
def test_get_sub_indexes_1(sheet_fixture):
    sheet, _, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data([sheet],
                                                   app_vars.sheet_columns, 65)
    jira_sub_index, project_sub_index = get_data.get_sub_indexes(
        project_uuid_index)
    assert isinstance(jira_sub_index, dict)
    assert isinstance(project_sub_index, dict)
    assert jira_sub_index is not None
    assert project_sub_index is not None


# TODO: Static return and check for actual values
def test_get_all_sheet_ids_0():
    import app.config as config
    set_init_fixture()
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids("config.minutes",
                                   config.workspace_id, config.index_sheet)
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids(config.minutes, "config.workspace_id",
                                   config.index_sheet)
    with pytest.raises(TypeError):
        get_data.get_all_sheet_ids(config.minutes, config.workspace_id,
                                   "config.index_sheet")
    with pytest.raises(ValueError):
        get_data.get_all_sheet_ids(-1337, config.workspace_id,
                                   config.index_sheet)
    with pytest.raises(ValueError):
        get_data.get_all_sheet_ids(config.minutes, [1337,
                                                    "config.workspace_id"],
                                   config.index_sheet)
    with pytest.raises(ValueError):
        get_data.get_all_sheet_ids(config.minutes, [1337, -1337],
                                   config.index_sheet)


def test_get_all_sheet_ids_1(workspace_fixture):
    import app.config as config
    set_init_fixture()
    workspace, ws_ids = workspace_fixture

    @patch('uuid_module.smartsheet_api.get_workspace', return_value=workspace)
    def test_0(mock_0):
        sheet_ids = get_data.get_all_sheet_ids(
            config.minutes, config.workspace_id, config.index_sheet)
        return sheet_ids
    result_0 = test_0()
    for id in result_0:
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
