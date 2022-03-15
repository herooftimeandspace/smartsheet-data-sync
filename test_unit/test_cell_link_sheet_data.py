import json
import logging
import os

import app.config as config
import pytest
import smartsheet
import uuid_module.cell_link_sheet_data as cell_links
import uuid_module.get_data as get_data
import uuid_module.helper as helper
import uuid_module.variables as app_vars

# import uuid_module.write_data as write_data

_, cwd = helper.get_local_paths()
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
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
    sheet_list = [sheet]
    sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
    sheet_no_summary_col = no_summary_col_fixture(sheet_json)
    return sheet, sheet_list, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture
def env():
    return "-debug"


# Need Mock
@pytest.fixture
def smartsheet_client(env):
    secret_name = config.get_secret_name(env)
    try:
        os.environ["SMARTSHEET_ACCESS_TOKEN"] = config.get_secret(secret_name)
    except TypeError:
        raise ValueError("Refresh Isengard Auth")
    smartsheet_client = smartsheet.Smartsheet()
    # Make sure we don't miss any error
    smartsheet_client.errors_as_exceptions(True)
    return smartsheet_client


@pytest.fixture
def columns():
    columns = app_vars.sheet_columns
    return columns


@pytest.fixture
def project_data_index(sheet_fixture, columns):
    _, source_sheets, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data(
        source_sheets, columns, config.minutes)
    return project_uuid_index


def test_write_uuid_cell_links(project_data_index, sheet_fixture,
                               smartsheet_client):
    _, source_sheets, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links("project_data_index", source_sheets,
                                         smartsheet_client)
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links(project_data_index, "source_sheets",
                                         smartsheet_client)
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links(project_data_index, source_sheets,
                                         "smartsheet_client")
