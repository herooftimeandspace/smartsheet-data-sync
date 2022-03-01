
import json
import logging
import os
import pytest
import smartsheet
from freezegun import freeze_time
from uuid_module.variables import (assignee_col, jira_col, dev_minutes,
                                   sheet_columns, status_col, task_col)
logger = logging.getLogger(__name__)
cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def jira_index_sheet():
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        dev_idx_sheet = json.load(f)
        dev_idx_sheet_dict = dict(dev_idx_sheet)
        dev_idx_sheet = smartsheet.models.Sheet(dev_idx_sheet)
    return dev_idx_sheet, dev_idx_sheet_dict


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
def jira_index_col_map(jira_index_sheet):
    from uuid_module.helper import get_column_map
    jira_index_sheet, _ = jira_index_sheet
    jira_index_col_map = get_column_map(jira_index_sheet)
    return jira_index_col_map


@pytest.fixture(scope="module")
def dest_col_map(sheet_fixture):
    from uuid_module.helper import get_column_map
    sheet, _, _, _ = sheet_fixture
    dest_col_map = get_column_map(sheet)
    return dest_col_map


@pytest.fixture
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    linked_row = smartsheet.models.Row(row_json)
    with open(cwd + '/dev_program_plan_unlinked_row.json') as f:
        unlinked_row_json = json.load(f)
    unlinked_row = smartsheet.models.Row(unlinked_row_json)
    return linked_row, unlinked_row


@pytest.fixture(scope="module")
def idx_row_id():
    with open(cwd + '/dev_jira_index_row.json') as f:
        row_json = json.load(f)
    return str(row_json['id'])


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


@pytest.fixture
def columns_to_link():
    columns_to_link = [jira_col, status_col, task_col, assignee_col]
    return columns_to_link


@pytest.fixture
def jira_column():
    return jira_col


@pytest.fixture
def minutes_fixture():
    min = dev_minutes
    return min


@pytest.fixture(scope="module")
def env():
    return "-debug"


# TODO: Validate returned data is not malformed
def test_build_linked_cell(jira_index_sheet, jira_index_col_map,
                           dest_col_map, idx_row_id, jira_column):
    from uuid_module.build_data import build_linked_cell
    jira_index_sheet, _ = jira_index_sheet
    with pytest.raises(TypeError):
        build_linked_cell("jira_index_sheet", jira_index_col_map, dest_col_map,
                          idx_row_id, jira_column)
    with pytest.raises(TypeError):
        build_linked_cell(jira_index_sheet, "jira_index_col_map",
                          dest_col_map, idx_row_id, jira_column)
    with pytest.raises(TypeError):
        build_linked_cell(jira_index_sheet, jira_index_col_map,
                          "dest_col_map", idx_row_id, jira_column)
    with pytest.raises(TypeError):
        build_linked_cell(jira_index_sheet, jira_index_col_map,
                          dest_col_map, 7, jira_column)
    with pytest.raises(TypeError):
        build_linked_cell(jira_index_sheet, jira_index_col_map,
                          dest_col_map, idx_row_id, 7)

    link_cell = build_linked_cell(jira_index_sheet, jira_index_col_map,
                                  dest_col_map, idx_row_id, jira_column)
    assert type(link_cell) == smartsheet.models.cell.Cell


# TODO: Validate returned data is not malformed
@freeze_time("2021-11-18 21:23:54")
def test_dest_indexes(sheet_fixture, columns, minutes_fixture):
    from uuid_module.build_data import dest_indexes
    from uuid_module.get_data import get_all_row_data
    _, sheet_list, _, _ = sheet_fixture
    project_data = get_all_row_data(sheet_list, columns, minutes_fixture)

    with pytest.raises(TypeError):
        dest_indexes("project_data")

    dest_sheet_index = dest_indexes(project_data)
    assert type(dest_sheet_index) == tuple


# TODO: Valdate returned data is not malformed
def test_build_row(row_fixture, columns_to_link, dest_col_map,
                   jira_index_sheet, jira_index_col_map, idx_row_id):
    from uuid_module.build_data import build_row
    jira_index_sheet, _ = jira_index_sheet
    _, row = row_fixture
    with pytest.raises(TypeError):
        build_row("row", columns_to_link, dest_col_map, jira_index_sheet,
                  jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_row(row, "columns_to_link", dest_col_map, jira_index_sheet,
                  jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_row(row, columns_to_link, "dest_col_map", jira_index_sheet,
                  jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_row(row, columns_to_link, dest_col_map, "jira_index_sheet",
                  jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
                  "jira_index_col_map", idx_row_id)
    with pytest.raises(TypeError):
        build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
                  jira_index_col_map, 7)

    new_row = build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
                        jira_index_col_map, idx_row_id)
    assert type(new_row) == smartsheet.models.row.Row


# TODO: Failing pynguin tests
# Automatically generated by Pynguin.
# import uuid_module.build_data as module_0

# def test_case_0():
#     try:
#         str_0 = 'aD zV5 YoZ\tI E!G'
#         tuple_0 = ()
#         var_0 = module_0.build_linked_cell(str_0, str_0, tuple_0, tuple_0,
#             tuple_0)
#     except BaseException:
#         pass


# def test_case_1():
#     try:
#         str_0 = 'Sheet IDs object type {}, object values {}'
#         var_0 = module_0.dest_indexes(str_0)
#     except BaseException:
#         pass


# def test_case_2():
#     try:
#         bool_0 = True
#         tuple_0 = ()
#         var_0 = module_0.build_row(tuple_0, bool_0, tuple_0, bool_0,
#             tuple_0, bool_0)
#     except BaseException:
#         pass


# def test_case_3():
#     try:
#         bool_0 = False
#         str_0 = 'H1r~8HgU"\nd8T'
#         list_0 = None
#         dict_0 = {str_0: str_0, list_0: list_0}
#         var_0 = module_0.dest_indexes(dict_0)
#         assert var_0 == ({'H1r~8HgU"\nd8T': ['H1r~8HgU"\nd8T']},)
#         assert module_0.logger.filters == []
#         assert module_0.logger.name == 'uuid_module.build_data'
#         assert module_0.logger.level == 0
#         assert module_0.logger.propagate is True
#         assert module_0.logger.handlers == []
#         assert module_0.logger.disabled is False
#         var_1 = module_0.build_row(str_0, list_0, str_0, list_0, list_0,
#               bool_0)
#     except BaseException:
#         pass

# def test_case_4():
#     tuple_0 = ()
#     str_0 = 'Second argument must be non-zero, not {}'
#     dict_0 = {str_0: tuple_0}
#     var_0 = module_0.dest_indexes(dict_0)
#     assert var_0 == ({'Second argument must be non': [()]},)
#     assert module_0.logger.filters == []
#     assert module_0.logger.name == 'uuid_module.build_data'
#     assert module_0.logger.level == 0
#     assert module_0.logger.propagate is True
#     assert module_0.logger.handlers == []
#     assert module_0.logger.disabled is False
