import json

import pytest
import smartsheet
import uuid_module.helper as helper
import uuid_module.smartsheet_api as smartsheet_api
import uuid_module.variables as app_vars

_, cwd = helper.get_local_paths()


@pytest.fixture(scope="module")
def workspace_fixture():
    with open(cwd + '/dev_workspaces.json') as f:
        dev_workspace = json.load(f)
        dev_workspace = smartsheet.models.Workspace(dev_workspace)
    ws_ids = [8262165481187204, 943816086710148, 5447415714080644,
              3195615900395396, 7699215527765892, 2069715993552772,
              6573315620923268, 4321515807238020]
    return dev_workspace, ws_ids


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col_fixture(sheet_json):
        sheet_json['columns'][20]['title'] = "Not UUID"
        no_uuid_col = smartsheet.models.Sheet(sheet_json)
        return no_uuid_col

    def no_summary_col_fixture(sheet_json):
        sheet_json['columns'][4]['name'] = "Not Summary"
        no_summary_col = smartsheet.models.Sheet(sheet_json)
        return no_summary_col

    sheet = smartsheet.models.Sheet(sheet_json)
    col_map = helper.get_column_map(sheet)
    sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
    sheet_no_summary_col = no_summary_col_fixture(sheet_json)
    return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture(scope="module")
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    linked_row = smartsheet.models.Row(row_json)

    with open(cwd + '/dev_program_plan_unlinked_row.json') as f:
        row_json = json.load(f)
    unlinked_row = smartsheet.models.Row(row_json)
    return linked_row, unlinked_row


@pytest.fixture
def setup_new_sheet(sheet_fixture):
    sheet, _, _, _ = sheet_fixture

    def clear_sheet(sheet_id):
        temp_sheet = smartsheet_api.get_sheet(sheet_id)
        assert isinstance(temp_sheet, smartsheet.models.Sheet)
        delete_rows = []
        for row in temp_sheet.rows:
            delete_rows.append(row.id)
        if not delete_rows:
            return temp_sheet
        if len(delete_rows > 125):
            chunked_rows = helper.chunks(delete_rows, 125)
            for i in chunked_rows:
                try:
                    response = smartsheet_client.\
                        Sheets.delete_rows(temp_sheet.id, i,
                                           ignore_rows_not_found=True)
                except Exception as result:
                    print(result)
        else:
            try:
                response = smartsheet_client.\
                    Sheets.delete_rows(temp_sheet.id, delete_rows,
                                       ignore_rows_not_found=True)
            except Exception as result:
                print(result)
        assert response.message == "SUCCESS"
        return temp_sheet

    response = smartsheet_client.Sheets.copy_sheet(
        sheet.id,
        smartsheet.models.ContainerDestination({
            'destination_type': 'folder',
            'destination_id': 4587159811319684,
            'new_name': 'Program Integration Tests'
        })
    )
    assert response.message == "SUCCESS"
    assert isinstance(response.result, smartsheet.models.Sheet)
    temp_sheet = response.result
    assert isinstance(temp_sheet.id, int)
    temp_sheet = clear_sheet(temp_sheet.id)
    col_map = helper.get_column_map(temp_sheet)
    return temp_sheet, col_map


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_init():
    set_init_fixture()


def test_adding_rows_0(setup_new_sheet):
    sheet, col_map = setup_new_sheet
    rows_to_add = []
    i = 1
    while(i <= 123):
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        value = str("Added less than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Tasks"],
            'value': value
        })
        rows_to_add.append(new_row)
        i += 1
    result = smartsheet_api.write_rows_to_sheet(rows_to_add,
                                                sheet, write_method="add")
    assert result.message == "SUCCESS"
    assert result.result_code == 0

    result = smartsheet_client.Sheets.delete_sheet(sheet.id)
    assert result.message == "SUCCESS"
    assert result.result_code == 0


def test_adding_rows_1(setup_new_sheet):
    sheet, col_map = setup_new_sheet
    rows_to_add = []
    i = 1
    while(i <= 500):
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        value = str("Add more than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Tasks"],
            'value': value
        })
        rows_to_add.append(new_row)
        i += 1
    result = smartsheet_api.write_rows_to_sheet(rows_to_add,
                                                sheet, write_method="add")
    assert result.message == "SUCCESS"
    assert result.result_code == 0

    result = smartsheet_client.Sheets.delete_sheet(sheet.id)
    assert result.message == "SUCCESS"
    assert result.result_code == 0


def test_updating_rows_0(setup_new_sheet):
    sheet, col_map = setup_new_sheet
    rows_to_add = []
    i = 1
    while(i <= 123):
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        value = str("Add more than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Tasks"],
            'value': value
        })
        rows_to_add.append(new_row)
        i += 1
    result = smartsheet_api.write_rows_to_sheet(rows_to_add,
                                                sheet, write_method="add")
    assert result.message == "SUCCESS"
    assert result.result_code == 0

    sheet_1 = smartsheet_api.get_sheet(sheet.id)
    assert isinstance(sheet_1, smartsheet.models.Sheet)
    assert sheet.id == sheet_1.id
    assert len(sheet_1.rows) == 123

    rows_to_update = []
    i = 1
    for row in sheet_1.rows:
        new_row = smartsheet.models.Row()
        new_row.id = row.id
        value = str("Update less than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Description"],
            'value': value
        })
        rows_to_update.append(new_row)
        i += 1
    result = smartsheet_api.\
        write_rows_to_sheet(rows_to_update, sheet, write_method="update")
    assert result.message == "SUCCESS"
    assert result.result_code == 0

    result = smartsheet_client.Sheets.delete_sheet(sheet.id)
    assert result.message == "SUCCESS"
    assert result.result_code == 0


def test_updating_rows_1(setup_new_sheet):
    sheet, col_map = setup_new_sheet
    rows_to_add = []
    i = 1
    while(i <= 500):
        new_row = smartsheet.models.Row()
        new_row.to_bottom = True
        value = str("Add more than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Tasks"],
            'value': value
        })
        rows_to_add.append(new_row)
        i += 1
    result = smartsheet_api.write_rows_to_sheet(rows_to_add,
                                                sheet, write_method="add")
    assert result.message == "SUCCESS"
    assert result.result_code == 0

    sheet_1 = smartsheet_api.get_sheet(sheet.id)
    assert isinstance(sheet_1, smartsheet.models.Sheet)
    assert sheet.id == sheet_1.id
    assert len(sheet_1.rows) == 500

    rows_to_update = []
    i = 1
    for row in sheet_1.rows:
        new_row = smartsheet.models.Row()
        new_row.id = row.id
        value = str("Update more than 125 rows. Row {}").format(i)
        new_row.cells.append({
            'column_id': col_map["Comments"],
            'value': value
        })
        rows_to_update.append(new_row)
        i += 1
    result = smartsheet_api.\
        write_rows_to_sheet(rows_to_update, sheet, write_method="update")

    assert result.message == "SUCCESS"
    assert result.result_code == 0

    result = smartsheet_client.Sheets.delete_sheet(sheet.id)
    assert result.message == "SUCCESS"
    assert result.result_code == 0


def test_get_workspace_0(workspace_fixture):
    workspace, _ = workspace_fixture
    response_0 = smartsheet_api.get_workspace(app_vars.dev_workspace_id[0])
    assert response_0.id == workspace.id


def test_get_workspace_1(workspace_fixture):
    workspace, _ = workspace_fixture
    workspaces = [workspace, workspace]
    workspace_ids = [app_vars.dev_workspace_id[0],
                     app_vars.dev_workspace_id[0]]
    response_0 = smartsheet_api.get_workspace(workspace_ids)
    assert isinstance(response_0, list)
    for res in response_0:
        assert isinstance(res, smartsheet.models.Workspace)
        for ws in workspaces:
            assert res.id == ws.id


def test_get_sheet_0(sheet_fixture):
    sheet, col_map, _, _ = sheet_fixture
    response_0 = smartsheet_api.get_sheet(sheet.id)
    assert isinstance(response_0, smartsheet.models.Sheet)
    assert response_0.id == sheet.id
    response_col_map = helper.get_column_map(response_0)
    for col in col_map:
        assert col in response_col_map.keys()


def test_get_row_0():
    response_0 = smartsheet_api.get_sheet(app_vars.dev_jira_idx_sheet)
    for row in response_0.rows:
        if row.row_number <= 10:
            response = smartsheet_api.get_row(response_0.id, row.id)
            assert isinstance(response, smartsheet.models.Row)
            assert response.row_number <= 10
