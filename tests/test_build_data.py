
import json
import logging
import os

import pytest
import smartsheet
from freezegun import freeze_time
from uuid_module.build_data import build_linked_cell, build_row, dest_indexes
from uuid_module.get_data import get_all_row_data
from uuid_module.helper import get_column_map
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
    jira_index_sheet, _ = jira_index_sheet
    jira_index_col_map = get_column_map(jira_index_sheet)
    return jira_index_col_map


@pytest.fixture(scope="module")
def dest_col_map(sheet_fixture):
    sheet, _, _, _ = sheet_fixture
    dest_col_map = get_column_map(sheet)
    return dest_col_map


@pytest.fixture
def row():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


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
    _, sheet_list, _, _ = sheet_fixture
    project_data = get_all_row_data(sheet_list, columns, minutes_fixture)

    with pytest.raises(TypeError):
        dest_indexes("project_data")

    dest_sheet_index = dest_indexes(project_data)
    assert type(dest_sheet_index) == tuple


# TODO: Valdate returned data is not malformed
def test_build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
                   jira_index_col_map, idx_row_id):
    jira_index_sheet, _ = jira_index_sheet
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
