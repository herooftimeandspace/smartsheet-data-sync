import json
import os
from botocore.exceptions import NoCredentialsError
import pytest
import smartsheet
from unittest.mock import patch, Mock
import uuid_module.smartsheet_api as smartsheet_api
from uuid_module.variables import dev_minutes, dev_workspace_id
from uuid_module.helper import get_secret, get_secret_name
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


def test_set_access_token():
    with pytest.raises(NoCredentialsError):
        secret_name = get_secret_name()
        os.environ["AWS_ACCESS_KEY_ID"] = ""
        os.environ["AWS_SECRET_ACCESS_KEY"] = ""
        os.environ["AWS_SESSION_TOKEN"] = ""
        os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)


def test_write_rows_to_sheet(monkeypatch, row, sheet):
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

    with patch("uuid_module.smartsheet_api.write_rows_to_sheet") as func_mock:
        func_mock.return_value = {"result": {"statusCode": 200}}
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet)
        assert response['result']['statusCode'] == 200


def test_get_workspace(workspace_fixture, monkeypatch):
    workspace, workspaces = workspace_fixture
    with pytest.raises(TypeError):
        smartsheet_api.get_workspace("workspace_id")
    with patch("uuid_module.smartsheet_api.get_workspace") as func_mock:
        func_mock.return_value = workspace
        response = smartsheet_api.get_workspace(workspace_id=dev_workspace_id)
        assert response == workspace
    with patch("uuid_module.smartsheet_api.get_workspace") as func_mock:
        func_mock.return_value = workspaces
        dev_workspace_id.append(dev_workspace_id[0])
        response = smartsheet_api.get_workspace(workspace_id=dev_workspace_id)
        assert response == workspaces


def test_get_sheet(sheet):
    sheet_id = sheet.id
    with pytest.raises(TypeError):
        smartsheet_api.get_sheet("sheet_id", minutes=dev_minutes)
    with pytest.raises(TypeError):
        smartsheet_api.get_sheet(sheet_id, minutes="dev_minutes")
    with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
        func_mock.return_value = sheet
        response = smartsheet_api.get_sheet(sheet_id, minutes=dev_minutes)
        assert response == sheet


def test_get_row(sheet, row):
    sheet_id = sheet.id
    row_id = row.id
    with pytest.raises(TypeError):
        smartsheet_api.get_row("sheet_id", row_id)
    with pytest.raises(TypeError):
        smartsheet_api.get_row(sheet_id, "row_id")
    with patch("uuid_module.smartsheet_api.get_row") as func_mock:
        func_mock.return_value = row
        response = smartsheet_api.get_row(sheet_id, row_id)
        assert response == row
