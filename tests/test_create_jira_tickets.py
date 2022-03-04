import json
import logging
import os
from unittest.mock import patch
from venv import create

import pytest
import smartsheet


logger = logging.getLogger(__name__)
cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def sheet_fixture():
    from uuid_module.helper import get_column_map
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
    col_map = get_column_map(sheet)
    sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
    sheet_no_summary_col = no_summary_col_fixture(sheet_json)
    return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture
def index_sheet_fixture():
    from uuid_module.helper import get_column_map
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    col_map = get_column_map(dev_idx_sheet)
    return dev_idx_sheet, col_map


@pytest.fixture
def patch_functions(index_sheet_fixture, sheet_fixture):
    dev_idx_sheet, _ = index_sheet_fixture
    sheet, _, _, _ = sheet_fixture
    sheet_ids = [3027747506284420, 5279547319969668,
                 775947692599172, 7531347133654916,
                 6405447226812292, 1901847599441796,
                 4153647413127044, 8657247040497540]
    return dev_idx_sheet, [sheet], sheet_ids


@pytest.fixture(scope="module")
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row, row_json


@patch("uuid_module.create_jira_tickets.create_ticket_index",
       return_value={"Row": "Data"})
@patch("uuid_module.smartsheet_api.write_rows_to_sheet",
       return_value="SUCCESS")
@patch("uuid_module.create_jira_tickets.form_rows",
       return_value=['row 1', 'row 2'])
def test_create_tickets_1(mock_create_ticket_index, mock_write_rows_to_sheet,
                          mock_form_rows):
    import uuid_module.create_jira_tickets as create_jira_tickets
    import app.config as config
    result = create_jira_tickets.create_tickets(config.minutes)
    assert result is True


@patch("uuid_module.create_jira_tickets.create_ticket_index", return_value={})
def test_create_tickets_2(mock_create_ticket_index):
    import uuid_module.create_jira_tickets as create_jira_tickets
    import app.config as config
    result = create_jira_tickets.create_tickets(config.minutes)
    assert result is False


def test_refresh_sheets_0():
    import uuid_module.create_jira_tickets as create_jira_tickets
    with pytest.raises(TypeError):
        create_jira_tickets.refresh_sheets("dev_minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.refresh_sheets(-1337)


def test_refresh_sheets_1(sheet_fixture, index_sheet_fixture, patch_functions):
    import uuid_module.create_jira_tickets as create_jira_tickets
    import app.config as config
    sheet, _, _, _ = sheet_fixture
    index_sheet, index_col_map = index_sheet_fixture
    patch_get_all_sheet_ids, patch_refresh_source_sheets, \
        patch_index_sheet_fixture = patch_functions

    @patch("uuid_module.get_data.get_all_sheet_ids",
           return_value=patch_get_all_sheet_ids)
    @patch("uuid_module.get_data.refresh_source_sheets",
           return_value=patch_refresh_source_sheets)
    @patch("uuid_module.smartsheet_api.get_sheet",
           return_value=patch_index_sheet_fixture)
    def test(mock_1, mock_2, mock_3):
        source_sheets, index, col_map = \
            create_jira_tickets.refresh_sheets(config.minutes)
        assert source_sheets == [sheet]
        assert index.id == index_sheet.id
        assert col_map == index_col_map
        return True
    result = test()
    assert result is True


def test_form_rows_0(row_fixture, index_sheet_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows("row_dict", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows(row_dict, "index_col_map")
    with pytest.raises(ValueError):
        empty_row_dict = {}
        create_jira_tickets.form_rows(empty_row_dict, index_col_map)
    with pytest.raises(ValueError):
        empty_index_col_map = {}
        create_jira_tickets.form_rows(row_dict, empty_index_col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0
    copy_0 = row_dict.copy()
    copy_0[row.id]['Jira Ticket'] = "Create"
    copy_0[row.id]['Inject'] = True
    copy_0[row.id]['KTLO'] = True
    rows_to_add_1 = create_jira_tickets.form_rows(
        copy_0, index_col_map)
    assert rows_to_add_1


def test_form_rows_1(row_fixture, index_sheet_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0


def test_form_rows_2(row_fixture, index_sheet_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    row_dict[row.id]['Jira Ticket'] = "Create"
    row_dict[row.id]['Inject'] = True
    row_dict[row.id]['KTLO'] = True
    rows_to_add_1 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert isinstance(rows_to_add_1, list)
    for row in rows_to_add_1:
        assert isinstance(row, smartsheet.models.row.Row)


def test_link_jira_index_to_sheet_0(index_sheet_fixture, sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            "source_sheets", index_sheet, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            source_sheets, "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            source_sheets, index_sheet, "index_col_map")


def test_link_jira_index_to_sheet_1(index_sheet_fixture,
                                    sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    index_sheet, index_col_map = index_sheet_fixture
    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]

    @patch("uuid_module.create_jira_tickets.build_index_sheet_sub_index",
           return_value={})
    def test(mock_0):
        sheets_updated = create_jira_tickets.link_jira_index_to_sheet(
            source_sheets, index_sheet, index_col_map)
        assert sheets_updated == 0
        return True
    result = test()
    assert result is True


def test_build_index_sheet_sub_index(index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    index_sheet, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.build_sheet_sub_index(
            "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sheet_sub_index(
            index_sheet, "index_col_map")
    with pytest.raises(TypeError):
        create_jira_tickets.build_sheet_sub_index(None, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sheet_sub_index(index_sheet, None)


def test_push_jira_tickets_to_sheet(sheet_fixture, index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    from uuid_module.helper import get_column_map
    sheet, sheet_col_map, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture

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
    row, _ = row_fixture
    sheet, col_map, _, _ = sheet_fixture

    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data("row", col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data(row, "col_map")

    row_data = create_jira_tickets.build_row_data(row, col_map)
    assert isinstance(row_data, dict)


def test_create_ticket_index_0(sheet_fixture, index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    sheet1, sheet2, sheet3, sheet4 = sheet_fixture
    source_sheets = [sheet1, sheet2, sheet3, sheet4]
    _, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            "sheet_fixture", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet_fixture, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.link_jira_index_to_sheet(
            sheet_fixture, index_sheet_fixture, "index_col_map")


def test_create_ticket_index_1(sheet_fixture, index_sheet_fixture):
    import uuid_module.create_jira_tickets as create_jira_tickets
    sheet, _, _, _ = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map = index_sheet_fixture

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet", return_value=200)
    def test(mock_0):
        ticket_index = create_jira_tickets.create_ticket_index(
            source_sheets, index_sheet, index_col_map)
        assert isinstance(ticket_index, (dict, smartsheet.models.Sheet))
        return True
    result = test()
    assert result is True


def test_create_tickets_0():
    import uuid_module.create_jira_tickets as create_jira_tickets
    with pytest.raises(TypeError):
        create_jira_tickets.create_tickets("minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.create_tickets(-1337)
