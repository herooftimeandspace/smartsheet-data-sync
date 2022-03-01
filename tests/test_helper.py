import json
import os

import pytest
import smartsheet
import datetime
from freezegun import freeze_time

true = True
false = False
null = None

cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def sheet():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)
    sheet = smartsheet.models.Sheet(sheet_json)
    return sheet


@pytest.fixture
def row():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


@pytest.fixture
def cell():
    with open(cwd + '/dev_cell_with_url_and_incoming_link.json') as f:
        cell_json = json.load(f)
    cell = smartsheet.models.Cell(cell_json)
    return cell


@pytest.fixture
def col_name():
    col_name = "Tasks"
    return col_name


@pytest.fixture
def col_map():
    col_map = {
        'Actual Inject LoE': 482457047852932,
        'Actual Planned LoE': 4986056675223428,
        'Allocation %': 5760112861177732,
        'Assigned To': 1256513233807236,
        'Change': 763932024563588,
        'Child Projects': 4141631745091460,
        'Comments': 8011912674862980,
        'Confidence': 6111956582066052,
        'Created': 7660068953974660,
        'Current Quarter': 8785968860817284,
        'Description': 2171306908116868,
        'Duration': 8926706349172612,
        'Estimated Inject LoE': 2734256861538180,
        'Estimated LoE': 1608356954695556,
        'Estimated Planned LoE': 7237856488908676,
        'Finish': 4634212954335108,
        'Hierarchy': 8363756395751300,
        'Initiative': 5267531651934084,
        'Inject': 5549006628644740,
        'Issue Type': 4877680976914308,
        'Jira Sync': 6956381512198020,
        'Jira Ticket': 6886012768020356,
        'KTLO': 6817156137543556,
        'Launch Calendar': 2452781884827524,
        'Launch Date Row': 1045407001274244,
        'Level': 7519331465619332,
        'LoE': 4423106721802116,
        'Modified': 2030569419761540,
        'Modified Copy': 6534169047132036,
        'Next Quarter Task': 200982071142276,
        'Parent': 6393431558776708,
        'Parent Issue Type': 633554282538884,
        'Parent Team': 3578681791670148,
        'Parent Ticket': 374081349543812,
        'ParentUUID': 5830481605355396,
        'Predecessors': 3508313047492484,
        'Priority': 8082281419040644,
        'Program': 3015731838248836,
        'Project Key': 1326881977984900,
        'Quarter': 2382413140649860,
        'Quarter Rollup': 4704581698512772,
        'RowID': 3156469326604164,
        'Start': 130613326964612,
        'Status': 3297206814959492,
        'Summary': 4282369233446788,
        'Tasks': 7800806442329988,
        'Team': 6674906535487364,
        'UUID': 8645231372461956,
        'Year': 1889831931406212,
        '← Hide Everything to the Left': 3860156768380804,
    }
    return col_map


@pytest.fixture
def bad_cell():
    bad_cell = {
        "columnId": 752133921468837,
        "columnType": "TEXT_NUMBER",
        "displayValue": "Lumine",
        "formula": "=UUID@row",
        "hyperlink": {
            "reportId": 674477165909395,
            "sheetId": 117648125440672,
            "sightId": 859583955564213,
            "url": "https://genshin.gg"
        },
        "image": {
            "altText": "Benny's favorite food",
            "height": 25,
            "id": "937767591144840",
            "width": 25
        },
        "objectValue": {
            "objectType": "ABSTRACT_DATETIME"
        },
        "overrideValidation": true,
        "strict": true,
        "value": "Lumine"
    }
    bad_cell = smartsheet.models.Cell(bad_cell)
    return bad_cell


@pytest.fixture
def direction():
    return "In"


@pytest.fixture
def number():
    return 3.1415


@pytest.fixture
def decimals():
    return 3


@pytest.fixture
def json_extract_fixture():
    with open(cwd + '/dev_cell_with_formula.json') as f:
        cell_json = json.load(f)
    return cell_json, "formula"


@pytest.fixture
def simple_list():
    return [1, 2, 3, 4, 5, 6]


@pytest.fixture
def env_fixture():
    return "--debug"


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_get_cell_data(row, col_name, col_map):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.get_cell_data("Row", col_name, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_data(row, 1, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_data(row, col_name, "col_map")
    with pytest.raises(KeyError):
        keyerror_col_map = {}
        keyerror_col_map["Jira Issue"] = "JAR-1234"
        helper.get_cell_data(row, col_name, keyerror_col_map)

    with open(cwd + '/dev_cell_basic.json') as f:
        cell_json = json.load(f)
    test_fixture_cell_data = smartsheet.models.Cell(cell_json)
    test_cell_data = helper.get_cell_data(row, col_name, col_map)
    assert (test_cell_data.value,
            test_cell_data.column_id,
            test_cell_data.column_type,
            test_cell_data.formula) == (
        test_fixture_cell_data.value,
        test_fixture_cell_data.column_id,
        test_fixture_cell_data.column_type,
        test_fixture_cell_data.formula)


def test_get_column_map(sheet, col_map):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.get_column_map("Sheet")
    assert helper.get_column_map(sheet) == col_map


def test_has_cell_link(cell, bad_cell, direction):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.has_cell_link("cell", direction)
    with pytest.raises(TypeError):
        helper.has_cell_link(cell, 7)
    with pytest.raises(ValueError):
        helper.has_cell_link(cell, "Sideways")
    assert helper.has_cell_link(cell, direction) == "OK"
    assert helper.has_cell_link(bad_cell, direction) is "Unlinked"
    try:
        helper.has_cell_link(bad_cell, "Out")
    except KeyError as k:
        assert str(k) == str("'Unlinked'")


def test_get_cell_value(row, col_name, col_map):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.get_cell_value("Row", col_name, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_value(row, 1, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_value(row, col_name, "col_map")
    assert helper.get_cell_value(
        row, col_name, col_map) == "Performance Tests"


def test_json_extract(json_extract_fixture):
    import uuid_module.helper as helper
    obj, key = json_extract_fixture
    with pytest.raises(TypeError):
        helper.json_extract("String", -1)
    with pytest.raises(TypeError):
        helper.json_extract(obj, -1)
    assert helper.json_extract(obj, key) == [
        "=IFERROR(PARENT(UUID@row), \"\")"]


def test_truncate(number, decimals):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.truncate("Benny's Adventure Team", 4)
    with pytest.raises(TypeError):
        helper.truncate(number, "decimals")
    with pytest.raises(ValueError):
        helper.truncate(number, -1)
    assert helper.truncate(number, decimals) == 3.141


@freeze_time("2012-01-14 12:13:00")
def test_get_timestamp(decimals):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        helper.get_timestamp("number")
    with pytest.raises(ValueError):
        helper.get_timestamp(-5)
    modified_since, modified_since_iso = helper.get_timestamp(decimals)
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14, 12, 13, 0)
    assert modified_since == datetime.datetime(
        2012, 1, 14, 12, 10, 00)  # "2012-01-14T12:10:00"
    assert modified_since_iso == datetime.datetime(
        2012, 1, 14, 12, 10, 00).isoformat()  # "2012-01-14T12:10:00"


def test_chunks(simple_list, decimals):
    import uuid_module.helper as helper
    with pytest.raises(TypeError):
        for i in helper.chunks("simple_list", 3):
            pass
    with pytest.raises(TypeError):
        for i in helper.chunks(simple_list, "Four"):
            pass
    with pytest.raises(ValueError):
        for i in helper.chunks(simple_list, -1):
            pass
    with pytest.raises(ValueError):
        for i in helper.chunks(simple_list, 0):
            pass
    with pytest.raises(ValueError):
        for i in helper.chunks(simple_list, 10):
            pass
    for i in helper.chunks(simple_list, decimals):
        assert len(i) == 3


# Automatically generated by Pynguin.
def test_case_0():
    import uuid_module.helper as module_0
    int_0 = 1
    var_0 = module_0.get_timestamp(int_0)
    assert len(var_0) == 2
    assert module_0.logger.filters == []
    assert module_0.logger.name == 'uuid_module.helper'
    assert module_0.logger.level == 0
    assert module_0.logger.propagate is True
    assert module_0.logger.handlers == []
    # assert module_0.logger.disabled is False


# TODO: Failing pynguin tests
# # Automatically generated by Pynguin.
# import pytest
# import uuid_module.helper as module_0


# def test_case_0():
#     try:
#         set_0 = set()
#         int_0 = 7
#         var_0 = module_0.get_cell_data(set_0, int_0, set_0)
#     except BaseException:
#         pass


# def test_case_1():
#     try:
#         int_0 = -1241
#         var_0 = module_0.get_column_map(int_0)
#     except BaseException:
#         pass


# def test_case_2():
#     try:
#         str_0 = '{H7r'
#         set_0 = {str_0, str_0, str_0}
#         var_0 = module_0.has_cell_link(str_0, set_0)
#     except BaseException:
#         pass


# def test_case_3():
#     try:
#         str_0 = ''
#         int_0 = -295
#         var_0 = module_0.get_cell_value(str_0, int_0, int_0)
#     except BaseException:
#         pass


# def test_case_4():
#     try:
#         str_0 = '--project-path'
#         int_0 = 1387
#         var_0 = module_0.json_extract(str_0, int_0)
#     except BaseException:
#         pass


# def test_case_5():
#     try:
#         str_0 = 'U$UlE1Hv.N1z(I'
#         var_0 = module_0.truncate(str_0)
#     except BaseException:
#         pass


# def test_case_6():
#     try:
#         var_0 = module_0.get_secret_name()
#         assert var_0 == 'staging/smartsheet-data-sync/svc-api-token'
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.prod_jira_idx_sheet == 5786250381682564
#         assert module_0.prod_minutes == 65
#         assert module_0.prod_workspace_id == [2618107878500228]
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.helper'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.workspace_id == [2618107878500228]
#         assert module_0.index_sheet == 5786250381682564
#         assert module_0.minutes == 525600
#         str_0 = 'gm6V'
#         set_0 = None
#         var_1 = module_0.truncate(str_0, set_0)
#     except BaseException:
#         pass


# def test_case_7():
#     try:
#         complex_0 = None
#         var_0 = module_0.get_timestamp(complex_0)
#     except BaseException:
#         pass


# def test_case_8():
#     try:
#         bool_0 = True
#         var_0 = module_0.get_secret(bool_0)
#     except BaseException:
#         pass


# def test_case_9():
#     try:
#         float_0 = 3586.106
#         var_0 = module_0.get_secret_name(float_0)
#     except BaseException:
#         pass


# def test_case_10():
#     try:
#         float_0 = 1532.8
#         var_0 = module_0.set_env_vars()
#         assert var_0 == ('--project-path',
#             'Using default debug/staging variables for workspace_id and Jira
#               index sheet', [2618107878500228], 5786250381682564, 525600)
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.minutes == 525600
#         var_1 = module_0.truncate(float_0)
#     except BaseException:
#         pass


# def test_case_11():
#     try:
#         str_0 = '8Fc@'
#         var_0 = module_0.get_secret_name(str_0)
#     except BaseException:
#         pass


# def test_case_12():
#     try:
#         var_0 = module_0.get_secret_name()
#         assert var_0 == 'staging/smartsheet-data-sync/svc-api-token'
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.prod_jira_idx_sheet == 5786250381682564
#         assert module_0.prod_minutes == 65
#         assert module_0.prod_workspace_id == [2618107878500228]
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.helper'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.workspace_id == [2618107878500228]
#         assert module_0.index_sheet == 5786250381682564
#         assert module_0.minutes == 525600
#         str_0 = 'jCnVQjDumWF'
#         var_1 = module_0.get_secret(str_0)
#     except BaseException:
#         pass


# def test_case_13():
#     try:
#         bool_0 = False
#         var_0 = module_0.get_timestamp(bool_0)
#     except BaseException:
#         pass


# def test_case_14():
#     try:
#         str_0 = '|Y%X/\r\x0b(\n!'
#         dict_0 = {str_0: str_0, str_0: str_0, str_0: str_0}
#         str_1 = '2sc$9O5i/~E<WEL\x0c '
#         var_0 = module_0.json_extract(dict_0, str_1)
#         assert var_0 == []
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.prod_jira_idx_sheet == 5786250381682564
#         assert module_0.prod_minutes == 65
#         assert module_0.prod_workspace_id == [2618107878500228]
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.helper'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.workspace_id == [2618107878500228]
#         assert module_0.index_sheet == 5786250381682564
#         assert module_0.minutes == 525600
#         var_1 = module_0.get_secret_name()
#         assert var_1 == 'staging/smartsheet-data-sync/svc-api-token'
#         bool_0 = True
#         var_2 = module_0.get_timestamp(bool_0)
#         assert len(var_2) == 2
#         var_3 = module_0.get_secret(str_0)
#         assert var_3 is None
#         int_0 = 1
#         float_0 = 718.1563
#         var_4 = module_0.has_cell_link(float_0, int_0)
#     except BaseException:
#         pass


# def test_case_15():
#     try:
#         str_0 = '|Y%X/\r\x0b(\n!'
#         dict_0 = {str_0: str_0, str_0: str_0, str_0: str_0}
#         str_1 = '2sc$9O5i/~E<WEL\x0c '
#         var_0 = module_0.json_extract(dict_0, str_1)
#         assert var_0 == []
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.prod_jira_idx_sheet == 5786250381682564
#         assert module_0.prod_minutes == 65
#         assert module_0.prod_workspace_id == [2618107878500228]
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.helper'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.workspace_id == [2618107878500228]
#         assert module_0.index_sheet == 5786250381682564
#         assert module_0.minutes == 525600
#         var_1 = module_0.get_secret_name()
#         assert var_1 == 'staging/smartsheet-data-sync/svc-api-token'
#         bool_0 = True
#         var_2 = module_0.get_timestamp(bool_0)
#         assert len(var_2) == 2
#         int_0 = 113
#         var_3 = module_0.json_extract(dict_0, int_0)
#     except BaseException:
#         pass


# def test_case_16():
#     try:
#         float_0 = 10.0
#         int_0 = 7
#         var_0 = module_0.truncate(float_0, int_0)
#         assert var_0 == pytest.approx(10.0, abs=0.01, rel=0.01)
#         assert module_0.dev_jira_idx_sheet == 5786250381682564
#         assert module_0.dev_minutes == 525600
#         assert module_0.dev_workspace_id == [2618107878500228]
#         assert module_0.prod_jira_idx_sheet == 5786250381682564
#         assert module_0.prod_minutes == 65
#         assert module_0.prod_workspace_id == [2618107878500228]
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.helper'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         assert module_0.env == '--project-path'
#         assert module_0.msg == 'Using default debug/staging variables for
#               workspace_id and Jira index sheet'
#         assert module_0.workspace_id == [2618107878500228]
#         assert module_0.index_sheet == 5786250381682564
#         assert module_0.minutes == 525600
#         dict_0 = {}
#         var_1 = module_0.truncate(dict_0)
#     except BaseException:
#         pass
