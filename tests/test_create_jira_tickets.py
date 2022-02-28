import json
import logging
import os
import pytest
import smartsheet


logger = logging.getLogger(__name__)
cwd = os.path.dirname(os.path.abspath(__file__))


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


@pytest.fixture(scope="module")
def index_sheet_fixture():
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    return dev_idx_sheet


@pytest.fixture(scope="module")
def index_col_map_fixture(index_sheet_fixture):
    from uuid_module.helper import get_column_map
    col_map = get_column_map(index_sheet_fixture)
    return col_map


@pytest.fixture(scope="module")
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row, row_json


def test_create_tickets():
    import uuid_module.create_jira_tickets as create_jira_tickets
    with pytest.raises(TypeError):
        create_jira_tickets.create_tickets("smartsheet_client")


def test_refresh_sheets():
    import uuid_module.create_jira_tickets as create_jira_tickets
    with pytest.raises(TypeError):
        create_jira_tickets.refresh_sheets("dev_minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.refresh_sheets(-1337)


def test_form_rows(row_fixture, index_col_map_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    col_map = get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows("row_dict", index_col_map_fixture)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows(row_dict, "index_col_map_fixture")
    with pytest.raises(ValueError):
        empty_row_dict = {}
        create_jira_tickets.form_rows(empty_row_dict, index_col_map_fixture)
    with pytest.raises(ValueError):
        empty_index_col_map = {}
        create_jira_tickets.form_rows(row_dict, empty_index_col_map)

    index_rows_to_add = create_jira_tickets.form_rows(
        row_dict, index_col_map_fixture)
    assert index_rows_to_add


def test_push_jira_tickets_to_sheet(sheet_fixture, index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    sheet_col_map = get_column_map(sheet)
    index_col_map = get_column_map(index_sheet_fixture)

    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            "sheet", sheet_col_map, index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet, "sheet_col_map", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet, sheet_col_map, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet, sheet_col_map, index_sheet_fixture, "index_col_map")


def test_build_row_data(row_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    row, _ = row_fixture
    sheet, _, _, _ = sheet_fixture
    col_map = get_column_map(sheet)

    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data("row", col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data(row, "col_map")

    row_data = create_jira_tickets.build_row_data(row, col_map)
    assert isinstance(row_data, dict)


def test_create_ticket_index(sheet_fixture, index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet1, sheet2, sheet3, sheet4 = sheet_fixture
    source_sheets = [sheet1, sheet2, sheet3, sheet4]
    index_col_map = get_column_map(index_sheet_fixture)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            "sheet_fixture", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet_fixture, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet_fixture, index_sheet_fixture, "index_col_map")

    # ticket_index = create_ticket_index(
    #     source_sheets, index_sheet_fixture, index_col_map)
    # assert isinstance(ticket_index, (dict, smartsheet.models.Sheet))


def test_create_tickets():
    import uuid_module.create_jira_tickets as create_jira_tickets
    with pytest.raises(TypeError):
        create_jira_tickets.create_tickets("dev_minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.create_tickets(-1337)
