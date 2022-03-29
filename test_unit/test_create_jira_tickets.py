import json
import logging
from unittest.mock import patch

import pytest
import smartsheet
import uuid_module.helper as helper
import uuid_module.create_jira_tickets as create_jira_tickets


logger = logging.getLogger(__name__)
_, cwd = helper.get_local_paths()


@pytest.fixture
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


@pytest.fixture
def index_sheet_fixture():
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    col_map = helper.get_column_map(dev_idx_sheet)
    return dev_idx_sheet, col_map


@pytest.fixture(scope="module")
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row, row_json


def test_form_rows_0(row_fixture, index_sheet_fixture, sheet_fixture):
    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = helper.get_column_map(sheet)
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


def test_form_rows_1(row_fixture, index_sheet_fixture, sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = helper.get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0


def test_form_rows_2(row_fixture, index_sheet_fixture, sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = helper.get_column_map(sheet)
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


def test_form_rows_3(row_fixture, index_sheet_fixture, sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture
    col_map = helper.get_column_map(sheet)
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
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


def test_link_jira_index_to_sheet_0(index_sheet_fixture, sheet_fixture):

    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "source_sheets", index_sheet, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet, "index_col_map")


def test_link_jira_index_to_sheet_1(index_sheet_fixture,
                                    sheet_fixture):

    index_sheet, index_col_map = index_sheet_fixture
    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]

    @patch("uuid_module.create_jira_tickets.build_sub_indexes",
           return_value=({}, []))
    def test(mock_0):
        sheets_updated = create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet, index_col_map)
        return sheets_updated
    sheets_updated = test()
    assert sheets_updated == 0


def test_build_sub_indexes_0(index_sheet_fixture):

    index_sheet, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(
            "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(
            index_sheet, "index_col_map")
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(None, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(index_sheet, None)


def test_build_sub_indexes_1(index_sheet_fixture):
    index_sheet, index_col_map = index_sheet_fixture
    sub_index_dict, sub_index_list = \
        create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
    assert isinstance(sub_index_dict, dict)
    assert isinstance(sub_index_list, list)
    assert sub_index_dict is not None
    assert sub_index_list is not None


def test_push_jira_tickets_to_sheet_0(sheet_fixture, index_sheet_fixture):

    sheet, sheet_col_map, _, _ = sheet_fixture
    _, index_col_map = index_sheet_fixture

    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "sheet", sheet_col_map, index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, "sheet_col_map", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, sheet_col_map, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, sheet_col_map, index_sheet_fixture, "index_col_map")


def test_build_row_data_0(row_fixture, sheet_fixture):

    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data("row", col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data(row, "col_map")


def test_build_row_data_1(row_fixture, sheet_fixture):

    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    row_data = create_jira_tickets.build_row_data(row, col_map)
    assert isinstance(row_data, dict)


def test_create_ticket_index_0(sheet_fixture, index_sheet_fixture):

    sheet1, _, _, _ = sheet_fixture
    source_sheets = [sheet1, sheet1, sheet1, sheet1]
    _, index_col_map = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "source_sheets", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet_fixture, "index_col_map")


def test_create_ticket_index_1(sheet_fixture, index_sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map = index_sheet_fixture
    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    def test(mock_0):
        ticket_index = create_jira_tickets.create_ticket_index(
            source_sheets, index_sheet, index_col_map)

        return ticket_index
    ticket_index = test()
    assert isinstance(ticket_index, (dict, smartsheet.models.Sheet))


def test_create_tickets_0():

    with pytest.raises(TypeError):
        create_jira_tickets.create_tickets("minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.create_tickets(-1337)


def test_create_tickets_1():
    import app.config as config
    import uuid_module.create_jira_tickets as jira

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.create_jira_tickets.create_ticket_index",
           return_value={"Row": "Data"})
    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.form_rows",
           return_value=['row 1', 'row 2'])
    def test_0(mock_0, mock_1, mock_2):
        result = jira.create_tickets(config.minutes)
        return result
    result = test_0()
    assert result is True


def test_create_tickets_2():
    import app.config as config

    @patch("uuid_module.create_jira_tickets.create_ticket_index",
           return_value={})
    def test_0(mock_0):
        result = create_jira_tickets.create_tickets(config.minutes)
        return result
    result_0 = test_0()
    assert result_0 is False


def test_copy_uuid_to_index_sheet_0(index_sheet_fixture):
    # TypeError / ValueError
    pass


def test_copy_uuid_to_index_sheet_1(index_sheet_fixture):
    #
    # index_sheet, index_col_map = index_sheet_fixture
    # @patch("uuid_module.create_jira_tickets.build_sheet_sub_inded",
    #    return_value={})
    # def test_0(mock_0):
    # result = copy_uuid_to_index_sheet(index_sheet, index_col_map)
    # assert result is False
    pass


def test_copy_uuid_to_index_sheet_2(index_sheet_fixture):
    #
    # index_sheet, index_col_map = index_sheet_fixture
    # @patch("uuid_module.create_jira_tickets.build_sheet_sub_inded",
    #    return_value={})
    # def test_0(mock_0):
    # result = copy_uuid_to_index_sheet(index_sheet, index_col_map)
    # assert result is True
    pass


# def test_get_push_tickets_sheet(index_sheet_fixture):
#
#     sheet, col_map = index_sheet_fixture

#     def test_0():
#         with patch("uuid_module.smartsheet_api.get_sheet") as func_mock:
#             func_mock.return_value = sheet
#             push_sheet, push_col_map = \
#                 create_jira_tickets.get_push_tickets_sheet()
#             return push_sheet, push_col_map
#     push_sheet, push_col_map = test_0()
#     assert sheet.id == push_sheet.id
#     assert col_map['Tasks'] == push_col_map['Tasks']
