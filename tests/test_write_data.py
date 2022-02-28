import json
import logging
import os

import pytest
import smartsheet
from freezegun import freeze_time
from uuid_module.get_data import (get_all_row_data, get_sub_indexes)
from uuid_module.variables import (dev_minutes, sheet_columns)
from uuid_module.write_data import (check_uuid, write_jira_index_cell_links,
                                    write_predecessor_dates, write_uuids)
cwd = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


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


@pytest.fixture
def env():
    return "-debug"


@pytest.fixture
def minutes_fixture():
    min = dev_minutes
    return min


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


@pytest.fixture
def uuids():
    uuid_value = ["7208979009955716-3683235938232196-\
        7010994181433220-202105112138550000"]
    jira_value = "JAR-123"
    uuid_list = ["7208979009955716-3683235938232196-\
        7010994181433220-202105112138550000"]
    jira_data_values = ["JAR-123", "JAR-456"]
    return uuid_value, jira_value, uuid_list, jira_data_values


@pytest.fixture
def src_data():
    data = {}
    data['UUID'] = "7208979009955716-3683235938232196"
    return data


@pytest.fixture
@freeze_time("2021-11-18 21:23:54")
# TODO: Static return and check for actual values
def project_indexes(sheet_fixture, columns, minutes_fixture):
    _, sheet_list, _, _ = sheet_fixture
    project_uuid_index = get_all_row_data(sheet_list, columns, minutes_fixture)
    _, sub_index = get_sub_indexes(project_uuid_index)
    return project_uuid_index, sub_index


def test_write_uuids(sheet_fixture):
    sheets_to_update, _, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        write_uuids("sheets_to_update")
    return


def test_write_jira_index_cell_links(project_indexes):
    _, project_sub_index = project_indexes
    with pytest.raises(TypeError):
        write_jira_index_cell_links("project_sub_index")
    return


def test_check_uuid(uuids):
    uuid_value, jira_value, uuid_list, jira_data_values = uuids
    with pytest.raises(TypeError):
        check_uuid("uuid_value", jira_value, uuid_list, jira_data_values)
    with pytest.raises(TypeError):
        check_uuid(uuid_value, [jira_value], uuid_list, jira_data_values)
    with pytest.raises(TypeError):
        check_uuid(uuid_value, jira_value, "uuid_list", jira_data_values)
    with pytest.raises(TypeError):
        check_uuid(uuid_value, jira_value, uuid_list, "jira_data_values")
    return


def test_write_predecessor_dates(src_data, project_indexes):
    project_data_index, _ = project_indexes
    with pytest.raises(TypeError):
        write_predecessor_dates("src_data", project_data_index)
    with pytest.raises(TypeError):
        write_predecessor_dates(src_data, "project_data_index")
    # TODO: Write a test to validate the format instead.
    #     Format of the src_data should be:
    # {
    #     "UUID": "7208979009955716-3683235938232196-
    #             7010994181433220-202105112138550000",  # Type: str
    #     "Tasks": "Retrospective", # Type: str
    #     "Description": "Thoughts on how the project went.",  # Type: str
    #     "Status": "In Progress",  # Type: str
    #     "Assigned To": "link@twitch.tv",  # Type: str
    #     "Jira Ticket": "ING-12342",  # Type: str
    #     "Duration": None,  # Type: str
    #     "Start": "2021-03-31T08:00:00",  # Type: str
    #     "Finish": "2021-03-31T08:00:00",  # Type: str
    #     "Predecessors": "38FS +1w",  # Type: str
    #     "Summary": "False"  # Type: str
    # }
    return
