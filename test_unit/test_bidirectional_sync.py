# import json
import logging

import pytest
import smartsheet
import uuid_module.bidirectional_sync as sync
import uuid_module.helper as helper
import uuid_module.variables as app_vars

# from unittest.mock import patch

# from freezegun import freeze_time

_, cwd = helper.get_local_paths()
logger = logging.getLogger(__name__)


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_compare_dates_0(cell_history_fixture):
    cell_history = cell_history_fixture
    with pytest.raises(TypeError):
        sync.compare_dates("cell_history", cell_history, "Cell")
    with pytest.raises(TypeError):
        sync.compare_dates(cell_history, "cell_history", "Cell")
    with pytest.raises(TypeError):
        sync.compare_dates(cell_history, cell_history, 1337)
    with pytest.raises(ValueError):
        sync.compare_dates(cell_history, cell_history, "1337")


# def test_compare_dates_1(cell_history_fixture):
#     index_history = cell_history_fixture
#     plan_history = cell_history_fixture
#     print(index_history, plan_history)

#     def test_0():
#         index_history.modified_at = index_history.modified_at.time_delta(
#             seconds=30)
#         result = sync.compare_dates(index_history, plan_history, "Cell")
#         return result
#     result_0 = test_0()
#     assert result_0 == "Index"


def test_get_index_row_0(index_sheet_fixture):
    jira_index_sheet, _, _, row = index_sheet_fixture
    with pytest.raises(TypeError):
        sync.get_index_row("jira_index_sheet", row.id)
    with pytest.raises(TypeError):
        sync.get_index_row(jira_index_sheet, "row.id")
    with pytest.raises(ValueError):
        sync.get_index_row(jira_index_sheet, -1337)


def test_get_index_row_1(index_sheet_fixture):
    jira_index_sheet, _, _, row = index_sheet_fixture

    def test_0():
        result = sync.get_index_row(jira_index_sheet, row.id)
        return result
    result_0 = test_0()
    assert result_0.id == row.id
    assert result_0.modified_at == row.modified_at

    def test_1():
        result = sync.get_index_row(jira_index_sheet, 1337)
        return result
    result_1 = test_1()
    assert result_1 is None


def test_rebuild_cell_0(sheet_fixture, cell_fixture):
    _, col_map, _, _ = sheet_fixture
    column_id = col_map[app_vars.jira_col]
    cell, _, _, _, _, _ = cell_fixture
    with pytest.raises(TypeError):
        sync.rebuild_cell("cell", column_id)
    with pytest.raises(TypeError):
        sync.rebuild_cell(cell, "column_id")
    with pytest.raises(ValueError):
        sync.rebuild_cell(cell, -1337)


def test_rebuild_cell_1():
    pass


def test_build_row_0(index_sheet_fixture, sheet_fixture, row_fixture):
    jira_index_sheet, jira_index_col_map, _, index_row = index_sheet_fixture
    plan_sheet, plan_col_map, _, _ = sheet_fixture
    _, plan_row = row_fixture
    columns_to_compare = [app_vars.jira_col, app_vars.jira_status_col,
                          app_vars.assignee_col, app_vars.task_col]
    with pytest.raises(TypeError):
        sync.build_row("jira_index_sheet", jira_index_col_map, index_row,
                       plan_sheet, plan_col_map, plan_row, columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, "jira_index_col_map", index_row,
                       plan_sheet, plan_col_map, plan_row, columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, jira_index_col_map, "index_row",
                       plan_sheet, plan_col_map, plan_row, columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, jira_index_col_map, index_row,
                       "plan_sheet", plan_col_map, plan_row,
                       columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, jira_index_col_map, index_row,
                       plan_sheet, "plan_col_map", plan_row,
                       columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, jira_index_col_map, index_row,
                       plan_sheet, plan_col_map, "plan_row",
                       columns_to_compare)
    with pytest.raises(TypeError):
        sync.build_row(jira_index_sheet, jira_index_col_map, index_row,
                       plan_sheet, plan_col_map, plan_row,
                       "columns_to_compare")
    with pytest.raises(ValueError):
        sync.build_row(jira_index_sheet, jira_index_col_map, index_row,
                       plan_sheet, plan_col_map, plan_row, [])


def test_build_row_1():
    pass


def test_drop_dupes_0():
    with pytest.raises(TypeError):
        sync.drop_dupes(1337)
    with pytest.raises(ValueError):
        sync.drop_dupes([])


def test_drop_dupes_1(row_fixture):
    single_row = smartsheet.models.Row()
    single_row.id = 1337
    _, unlinked_row = row_fixture
    row_list = [unlinked_row, unlinked_row, unlinked_row, single_row]
    unique = sync.drop_dupes(row_list)
    assert unique[0].id == unlinked_row.id
    assert unique[1].id == unlinked_row.id


def test_bidirectional_sync_0():
    with pytest.raises(TypeError):
        sync.bidirectional_sync("config.minutes")
    with pytest.raises(ValueError):
        sync.bidirectional_sync(-1337)
