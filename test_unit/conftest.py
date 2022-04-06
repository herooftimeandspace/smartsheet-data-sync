import json
import logging

from freezegun import freeze_time
import pytest
import smartsheet
import uuid_module.variables as app_vars
import uuid_module.helper as helper
from unittest.mock import patch

logger = logging.getLogger(__name__)
_, cwd = helper.get_local_paths()


@pytest.fixture(scope="module")
def workspace_fixture():
    with open(cwd + '/dev_workspaces.json') as f:
        dev_workspace = json.load(f)
        dev_workspace = smartsheet.models.Workspace(dev_workspace)
    ws_ids = []
    for folder in dev_workspace.folders:
        for sheet in folder.sheets:
            ws_ids.append(sheet.id)
    return dev_workspace, ws_ids


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col_fixture(sheet_json):
        sheet_json['columns'][28]['title'] = "Not UUID"
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
def index_sheet_fixture():
    import uuid_module.get_data as get_data
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        index_sheet = json.load(f)
        index_sheet = smartsheet.models.Sheet(index_sheet)

    @patch("uuid_module.smartsheet_api.get_sheet",
           return_value=index_sheet)
    def load_jira_index_fixture(mock_0):
        jira_index_sheet, jira_index_col_map, jira_index_rows \
            = get_data.load_jira_index(index_sheet.id)
        return jira_index_sheet, jira_index_col_map, jira_index_rows

    jira_index_sheet, jira_index_col_map, jira_index_rows \
        = load_jira_index_fixture()
    with open(cwd + '/dev_jira_index_row.json') as f:
        row_json = json.load(f)
        row = smartsheet.models.Row(row_json)
    return jira_index_sheet, jira_index_col_map, jira_index_rows, row


@pytest.fixture(scope="module")
def push_tickets_sheet_fixture():
    with open(cwd + '/dev_push_jira_tickets_sheet.json') as f:
        push_tickets_sheet = json.load(f)
        push_tickets_sheet = smartsheet.models.Sheet(push_tickets_sheet)
    col_map = helper.get_column_map(push_tickets_sheet)
    return push_tickets_sheet, col_map


@pytest.fixture(scope="module")
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    linked_row = smartsheet.models.Row(row_json)

    with open(cwd + '/dev_program_plan_unlinked_row.json') as f:
        row_json = json.load(f)
    unlinked_row = smartsheet.models.Row(row_json)
    return linked_row, unlinked_row


@pytest.fixture(scope="module")
def cell_fixture():
    with open(cwd + '/dev_cell_basic.json') as f:
        basic_json = json.load(f)
    basic_cell = smartsheet.models.Cell(basic_json)
    with open(cwd + '/dev_cell_with_url_and_incoming_link.json') as f:
        url_json = json.load(f)
    url_cell = smartsheet.models.Cell(url_json)
    incoming_link = url_cell

    with open(cwd + '/dev_cell_with_formula.json') as f:
        formula_json = json.load(f)
    formula_cell = smartsheet.models.Cell(formula_json)
    with open(cwd + '/dev_cell_with_url_and_outgoing_link.json') as f:
        outgoing_json = json.load(f)
    outgoing_link = smartsheet.models.Cell(outgoing_json)
    with open(cwd + '/dev_cell_with_url_and_broken_link.json') as f:
        broken_json = json.load(f)
    broken_link = smartsheet.models.Cell(broken_json)
    return basic_cell, url_cell, formula_cell, incoming_link, outgoing_link, \
        broken_link


@pytest.fixture(scope="module")
def env_fixture():
    return "--dev"


@pytest.fixture
@freeze_time("2021-11-18 21:23:54")
# TODO: Static return and check for actual values
def project_indexes(sheet_fixture):
    import app.config as config
    import uuid_module.get_data as get_data
    sheet, _, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data([sheet],
                                                   app_vars.sheet_columns,
                                                   config.minutes)
    _, sub_index = get_data.get_sub_indexes(project_uuid_index)
    return project_uuid_index, sub_index


@pytest.fixture(scope="session")
def set_init_fixture():
    import app.config as config
    config.init(["--dev"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client
    return smartsheet_client
