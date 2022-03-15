import json
import os
from unittest.mock import patch

import pytest
import smartsheet
import uuid_module.variables as app_vars
from botocore.exceptions import NoCredentialsError

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
def workspace_fixture():
    with open(cwd + "/dev_workspaces.json") as f:
        workspace_json = json.load(f)
    workspace = smartsheet.models.Workspace(workspace_json)
    workspaces = [workspace, workspace]
    return workspace, workspaces


def test_write_rows_to_sheet_0(row, sheet):
    import uuid_module.smartsheet_api as smartsheet_api
    rows_to_write = [row]
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet("rows_to_write", sheet)
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet(rows_to_write, "sheet")
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet(rows_to_write, sheet,
                                           write_method=["This is a List"])
    with pytest.raises(ValueError):
        smartsheet_api.write_rows_to_sheet([], sheet)


def test_write_rows_to_sheet_1(row, sheet):
    import uuid_module.smartsheet_api as smartsheet_api
    rows_to_write = [row]

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet)
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_get_workspace_0(workspace_fixture):
    import uuid_module.smartsheet_api as smartsheet_api
    workspace, workspaces = workspace_fixture
    with pytest.raises(TypeError):
        smartsheet_api.get_workspace("workspace_id")
    with patch("uuid_module.smartsheet_api.get_workspace") as func_mock:
        func_mock.return_value = workspace
        response = smartsheet_api.get_workspace(app_vars.dev_workspace_id)
        assert response == workspace
    with patch("uuid_module.smartsheet_api.get_workspace") as func_mock:
        func_mock.return_value = workspaces
        app_vars.dev_workspace_id.append(app_vars.dev_workspace_id[0])
        response = smartsheet_api.get_workspace(app_vars.dev_workspace_id)
        assert response == workspaces


def test_get_workspace_1(workspace_fixture):
    import uuid_module.smartsheet_api as smartsheet_api
    workspace, workspaces = workspace_fixture

    @patch("uuid_module.smartsheet_api.get_workspace", return_value=workspace)
    def test_0(mock_0):
        response = smartsheet_api.get_workspace(app_vars.dev_workspace_id)
        return response
    response_0 = test_0()
    assert response_0 == workspace

    @patch("uuid_module.smartsheet_api.get_workspace", return_value=workspaces)
    def test_1(mock_0):
        app_vars.dev_workspace_id.append(app_vars.dev_workspace_id[0])
        response = smartsheet_api.get_workspace(app_vars.dev_workspace_id)
        return response
    response_1 = test_1()
    assert response_1 == workspaces


def test_get_sheet_0(sheet):
    import uuid_module.smartsheet_api as smartsheet_api
    with pytest.raises(TypeError):
        smartsheet_api.get_sheet("sheet_id", app_vars.dev_minutes)
    with pytest.raises(TypeError):
        smartsheet_api.get_sheet(sheet.id, "app_vars.dev_minutes")


def test_get_sheet_1(sheet):
    import uuid_module.smartsheet_api as smartsheet_api

    @patch("uuid_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0):
        response = smartsheet_api.get_sheet(sheet.id, app_vars.dev_minutes)
        return response
    response = test_0()
    assert response == sheet


def test_get_row_0(sheet, row):
    import uuid_module.smartsheet_api as smartsheet_api
    with pytest.raises(TypeError):
        smartsheet_api.get_row("sheet_id", row.id)
    with pytest.raises(TypeError):
        smartsheet_api.get_row(sheet.id, "row_id")


def test_get_row_1(sheet, row):
    import uuid_module.smartsheet_api as smartsheet_api

    @patch("uuid_module.smartsheet_api.get_row", return_value=row)
    def test_0(mock_0):
        response = smartsheet_api.get_row(sheet.id, row.id)
        return response
    response = test_0()
    assert response == row
