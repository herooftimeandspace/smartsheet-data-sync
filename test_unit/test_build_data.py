
import json
import logging

import pytest
import smartsheet
import uuid_module.variables as app_vars
import uuid_module.helper as helper
from freezegun import freeze_time

logger = logging.getLogger(__name__)
_, cwd = helper.get_local_paths()


@pytest.fixture(scope="module")
def jira_index_fixture():
    with open(cwd + '/dev_jira_index_sheet.json') as f:
        sheet = json.load(f)
        sheet = smartsheet.models.Sheet(sheet)
    col_map = helper.get_column_map(sheet)

    with open(cwd + '/dev_jira_index_row.json') as f:
        row_json = json.load(f)
        row = smartsheet.models.Row(row_json)
    return sheet, col_map, row


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col(sheet_json):
        sheet_json['columns'][20]['title'] = "Not UUID"
        no_uuid_col = smartsheet.models.Sheet(sheet_json)
        return no_uuid_col

    def no_summary_col(sheet_json):
        sheet_json['columns'][4]['name'] = "Not Summary"
        no_summary_col = smartsheet.models.Sheet(sheet_json)
        return no_summary_col

    sheet = smartsheet.models.Sheet(sheet_json)
    col_map = helper.get_column_map(sheet)
    sheet_no_uuid_col = no_uuid_col(sheet_json)
    sheet_no_summary_col = no_summary_col(sheet_json)
    return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture
def row_fixture():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    linked_row = smartsheet.models.Row(row_json)
    with open(cwd + '/dev_program_plan_unlinked_row.json') as f:
        unlinked_row_json = json.load(f)
    unlinked_row = smartsheet.models.Row(unlinked_row_json)
    return linked_row, unlinked_row


@pytest.fixture
def columns_to_link():
    columns_to_link = [app_vars.jira_col, app_vars.status_col,
                       app_vars.task_col, app_vars.assignee_col]
    return columns_to_link


@pytest.fixture(scope="module")
def env():
    return "-debug"


# TODO: Validate returned data is not malformed
def test_build_linked_cell_0(jira_index_fixture, sheet_fixture):
    import uuid_module.build_data as build_data
    jira_index_sheet, jira_index_col_map, jira_index_row = jira_index_fixture
    idx_row_id = jira_index_row.id
    _, dest_col_map, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        build_data.build_linked_cell("jira_index_sheet", jira_index_col_map,
                                     dest_col_map, idx_row_id,
                                     app_vars.jira_col)
    with pytest.raises(TypeError):
        build_data.build_linked_cell(jira_index_sheet, "jira_index_col_map",
                                     dest_col_map, idx_row_id,
                                     app_vars.jira_col)
    with pytest.raises(TypeError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     "dest_col_map", idx_row_id,
                                     app_vars.jira_col)
    with pytest.raises(TypeError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     dest_col_map, [1337, 31337],
                                     app_vars.jira_col)
    with pytest.raises(TypeError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     dest_col_map, idx_row_id, 7)
    with pytest.raises(TypeError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     dest_col_map, "idx_row_id",
                                     app_vars.jira_col)
    with pytest.raises(ValueError):
        build_data.build_linked_cell(jira_index_sheet, {},
                                     dest_col_map, idx_row_id,
                                     app_vars.jira_col)
    with pytest.raises(ValueError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     {}, idx_row_id,
                                     app_vars.jira_col)
    with pytest.raises(ValueError):
        build_data.build_linked_cell(jira_index_sheet, jira_index_col_map,
                                     dest_col_map, -1337,
                                     app_vars.jira_col)


def test_build_linked_cell_1(jira_index_fixture, sheet_fixture):
    import uuid_module.build_data as build_data
    jira_index_sheet, jira_index_col_map, jira_index_row = jira_index_fixture
    idx_row_id = jira_index_row.id
    _, dest_col_map, _, _ = sheet_fixture
    link_cell = build_data.build_linked_cell(jira_index_sheet,
                                             jira_index_col_map, dest_col_map,
                                             idx_row_id, app_vars.jira_col)
    assert type(link_cell) == smartsheet.models.cell.Cell
    assert link_cell.column_id == int(dest_col_map[app_vars.jira_col])
    assert isinstance(link_cell.value, type(smartsheet.models.ExplicitNull()))
    # link_in = helper.has_cell_link(link_cell, "In")
    # assert link_in == "Linked"
    assert link_cell.link_in_from_cell.sheet_id == jira_index_sheet.id
    assert link_cell.link_in_from_cell.row_id == idx_row_id
    assert link_cell.link_in_from_cell.column_id == \
        jira_index_col_map[app_vars.jira_col]


# TODO: Validate returned data is not malformed
@freeze_time("2021-11-18 21:23:54")
def test_dest_indexes(sheet_fixture):
    import uuid_module.build_data as build_data
    import uuid_module.get_data as get_data
    import app.config as config
    sheet, _, _, _ = sheet_fixture
    project_data = get_data.get_all_row_data(
        [sheet], app_vars.sheet_columns, config.minutes)

    with pytest.raises(TypeError):
        build_data.dest_indexes("project_data")

    dest_sheet_index = build_data.dest_indexes(project_data)
    assert type(dest_sheet_index) == tuple


# TODO: Valdate returned data is not malformed
def test_build_row_0(row_fixture, columns_to_link, sheet_fixture,
                     jira_index_fixture):
    import uuid_module.build_data as build_data
    _, dest_col_map, _, _ = sheet_fixture
    jira_index_sheet, jira_index_col_map, jira_index_row = jira_index_fixture
    idx_row_id = jira_index_row.id
    _, row = row_fixture
    with pytest.raises(TypeError):
        build_data.build_row("row", columns_to_link, dest_col_map,
                             jira_index_sheet, jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_data.build_row(row, "columns_to_link", dest_col_map,
                             jira_index_sheet, jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_data.build_row(row, columns_to_link, "dest_col_map",
                             jira_index_sheet, jira_index_col_map, idx_row_id)
    with pytest.raises(TypeError):
        build_data.build_row(row, columns_to_link, dest_col_map,
                             "jira_index_sheet", jira_index_col_map,
                             idx_row_id)
    with pytest.raises(TypeError):
        build_data.build_row(row, columns_to_link, dest_col_map,
                             jira_index_sheet, "jira_index_col_map",
                             idx_row_id)
    with pytest.raises(TypeError):
        build_data.build_row(row, columns_to_link, dest_col_map,
                             jira_index_sheet, jira_index_col_map,
                             "idx_row_id")


# TODO: Valdate returned data is not malformed
def test_build_row_1(row_fixture, columns_to_link, sheet_fixture,
                     jira_index_fixture):
    import uuid_module.build_data as build_data
    _, dest_col_map, _, _ = sheet_fixture
    jira_index_sheet, jira_index_col_map, jira_index_row = jira_index_fixture
    idx_row_id = jira_index_row.id
    _, row = row_fixture

    new_row = build_data.build_row(row, columns_to_link, dest_col_map,
                                   jira_index_sheet, jira_index_col_map,
                                   idx_row_id)
    assert type(new_row) == smartsheet.models.row.Row
    assert new_row.id == row.id


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
