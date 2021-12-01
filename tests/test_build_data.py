import base64
import json
import logging
import os
from collections import defaultdict

import pytest
import pytz
import smartsheet
from freezegun import freeze_time
from pytest_mock import mocker
from uuid_module.build_data import build_linked_cell
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes, load_jira_index,
                                  refresh_source_sheets)
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, has_cell_link, json_extract)
from uuid_module.variables import (jira_col, jira_idx_sheet,
                                   jira_index_columns, sheet_columns,
                                   summary_col, uuid_col, workspace_id)

logger = logging.getLogger(__name__)


@pytest.fixture
def jira_index_sheet():
    return


@pytest.fixture
def jira_index_col_map():
    return


@pytest.fixture
def dest_col_map():
    return


@pytest.fixture
def idx_row_id():
    return


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


# Need Mock
@pytest.fixture
def smartsheet_client(env):
    secret_name = get_secret_name(env)
    print(secret_name)
    try:
        os.environ["SMARTSHEET_ACCESS_TOKEN"] = get_secret(secret_name)
    except TypeError:
        raise ValueError("Refresh Isengard Auth")
    smartsheet_client = smartsheet.Smartsheet()
    # Make sure we don't miss any error
    smartsheet_client.errors_as_exceptions(True)
    return smartsheet_client


@pytest.fixture
def env():
    return "-debug"


def test_build_linked_cell(jira_index_sheet, jira_index_col_map, dest_col_map,
                           idx_row_id, colunn, smartsheet_client):
    # new_cell_link = smartsheet_client.models.CellLink()
    # new_cell_link.sheet_id = jira_index_sheet.id
    # new_cell_link.row_id = int(idx_row_id)
    # new_cell_link.column_id = int(jira_index_col_map[colunn])

    # new_cell = smartsheet_client.models.Cell()
    # new_cell.column_id = int(dest_col_map[colunn])
    # new_cell.value = smartsheet_client.models.ExplicitNull()
    # new_cell.link_in_from_cell = new_cell_link

    # return new_cell
    assert 0 == 0


def test_dest_indexes(project_data):
    # dest_sheet_index = defaultdict(list)
    # # dest_row_index = defaultdict(list)
    # for uuid, ticket in project_data.items():
    #     if uuid is None:
    #         continue
    #     else:
    #         dest_sheet_id = uuid.split("-")[0]
    #         dest_sheet_index[dest_sheet_id].append(ticket)
    # return dest_sheet_index,  # dest_row_index
    assert 0 == 0


def test_build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
                   jira_index_col_map, idx_row_id, smartsheet_client):
    # new_row = smartsheet_client.models.Row()
    # new_row.id = row.id
    # for col in columns_to_link:
    #     old_cell = get_cell_data(row, col, dest_col_map)
    #     try:
    #         cell_check = has_cell_link(old_cell, 'In')
    #     except KeyError as e:
    #         if str(e) == str("'Unlinked'"):
    #             cell_check = "Unlinked"
    #         else:
    #             raise KeyError

    #     if cell_check == "Linked":
    #         msg = str("Valid cell link: RowID {} | Row Number {} | "
    #                   "ColName {} | Cell Value {}").format(row.id,
    #                                                        row.row_number,
    #                                                        col,
    #                                                        old_cell.
    #                                                        link_in_from_cell)
    #         logging.debug(msg)
    #     elif cell_check == "Unlinked":
    #         link_cell = build_linked_cell(jira_index_sheet,
    #                                       jira_index_col_map,
    #                                       dest_col_map,
    #                                       idx_row_id,
    #                                       col,
    #                                       smartsheet_client)
    #         new_row.cells.append(link_cell)
    #         msg = str("No Cell Link: Row ID {} | Row Number {} | "
    #                   "ColName {} | Cell link {}").format(
    #             row.id, row.row_number, col, link_cell.link_in_from_cell)
    #         logging.debug(msg)
    #     elif cell_check == "Broken":
    #         unlink_cell = smartsheet_client.models.Cell()
    #         unlink_cell.id = int(dest_col_map[col])
    #         unlink_cell.value = old_cell.value
    #         new_row.cells.append(unlink_cell)
    #         msg = str("Broken Cell Link: Row ID {} | Row Number {} | "
    #                   "ColName {} | Cell link {}".format(row.id,
    #                                                      row.row_number, col,
    #                                                      unlink_cell.
    #                                                      link_in_from_cell))
    #         logging.debug(msg)
    #     elif cell_check is None:
    #         msg = str("Cell is valid and unlinked, but is {}. Continuing "
    #                   "to the next cell.").format(cell_check)
    #         logging.debug(msg)
    #     else:
    #         logging.warning("Unknown state for cell links.")
    # if new_row.cells:
    #     return new_row
    # else:
    #     return None
    assert 0 == 0
