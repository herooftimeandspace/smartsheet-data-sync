import json
import logging
import re

from uuid_module.helper import (chunks, get_cell_data, get_cell_value,
                                get_column_map, has_cell_link, json_extract)
from uuid_module.variables import (assignee_col, description_col, duration_col,
                                   jira_col, predecessor_col, start_col,
                                   status_col, task_col)
from uuid_module.write_data import write_predecessor_dates
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
from uuid_module.build_data import build_linked_cell, dest_indexes, build_row
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes, load_jira_index,
                                  refresh_source_sheets)
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, has_cell_link, json_extract)
from uuid_module.variables import (assignee_col, jira_col, jira_idx_sheet,
                                   jira_index_columns, sheet_columns,
                                   status_col, summary_col, task_col, uuid_col,
                                   workspace_id, minutes)
from uuid_module.cell_link_sheet_data import write_uuid_cell_links

cwd = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def sheet_fixture():
    with open(cwd + '/sheet_response.json') as f:
        sheet_json = json.load(f)

    def no_uuid_col_fixture(sheet_json):
        sheet_json['columns'][22]['name'] = "Not UUID"
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


@pytest.fixture
def minutes_fixture():
    min = minutes
    return min


@pytest.fixture
def project_data_index(sheet_fixture, minutes_fixture):
    _, source_sheets, _, _ = sheet_fixture
    project_uuid_index = get_all_row_data(
        source_sheets, sheet_columns, minutes_fixture)
    return project_uuid_index


def test_write_uuid_cell_links(project_data_index, source_sheets,
                               smartsheet_client):
    _, source_sheets, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        write_uuid_cell_links("project_data_index", source_sheets,
                              smartsheet_client)
    with pytest.raises(TypeError):
        write_uuid_cell_links(project_data_index, "source_sheets",
                              smartsheet_client)
    with pytest.raises(TypeError):
        write_uuid_cell_links(project_data_index, source_sheets,
                              "smartsheet_client")
