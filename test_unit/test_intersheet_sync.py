from unittest.mock import patch

import pytest
import smartsheet
import data_module.helper as helper
import sync_module.intersheet_sync as sync
import app.variables as app_vars

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


def test_full_smartsheet_sync_0():
    with pytest.raises(TypeError):
        sync.full_smartsheet_sync("minutes")
    with pytest.raises(ValueError):
        sync.full_smartsheet_sync(-1337)
    assert app_vars.sheet_columns == ["UUID", "Tasks", "Description",
                                      "Status", "Assigned To",
                                      "Jira Ticket", "Duration", "Start",
                                      "Finish", "Predecessors", "Summary"]


def test_full_smartsheet_sync_1(env_dict):
    environment_variables = env_dict
    minutes = environment_variables['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.get_all_sheet_ids", return_value=[])
    def test_0(mock_0, mock_1):
        var_0 = sync.full_smartsheet_sync(minutes)
        return var_0
    result_0 = test_0()

    assert isinstance(result_0, str)
    result_1 = "Sheet index is empty. " in result_0
    assert result_1 is True


def test_full_smartsheet_sync_2(env_dict, sheet_fixture, workspace_fixture):
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
        var_0 = sync.full_smartsheet_sync(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Full Smartsheet cross-sheet sync took: 10 seconds." in result_0
    assert result_1 is True


def test_full_smartsheet_sync_3(env_dict, sheet_fixture, workspace_fixture):
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
        var_0 = sync.full_smartsheet_sync(minutes)
        return var_0

    result_0, result_1 = test_0()
    assert isinstance(result_0, str)
    assert isinstance(result_1, str)
    assert result_0 == "Full Smartsheet cross-sheet sync took: 180 seconds."
    assert result_1 == str("Full Smartsheet cross-sheet sync took 60 seconds "
                           "longer than the interval.")


# def test_full_smartsheet_sync_3(env_dict, sheet_fixture):
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
#         var_0, var_1 = sync.full_smartsheet_sync(minutes)
#         return var_0, var_1

#     _, result_0 = test_0()
#     assert isinstance(result_0, str)
#     result_1 = "seconds longer than " in result_0
#     assert result_1 is True
