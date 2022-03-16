import json
from unittest.mock import patch

import pytest
import smartsheet
import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars

_, cwd = helper.get_local_paths()


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
    rows_to_write = [row]
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet("rows_to_write", sheet)
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet(rows_to_write, "sheet")
    with pytest.raises(TypeError):
        smartsheet_api.write_rows_to_sheet(rows_to_write, sheet,
                                           write_method=1337)
    with pytest.raises(ValueError):
        smartsheet_api.write_rows_to_sheet(rows_to_write, sheet,
                                           write_method="Add")
    with pytest.raises(ValueError):
        smartsheet_api.write_rows_to_sheet([], sheet)


def test_write_rows_to_sheet_1(row, sheet):
    rows_to_write = [row]

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet)
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_write_rows_to_sheet_2(row, sheet):
    rows_to_write = [row]

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet.id)
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_write_rows_to_sheet_3(row, sheet):
    i = 0
    rows_to_write = []
    while i <= 150:
        rows_to_write.append(row)
        i += 1

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet, write_method="add")
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_write_rows_to_sheet_4(row, sheet):
    rows_to_write = [row]

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet, write_method="update")
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_write_rows_to_sheet_5(row, sheet):
    i = 0
    rows_to_write = []
    while i <= 150:
        rows_to_write.append(row)
        i += 1

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value={"result": {"statusCode": 200}})
    def test_0(mock_0):
        response = smartsheet_api.write_rows_to_sheet(
            rows_to_write, sheet, write_method="update")
        return response
    response = test_0()
    assert response['result']['statusCode'] == 200


def test_get_workspace_0():
    with pytest.raises(TypeError):
        smartsheet_api.get_workspace("workspace_id")
    with pytest.raises(ValueError):
        smartsheet_api.get_workspace([])


def test_get_workspace_1(workspace_fixture):
    workspace, _ = workspace_fixture

    @patch("uuid_module.smartsheet_api.get_workspace", return_value=workspace)
    def test_0(mock_0):
        response = smartsheet_api.get_workspace(
            workspace_id=app_vars.dev_workspace_id[0])
        return response
    response_0 = test_0()
    assert response_0 == workspace


def test_get_workspace_2(workspace_fixture):
    _, workspaces = workspace_fixture

    @patch("uuid_module.smartsheet_api.get_workspace", return_value=workspaces)
    def test_1(mock_0):
        mock_workspaces = [app_vars.dev_workspace_id[0],
                           app_vars.dev_workspace_id[0]]
        response = smartsheet_api.get_workspace(workspace_id=mock_workspaces)
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
        response = smartsheet_api.get_sheet(
            sheet.id, minutes=app_vars.dev_minutes)
        return response
    response = test_0()
    assert response == sheet


def test_get_sheet_2(sheet):
    import uuid_module.smartsheet_api as smartsheet_api

    @patch("uuid_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0):
        response = smartsheet_api.get_sheet(sheet.id, minutes=5)
        return response
    response = test_0()
    assert response == sheet


def test_get_sheet_3(sheet):
    import uuid_module.smartsheet_api as smartsheet_api

    @patch("uuid_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0):
        response = smartsheet_api.get_sheet(sheet.id, minutes=0)
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
