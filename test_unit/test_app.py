from unittest.mock import patch

import pytest
import smartsheet
import data_module.helper as helper

_, cwd = helper.get_local_paths()


@pytest.fixture
def env_dict():
    value = {}
    value = {'env': '--debug', 'env_msg': "Using Staging variables for "
             "workspace_id and Jira index sheet. Set workspace_id to: "
             "[7802463043512196], index_sheet to: 5786250381682564, and "
             "minutes to: 525600. Pushing tickets to 3312520078354308",
             'workspace_id': [7802463043512196],
             'index_sheet': 5786250381682564,
             'minutes': 525600,
             'push_tickets_sheet': 3312520078354308}
    return value


# @pytest.fixture(scope="module")
# def sheet_fixture():
#     with open(cwd + '/dev_program_plan.json') as f:
#         sheet_json = json.load(f)

#     def no_uuid_col_fixture(sheet_json):
#         sheet_json['columns'][20]['title'] = "Not UUID"
#         no_uuid_col = smartsheet.models.Sheet(sheet_json)
#         return no_uuid_col

#     def no_summary_col_fixture(sheet_json):
#         sheet_json['columns'][4]['name'] = "Not Summary"
#         no_summary_col = smartsheet.models.Sheet(sheet_json)
#         return no_summary_col

#     sheet = smartsheet.models.Sheet(sheet_json)
#     col_map = helper.get_column_map(sheet)
#     sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
#     sheet_no_summary_col = no_summary_col_fixture(sheet_json)
#     return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


# @pytest.fixture
# def workspace_fixture():
#     with open(cwd + '/dev_workspaces.json') as f:
#         workspace_json = json.load(f)

#     workspace = smartsheet.models.Workspace(workspace_json)
#     return workspace


# @pytest.fixture(scope="module")
# def jira_index_sheet_fixture():
#     with open(cwd + '/dev_jira_index_sheet.json') as f:
#         dev_idx_sheet = json.load(f)
#         dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
#     with open(cwd + '/dev_jira_idx_rows.json') as f:
#         dev_idx_rows = json.load(f)
#     dev_idx_col_map = helper.get_column_map(dev_idx_sheet)
#     return dev_idx_sheet, dev_idx_col_map, dev_idx_rows


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


def test_full_jira_sync_0():
    import app.app as app
    with pytest.raises(TypeError):
        app.full_jira_sync("minutes")
    with pytest.raises(ValueError):
        app.full_jira_sync(-1337)
    assert app.app_vars.sheet_columns == ["UUID", "Tasks", "Description",
                                          "Status", "Assigned To",
                                          "Jira Ticket", "Duration", "Start",
                                          "Finish", "Predecessors", "Summary"]


def test_full_jira_sync_1(env_dict):
    import app.app as app
    minutes = env_dict['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.get_all_sheet_ids", return_value=[])
    def test_0(mock_0, mock_1):
        var_0 = app.full_jira_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Sheet index is empty. " in result_0
    assert result_1 is True


def test_full_jira_sync_2(env_dict, sheet_fixture):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    minutes = env_dict['minutes']

    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    @patch("data_module.write_data.write_uuids", return_value=1)
    @patch("data_module.get_data.get_all_row_data",
           return_value={})
    def test_0(mock_0, mock_1, mock_2, mock_3):
        var_0 = app.full_jira_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Project UUID Index is empty. " in result_0
    assert result_1 is True


def test_full_jira_sync_3(env_dict, sheet_fixture):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    minutes = env_dict['minutes']

    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    @patch("data_module.write_data.write_uuids", return_value=1)
    @patch("data_module.get_data.get_sub_indexes",
           return_value=({"UUID": "Value"}, {}))
    def test_0(mock_0, mock_1, mock_2, mock_3):
        var_0 = app.full_jira_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Project sub-index is empty. " in result_0
    assert result_1 is True


def test_full_jira_sync_4(env_dict, sheet_fixture):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    minutes = env_dict['minutes']

    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    @patch("data_module.write_data.write_uuids", return_value=1)
    @patch("data_module.get_data.get_sub_indexes",
           return_value=({}, {"UUID": "Value"}))
    def test_0(mock_0, mock_1, mock_2, mock_3):
        var_0 = app.full_jira_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Jira sub-index is empty. " in result_0
    assert result_1 is True


def test_full_jira_sync_5(env_dict, sheet_fixture, index_sheet_fixture,
                          project_indexes):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    index_sheet, index_col_map, index_rows, _ = index_sheet_fixture
    project_uuid_index, _ = project_indexes
    minutes = env_dict['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.get_data.load_jira_index",
           return_value=(index_sheet, index_col_map, index_rows))
    @patch("data_module.helper.truncate", return_value=10)
    @patch("data_module.get_data.get_all_row_data",
           return_value=project_uuid_index)
    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4, mock_5):
        var_0 = app.full_jira_sync(minutes)
        return var_0

    @patch("data_module.get_data.load_jira_index",
           return_value=(index_sheet, index_col_map, index_rows))
    @patch("data_module.helper.truncate", return_value=45)
    @patch("data_module.get_data.get_all_row_data",
           return_value=project_uuid_index)
    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    def test_1(mock_0, mock_1, mock_2, mock_3, mock_4, mock_5):
        var_0, var_1 = app.full_jira_sync(minutes)
        return var_0, var_1

    result_0 = test_0()
    assert isinstance(result_0, str)
    assert result_0 == "Full Jira sync took: 10 seconds."

    result_1, result_2 = test_1()
    assert isinstance(result_1, str)
    assert isinstance(result_2, str)
    assert result_1 == "Full Jira sync took: 45 seconds."
    assert result_2 == str("Full Jira Sync took 15 seconds longer than the "
                           "interval.")


def test_full_smartsheet_sync_0():
    import app.app as app
    with pytest.raises(TypeError):
        app.full_smartsheet_sync("minutes")
    with pytest.raises(ValueError):
        app.full_smartsheet_sync(-1337)
    assert app.app_vars.sheet_columns == ["UUID", "Tasks", "Description",
                                          "Status", "Assigned To",
                                          "Jira Ticket", "Duration", "Start",
                                          "Finish", "Predecessors", "Summary"]


def test_full_smartsheet_sync_1(env_dict):
    import app.app as app
    environment_variables = env_dict
    minutes = environment_variables['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.get_all_sheet_ids", return_value=[])
    def test_0(mock_0, mock_1):
        var_0 = app.full_smartsheet_sync(minutes)
        return var_0
    result_0 = test_0()

    assert isinstance(result_0, str)
    result_1 = "Sheet index is empty. " in result_0
    assert result_1 is True


def test_full_smartsheet_sync_2(env_dict, sheet_fixture, workspace_fixture):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    workspace, _ = workspace_fixture
    minutes = env_dict['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    @patch("data_module.smartsheet_api.get_workspace",
           return_value=workspace)
    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.helper.truncate", return_value=10)
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4):
        var_0 = app.full_smartsheet_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Full Smartsheet cross-sheet sync took: 10 seconds." in result_0
    assert result_1 is True


def test_full_smartsheet_sync_3(env_dict, sheet_fixture, workspace_fixture):
    import app.app as app
    sheet, _, _, _ = sheet_fixture
    workspace, _ = workspace_fixture
    minutes = env_dict['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.get_data.refresh_source_sheets", return_value=[sheet])
    @patch("data_module.get_data.get_all_sheet_ids",
           return_value=[sheet.id])
    @patch("data_module.smartsheet_api.get_workspace",
           return_value=workspace)
    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.helper.truncate", return_value=180)
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4):
        var_0 = app.full_smartsheet_sync(minutes)
        return var_0

    result_0, result_1 = test_0()
    assert isinstance(result_0, str)
    assert isinstance(result_1, str)
    assert result_0 == "Full Smartsheet cross-sheet sync took: 180 seconds."
    assert result_1 == str("Full Smartsheet cross-sheet sync took 60 seconds "
                           "longer than the interval.")


# def test_full_smartsheet_sync_3(env_dict, sheet_fixture):
#     import app.app as app
#     sheet, _, _, _ = sheet_fixture
#     minutes = env_dict['minutes']
    # result = smartsheet.models.Result()
    # result.message = "SUCCESS"
    # result.result_code = 0

#     @patch("data_module.get_data.refresh_source_sheets",
#            return_value=[sheet])
#     @patch("data_module.smartsheet_api.write_rows_to_sheet",
#            return_value=result)
#     @patch("data_module.helper.truncate", return_value=180)
#     def test_0(mock_0, mock_1, mock_2):
#         var_0, var_1 = app.full_smartsheet_sync(minutes)
#         return var_0, var_1

#     _, result_0 = test_0()
#     assert isinstance(result_0, str)
#     result_1 = "seconds longer than " in result_0
#     assert result_1 is True
