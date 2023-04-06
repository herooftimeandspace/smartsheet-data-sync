import logging

import app.config as config
import pytest
import data_module.cell_link_sheet_data as cell_links
import data_module.get_data as get_data
import data_module.helper as helper
import app.variables as app_vars

# import data_module.write_data as write_data

_, cwd = helper.get_local_paths()
logger = logging.getLogger(__name__)


# @pytest.fixture(scope="module")
# def sheet_fixture():
#     with open(cwd + '/dev_program_plan.json') as f:
#         sheet_json = json.load(f)

#     def no_uuid_col_fixture(sheet_json):
#         sheet_json['columns'][20]['title'] = "Not UUID"
#         no_uuid_col = smartsheet.models.Sheet(sheet_json)
#         return no_uuid_col

#     def no_summary_col_fixture(sheet_json):
#         sheet_json['columns'][4]['name'] = "Not Summary"
#         no_summary_col = smartsheet.models.Sheet(sheet_json)
#         return no_summary_col

#     sheet = smartsheet.models.Sheet(sheet_json)
#     sheet_list = [sheet]
#     sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
#     sheet_no_summary_col = no_summary_col_fixture(sheet_json)
#     return sheet, sheet_list, sheet_no_uuid_col, sheet_no_summary_col


@pytest.fixture
def project_data_index(sheet_fixture):
    sheet, _, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data(
        [sheet], app_vars.sheet_columns, config.minutes)
    return project_uuid_index


def test_write_uuid_cell_links(project_data_index, sheet_fixture,
                               set_init_fixture):
    sheet, _, _, _ = sheet_fixture
    smartsheet_client = set_init_fixture
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links("project_data_index", [sheet],
                                         smartsheet_client)
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links(project_data_index, "[sheets]",
                                         smartsheet_client)
    with pytest.raises(TypeError):
        cell_links.write_uuid_cell_links(project_data_index, [sheet],
                                         "smartsheet_client")
