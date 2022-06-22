from unittest.mock import patch

import pytest
import smartsheet
import data_module.helper as helper
import uuid_module.uuid as uuid
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


def test_uuid_0():

    with pytest.raises(TypeError):
        uuid.write_uuids_to_sheets("minutes")
    with pytest.raises(ValueError):
        uuid.write_uuids_to_sheets(-1337)
    assert app_vars.sheet_columns == ["UUID", "Tasks", "Description",
                                      "Status", "Assigned To",
                                      "Jira Ticket", "Duration", "Start",
                                      "Finish", "Predecessors", "Summary"]


def test_uuid_1(env_dict):
    minutes = env_dict['minutes']

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.get_all_sheet_ids", return_value=[])
    def test_0(mock_0, mock_1):
        var_0 = uuid.write_uuids_to_sheets(minutes)
        return var_0

    result_0 = test_0()
    assert isinstance(result_0, str)
    result_1 = "Sheet index is empty. " in result_0
    assert result_1 is True


def test_uuid_2(env_dict, sheet_fixture, index_sheet_fixture,
                project_indexes):
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
        var_0 = uuid.write_uuids_to_sheets(minutes)
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
        var_0, var_1 = uuid.write_uuids_to_sheets(minutes)
        return var_0, var_1

    result_0 = test_0()
    assert isinstance(result_0, str)
    assert result_0 == "Writing UUIDs took: 10 seconds."

    result_1, result_2 = test_1()
    assert isinstance(result_1, str)
    assert isinstance(result_2, str)
    assert result_1 == "Writing UUIDs took: 45 seconds."
    assert result_2 == str("Writing UUIDs took 15 seconds longer than the "
                           "interval.")
