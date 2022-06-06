import datetime
import json

import pytest
import smartsheet
import app.variables as app_vars
import data_module.helper as helper
from freezegun import freeze_time

true = True
false = False
null = None

_, cwd = helper.get_local_paths()

# @pytest.fixture
# def col_map():
#     col_map = {
#         'Actual Inject LoE': 482457047852932,
#         'Actual Planned LoE': 4986056675223428,
#         'Allocation %': 5760112861177732,
#         'Assigned To': 1256513233807236,
#         'Change': 763932024563588,
#         'Child Projects': 4141631745091460,
#         'Comments': 8011912674862980,
#         'Confidence': 6111956582066052,
#         'Created': 7660068953974660,
#         'Current Quarter': 8785968860817284,
#         'Description': 2171306908116868,
#         'Duration': 8926706349172612,
#         'Estimated Inject LoE': 2734256861538180,
#         'Estimated LoE': 1608356954695556,
#         'Estimated Planned LoE': 7237856488908676,
#         'Finish': 4634212954335108,
#         'Hierarchy': 8363756395751300,
#         'Initiative': 5267531651934084,
#         'Inject': 5549006628644740,
#         'Issue Type': 4877680976914308,
#         'Jira Sync': 6956381512198020,
#         'Jira Ticket': 6886012768020356,
#         'KTLO': 6817156137543556,
#         'Launch Calendar': 2452781884827524,
#         'Launch Date Row': 1045407001274244,
#         'Level': 7519331465619332,
#         'LoE': 4423106721802116,
#         'Modified': 2030569419761540,
#         'Modified Copy': 6534169047132036,
#         'Next Quarter Task': 200982071142276,
#         'Parent': 6393431558776708,
#         'Parent Issue Type': 633554282538884,
#         'Parent Team': 3578681791670148,
#         'Parent Ticket': 374081349543812,
#         'ParentUUID': 5830481605355396,
#         'Predecessors': 3508313047492484,
#         'Priority': 8082281419040644,
#         'Program': 3015731838248836,
#         'Project Key': 1326881977984900,
#         'Quarter': 2382413140649860,
#         'Quarter Rollup': 4704581698512772,
#         'RowID': 3156469326604164,
#         'Start': 130613326964612,
#         'Status': 3297206814959492,
#         'Summary': 4282369233446788,
#         'Tasks': 7800806442329988,
#         'Team': 6674906535487364,
#         'UUID': 8645231372461956,
#         'Year': 1889831931406212,
#         '← Hide Everything to the Left': 3860156768380804,
#     }
#     return col_map


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
def json_extract_fixture():
    with open(cwd + '/dev_cell_with_formula.json') as f:
        cell_json = json.load(f)
    return cell_json, "formula"


@pytest.fixture
def simple_list():
    return [1, 2, 3, 4, 5, 6]


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_get_cell_data_0(row_fixture, sheet_fixture):
    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    import data_module.helper as helper
    with pytest.raises(TypeError):
        helper.get_cell_data("Row", app_vars.task_col, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_data(row, 1, col_map)
    with pytest.raises(TypeError):
        helper.get_cell_data(row, app_vars.task_col, "col_map")
    with pytest.raises(KeyError):
        keyerror_col_map = {}
        keyerror_col_map["Jira Issue"] = 1337
        helper.get_cell_data(row, app_vars.task_col, keyerror_col_map)
    with pytest.raises(ValueError):
        helper.get_cell_data(row, app_vars.task_col, {})
    with pytest.raises(TypeError):
        k_type_error = {}
        k_type_error[12345] = 12345
        helper.get_cell_data(row, app_vars.task_col, k_type_error)
    with pytest.raises(TypeError):
        v_type_error = {}
        v_type_error["Jira Ticket"] = "12345"
        helper.get_cell_data(row, app_vars.task_col, v_type_error)
    with pytest.raises(ValueError):
        v_value_error = {}
        v_value_error["Jira Ticket"] = -1337
        helper.get_cell_data(row, app_vars.task_col, v_value_error)


def test_get_all_cell_data_1(row_fixture, sheet_fixture, cell_fixture):
    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    test_fixture_cell_data, _, _, _, _, _ = cell_fixture
    test_cell_data = helper.get_cell_data(row, app_vars.uuid_col, col_map)
    assert (test_cell_data.value,
            test_cell_data.column_id,
            test_cell_data.column_type,
            test_cell_data.formula) == (
        test_fixture_cell_data.value,
        test_fixture_cell_data.column_id,
        test_fixture_cell_data.column_type,
        test_fixture_cell_data.formula)


def test_get_column_map_0():
    with pytest.raises(TypeError):
        helper.get_column_map("Sheet")


def test_get_column_map_1(sheet_fixture):
    sheet, col_map, _, _ = sheet_fixture
    result_0 = helper.get_column_map(sheet)
    assert result_0 == col_map
    for k, v in result_0.items():
        assert isinstance(k, str)
        assert isinstance(v, int)


def test_has_cell_link_0(cell_fixture):
    _, _, _, incoming_link, _, _ = cell_fixture
    direction = "In"
    with pytest.raises(TypeError):
        helper.has_cell_link("incoming_link", direction)
    with pytest.raises(TypeError):
        helper.has_cell_link(incoming_link, 7)
    with pytest.raises(TypeError):
        helper.has_cell_link(incoming_link, "In", sheet_id="Sheet ID")
    with pytest.raises(ValueError):
        helper.has_cell_link(incoming_link, "Sideways")


def test_has_cell_link_1(cell_fixture):
    direction = "In"
    _, _, _, incoming_link, _, broken_link = cell_fixture
    assert helper.has_cell_link(incoming_link, direction) == "OK"
    assert helper.has_cell_link(broken_link, direction) == "BROKEN"


def test_has_cell_link_2(sheet_fixture, row_fixture):
    _, col_map, _, _ = sheet_fixture
    linked_row, _ = row_fixture
    jira_cell = helper.get_cell_data(linked_row, "Jira Ticket", col_map)
    cell_link_status = helper.has_cell_link(jira_cell, "In")
    assert cell_link_status == "OK"
    assert str(jira_cell.link_in_from_cell.status) == str(cell_link_status)


# TODO: Swap fixtures for Index Sheet to get OUT links
def test_has_cell_link_3(sheet_fixture, row_fixture):
    _, col_map, _, _ = sheet_fixture
    linked_row, _ = row_fixture
    jira_cell = helper.get_cell_data(linked_row, "Jira Ticket", col_map)
    i = 0
    while i <= (len(jira_cell.links_out_to_cells) - 1):
        cell_link_status = helper.has_cell_link(
            jira_cell, "Out",
            sheet_id=jira_cell.links_out_to_cells[i].sheet_id,
            row_id=jira_cell.links_out_to_cells[i].row_id,
            col_id=jira_cell.links_out_to_cells[i].column_id)
        assert cell_link_status == "OK"
        assert str(jira_cell.links_out_to_cells[i].status) == str(
            cell_link_status)
        i += 1


# TODO: Swap fixtures for Index Sheet to get OUT links
def test_has_cell_link_4(sheet_fixture, row_fixture):
    _, col_map, _, _ = sheet_fixture
    linked_row, _ = row_fixture
    jira_cell = helper.get_cell_data(linked_row, "Jira Ticket", col_map)
    i = 0
    while i <= (len(jira_cell.links_out_to_cells) - 1):
        cell_link_status = helper.has_cell_link(
            jira_cell, "Out")
        assert cell_link_status == "Linked"
        i += 1


def test_has_cell_link_5(sheet_fixture, row_fixture):
    sheet, col_map, _, _ = sheet_fixture
    linked_row, _ = row_fixture
    no_link = helper.get_cell_data(linked_row, "Finish", col_map)
    link_in_status = helper.has_cell_link(no_link, "In")
    link_out_status = helper.has_cell_link(no_link, "Out")
    link_out_with_args = helper.has_cell_link(
        no_link, "Out", sheet_id=sheet.id,
        row_id=linked_row.id,
        col_id=col_map['Finish'])
    assert link_in_status == "Unlinked"
    assert link_out_status == "Unlinked"
    assert link_out_with_args == "Unlinked"


def test_json_extract_0(json_extract_fixture):
    obj, key = json_extract_fixture
    with pytest.raises(TypeError):
        helper.json_extract("String", key)
    with pytest.raises(TypeError):
        helper.json_extract(obj, -1)
    with pytest.raises(ValueError):
        helper.json_extract({}, key)
    with pytest.raises(ValueError):
        helper.json_extract(obj, "")


def test_json_extract_1(json_extract_fixture):
    obj, key = json_extract_fixture
    assert helper.json_extract(obj, key) == [
        "=IFERROR(PARENT(UUID@row), \"\")"]


def test_truncate_0():
    with pytest.raises(TypeError):
        helper.truncate("Benny's Adventure Team", 4)
    with pytest.raises(TypeError):
        helper.truncate(3.1337, "decimals")
    with pytest.raises(ValueError):
        helper.truncate(3.1337, -1)
    assert helper.truncate(3.1415, 2) == 3.14


@freeze_time("2012-01-14 12:13:00")
def test_get_timestamp_0():
    with pytest.raises(TypeError):
        helper.get_timestamp("number")
    with pytest.raises(ValueError):
        helper.get_timestamp(-5)


@freeze_time("2012-01-14 12:13:00")
def test_get_timestamp_1():
    modified_since, modified_since_iso = helper.get_timestamp(3)
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14, 12, 13, 0)
    assert modified_since == datetime.datetime(
        2012, 1, 14, 12, 10, 00)  # "2012-01-14T12:10:00"
    assert modified_since_iso == datetime.datetime(
        2012, 1, 14, 12, 10, 00).isoformat()  # "2012-01-14T12:10:00"


def test_chunks_0(simple_list):
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


def test_chunks(simple_list):
    for i in helper.chunks(simple_list, 3):
        assert len(i) == 3


def test_get_local_paths():
    root = "/smartsheet-data-sync-gitlab"
    fixtures = "/smartsheet-data-sync-gitlab/test_fixtures"

    result_0, result_1 = helper.get_local_paths()
    assert root in result_0
    assert fixtures in result_1


# Automatically generated by Pynguin.
def test_case_0():
    import data_module.helper as module_0
    int_0 = 1
    var_0 = module_0.get_timestamp(int_0)
    assert len(var_0) == 2
    assert module_0.logger.filters == []
    assert module_0.logger.name == 'data_module.helper'
    assert module_0.logger.level == 0
    assert module_0.logger.propagate is True
    assert module_0.logger.handlers == []
    # assert module_0.logger.disabled is False


# TODO: Failing pynguin tests
# # Automatically generated by Pynguin.
# import pytest
# import data_module.helper as module_0


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
#         var_0 = module_0.get_cell_data(str_0, int_0, int_0)
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
#         assert module_0.logger.name == 'data_module.helper'
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
#         assert module_0.logger.name == 'data_module.helper'
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
#         assert module_0.logger.name == 'data_module.helper'
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
#         assert module_0.logger.name == 'data_module.helper'
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
#         assert module_0.logger.name == 'data_module.helper'
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
