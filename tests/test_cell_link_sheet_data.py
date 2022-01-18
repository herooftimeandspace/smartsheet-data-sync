import json
import logging
import os

import pytest
import smartsheet
from uuid_module.cell_link_sheet_data import write_uuid_cell_links
from uuid_module.get_data import get_all_row_data, get_secret, get_secret_name
from uuid_module.variables import dev_minutes, sheet_columns
from uuid_module.write_data import write_predecessor_dates

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


# Need Mock
@pytest.fixture
def smartsheet_client(env):
    secret_name = get_secret_name(env)
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


@pytest.fixture
def minutes_fixture():
    min = dev_minutes
    return min


@pytest.fixture
def columns():
    columns = sheet_columns
    return columns


@pytest.fixture
def project_data_index(sheet_fixture, columns, minutes_fixture):
    _, source_sheets, _, _ = sheet_fixture
    project_uuid_index = get_all_row_data(
        source_sheets, columns, minutes_fixture)
    return project_uuid_index


def test_write_uuid_cell_links(project_data_index, sheet_fixture,
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
