from venv import create
import pytest
from unittest.mock import patch, create_autospec
import json
import smartsheet
import os

cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def env_dict():
    value = {}
    value = {'env': '--debug', 'env_msg': "Using Staging variables for "
             "workspace_id and Jira index sheet. Set workspace_id to: "
             "[2618107878500228], index_sheet to: 5786250381682564, and "
             "minutes to: 525600. Pushing tickets to 3312520078354308",
             'workspace_id': [2618107878500228],
             'index_sheet': 5786250381682564,
             'minutes': 525600,
             'push_tickets_sheet': 3312520078354308}
    return value


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


@pytest.fixture()
def one_sheet():
    sheet, _, _, _ = sheet_fixture
    return sheet


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_main():
    import app.app as app
    set_init_fixture()
    result = app.main()
    assert result is True


def test_full_jira_sync_0(env_dict):
    import app.app as app
    vars = env_dict
    minutes = vars['minutes']
    with pytest.raises(TypeError):
        app.full_jira_sync("minutes")
    with pytest.raises(ValueError):
        app.full_jira_sync(-1337)
    # app.full_jira_sync(minutes)
    assert app.sheet_columns == ["UUID", "Tasks", "Description",
                                 "Status", "Assigned To", "Jira Ticket",
                                 "Duration", "Start", "Finish", "Predecessors",
                                 "Summary"]


# @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
#        {"result": {"statusCode": 200}})
# @patch("uuid_module.get_data.get_all_sheet_ids", None)
# def test_full_jira_sync_1(env_dict, sheet_fixture):
#     import app.app as app
#     # sheet, _, _, _ = sheet_fixture
#     environment_variables = env_dict
#     minutes = environment_variables['minutes']
#     var_0 = app.full_jira_sync(minutes)
#     assert isinstance(var_0, str)
#     result = "Sheet index is empty. " in var_0
#     assert result is True


# @patch("uuid_module.get_data.refresh_source_sheets", [one_sheet])
# @patch("uuid_module.get_data.get_all_sheet_ids", [3027747506284420])
# @patch("uuid_module.write_data_write_uuids", 1)
# @patch("uuid_module.get_data.get_all_row_data", (None, None))
# def test_full_jira_sync_2(env_dict):
#     import app.app as app
#     import uuid_module.get_data as get
#     import uuid_module.smartsheet_api as api
#     import uuid_module.write_data as write
#     refresh_source_sheets = create_autospec(
#         get.refresh_source_sheets, return_value=True)
#     get_all_sheet_ids = create_autospec(
#         get.get_all_sheet_ids, return_value=True)
#     write_rows_to_sheet = \
#         create_autospec(write.write_rows_to_sheet, return_value={
#             "result": {"statusCode": 200}})
#     write_uuids = create_autospec(write.write_uuids, return_value=1)
#     get_all_row_data = create_autospec(
#         get.get_all_row_data, return_value=(None, None))
#     environment_variables = env_dict
#     minutes = environment_variables['minutes']
#     var_0 = app.full_jira_sync(minutes)
#     assert isinstance(var_0, str)
#     result = "Project UUID Index is empty. " in var_0
#     assert result is True
