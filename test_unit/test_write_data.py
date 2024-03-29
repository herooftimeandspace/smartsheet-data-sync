import json
import logging
from unittest.mock import patch

import pytest
import smartsheet
import data_module.helper as helper
import app.variables as app_vars
import data_module.write_data as write_data
import data_module.get_data as get_data
from freezegun import freeze_time

_, cwd = helper.get_local_paths()
logger = logging.getLogger(__name__)


# @pytest.fixture(scope="module")
# def sheet_fixture():
#     import data_module.helper as helper
#     with open(cwd + '/dev_program_plan.json') as f:
#         sheet_json = json.load(f)

#     def no_uuid_col_fixture(sheet_json):
#         json_copy = sheet_json.copy()
#         json_copy['columns'][20]['name'] = "Not UUID"
#         no_uuid_col = smartsheet.models.Sheet(json_copy)
#         return no_uuid_col

#     def no_summary_col_fixture(sheet_json):
#         json_copy = sheet_json.copy()
#         json_copy['columns'][4]['name'] = "Not Summary"
#         no_summary_col = smartsheet.models.Sheet(json_copy)
#         return no_summary_col

#     sheet = smartsheet.models.Sheet(sheet_json)
#     col_map = helper.get_column_map(sheet)
#     sheet_no_uuid_col = no_uuid_col_fixture(sheet_json)
#     sheet_no_summary_col = no_summary_col_fixture(sheet_json)
#     return sheet, col_map, sheet_no_uuid_col, sheet_no_summary_col


# @pytest.fixture
# def row_fixture():
#     with open(cwd + '/dev_program_plan_row.json') as f:
#         linked_row_json = json.load(f)
#     with open(cwd + '/dev_program_plan_row.json') as f:
#         unlinked_row_json = json.load(f)
#     linked_row = smartsheet.models.Row(linked_row_json)
#     unlinked_row = smartsheet.models.Row(unlinked_row_json)
#     return linked_row, unlinked_row


# @pytest.fixture(scope="module")
# def index_fixture():
#     import data_module.get_data as get_data
#     with open(cwd + '/dev_jira_index_sheet.json') as f:
#         sheet_json = json.load(f)
#     index_sheet = smartsheet.models.Sheet(sheet_json)

#     @patch("data_module.smartsheet_api.get_sheet", return_value=index_sheet)
#     def load_jira_index_fixture(mock_0):
#         jira_index_sheet, jira_index_col_map, jira_index_rows \
#             = get_data.load_jira_index(index_sheet.id)
#         return jira_index_sheet, jira_index_col_map, jira_index_rows

#     jira_index_sheet, jira_index_col_map, jira_index_rows \
#         = load_jira_index_fixture()
#     return jira_index_sheet, jira_index_col_map, jira_index_rows


# @pytest.fixture
# def env():
#     return "-debug"


@pytest.fixture
def uuids():
    uuid_value = ["7208979009955716-3683235938232196-"
                  "7010994181433220-202105112138550000"]
    jira_value = "JAR-123"
    uuid_list = ["7208979009955716-3683235938232196-"
                 "7010994181433220-202105112138550000"]
    jira_data_values = ["JAR-123", "JAR-456"]
    return uuid_value, jira_value, uuid_list, jira_data_values


@pytest.fixture
def src_data():
    data = {
        "UUID": "7208979009955716-3683235938232196-"
                "7010994181433220-202105112138550000",  # Type: str
        "Tasks": "Retrospective",  # Type: str
        "Description": "Thoughts on how the project went.",  # Type: str
        "Status": "In Progress",  # Type: str
        "Assigned To": "link@twitch.tv",  # Type: str
        "Jira Ticket": "ING-12342",  # Type: str
        "Duration": None,  # Type: str
        "Start": "2021-03-31T08:00:00",  # Type: str
        "Finish": "2021-03-31T08:00:00",  # Type: str
        "Predecessors": "38FS +1w",  # Type: str
        "Summary": "False"  # Type: str
    }
    return data


@pytest.fixture
@freeze_time("2021-11-18 21:23:54")
# TODO: Static return and check for actual values
def project_indexes(sheet_fixture):
    import app.config as config
    import data_module.get_data as get_data
    sheet, _, _, _ = sheet_fixture
    project_uuid_index = get_data.get_all_row_data([sheet],
                                                   app_vars.sheet_columns,
                                                   config.minutes)
    _, sub_index = get_data.get_sub_indexes(project_uuid_index)
    return project_uuid_index, sub_index


def test_write_uuids_0():
    with pytest.raises(TypeError):
        write_data.write_uuids("sheets_to_update")


def test_write_uuids_1(sheet_fixture):
    sheet, _, _, _ = sheet_fixture
    sheets_to_update = {}
    sheets_to_update[sheet.id] = {
        "sheet_name": sheet.name, "row_data": {}}

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    def test_0(mock_0):
        sheets_updated = write_data.write_uuids(sheets_to_update)
        return sheets_updated

    result_0 = test_0()
    assert isinstance(result_0, int)
    assert result_0 == 0


def test_write_uuids_2(sheet_fixture):
    _, col_map, _, _ = sheet_fixture
    with open(cwd + '/dev_program_plan.json') as f:
        blank_uuid_sheet = json.load(f)

    for row in blank_uuid_sheet['rows']:
        for cell in row['cells']:
            if cell['columnId'] == col_map[app_vars.uuid_col]:
                cell['value'] = None
                cell['objectValue'] = None
                cell['displayValue'] = None
    blank_uuid_sheet = smartsheet.models.Sheet(blank_uuid_sheet)
    sheets_to_update = get_data.get_blank_uuids([blank_uuid_sheet])

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    def test_0(mock_0):
        sheets_updated = write_data.write_uuids(sheets_to_update)
        return sheets_updated

    result_0 = test_0()
    assert isinstance(result_0, int)
    assert result_0 == 1


def test_write_jira_index_cell_links_0():
    with pytest.raises(TypeError):
        write_data.write_jira_index_cell_links("project_sub_index")
    with pytest.raises(ValueError):
        write_data.write_jira_index_cell_links({})


def test_write_jira_index_cell_links_1(index_sheet_fixture,
                                       sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    index_sheet, index_col_map, index_rows, _ = index_sheet_fixture

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.load_jira_index",
           return_value=(index_sheet, index_col_map,
                         index_rows))
    @patch("data_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0, mock_1, mock_2):
        project_sub_index = {}
        project_sub_index[31337] = "1337"
        with pytest.raises(ValueError):
            write_data.write_jira_index_cell_links(project_sub_index)
        return True

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.load_jira_index",
           return_value=(index_sheet, index_col_map,
                         index_rows))
    @patch("data_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_1(mock_0, mock_1, mock_2):
        project_sub_index = {}
        project_sub_index["31337"] = 1337
        with pytest.raises(ValueError):
            write_data.write_jira_index_cell_links(project_sub_index)
        return True

    result_0 = test_0()
    result_1 = test_1()
    assert result_0 is True
    assert result_1 is True


def test_write_jira_index_cell_links_2(project_indexes, index_sheet_fixture,
                                       sheet_fixture):
    _, project_sub_index = project_indexes
    sheet, _, _, _ = sheet_fixture
    index_sheet, index_col_map, index_rows, _ = index_sheet_fixture

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("data_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("data_module.get_data.load_jira_index",
           return_value=(index_sheet, index_col_map,
                         index_rows))
    @patch("data_module.smartsheet_api.get_sheet", return_value=sheet)
    def test_0(mock_0, mock_1, mock_2):
        var_0 = write_data.write_jira_index_cell_links(project_sub_index)
        return var_0

    result_0 = test_0()
    result_1 = "No Jira Ticket updates needed for Sheet ID" in result_0
    assert isinstance(result_0, str)
    assert result_1 is True


# TODO: Build a version of the sheet we can use to link and get a successful
# msg back.
# def test_write_jira_index_cell_links_3(project_indexes, index_fixture,
#                                        sheet_fixture, row_fixture):
#     _, project_sub_index = project_indexes
#     sheet, _, _, _ = sheet_fixture
#     jira_index_sheet, jira_index_col_map, jira_index_rows = index_fixture
#     row, _ = row_fixture

#     result = smartsheet.models.Result()
    # result.message = "SUCCESS"
    # result.result_code = 0

    # @patch("data_module.smartsheet_api.write_rows_to_sheet",
    #        return_value=result)
#     @patch("data_module.build_data.build_row", return_value=row)
#     @patch("data_module.get_data.load_jira_index",
#            return_value=(jira_index_sheet, jira_index_col_map,
#                          jira_index_rows))
#     @patch("data_module.smartsheet_api.get_sheet", return_value=sheet)
#     def test_0(mock_0, mock_1, mock_2, mock_3):
#         var_0 = write_data.write_jira_index_cell_links(project_sub_index)
#         return var_0

#     result_0 = test_0()
#     result_1 = "Writing" in result_0
#     assert isinstance(result_0, str)
#     assert result_1 is True


# def test_write_predecessor_dates_0(src_data, project_indexes):
#     project_data_index, _ = project_indexes
#     with pytest.raises(TypeError):
#         write_data.write_predecessor_dates("src_data", project_data_index)
#     with pytest.raises(TypeError):
#         write_data.write_predecessor_dates(src_data, "project_data_index")
#     with pytest.raises(ValueError):
#         data_copy = src_data.copy()
#         data_copy["UUID"] = 1337
#         write_data.write_predecessor_dates(data_copy, project_data_index)
#     with pytest.raises(ValueError):
#         data_copy = src_data.copy()
#         data_copy.pop("UUID", None)
#         write_data.write_predecessor_dates(data_copy, project_data_index)
#     #     Format of the src_data should be:
#     # {
#     #     "UUID": "7208979009955716-3683235938232196-
#     #             7010994181433220-202105112138550000",  # Type: str
#     #     "Tasks": "Retrospective", # Type: str
#     #     "Description": "Thoughts on how the project went.",  # Type: str
#     #     "Status": "In Progress",  # Type: str
#     #     "Assigned To": "link@twitch.tv",  # Type: str
#     #     "Jira Ticket": "ING-12342",  # Type: str
#     #     "Duration": None,  # Type: str
#     #     "Start": "2021-03-31T08:00:00",  # Type: str
#     #     "Finish": "2021-03-31T08:00:00",  # Type: str
#     #     "Predecessors": "38FS +1w",  # Type: str
#     #     "Summary": "False"  # Type: str
#     # }


# def test_write_predecessor_dates_1(src_data, project_indexes,
#                                    sheet_fixture, row_fixture, cell_fixture):
#     project_data_index, _ = project_indexes
#     sheet, col_map, _, _ = sheet_fixture
#     _, unlinked_row = row_fixture
#     pred_cell, _, _, _, _, _ = cell_fixture

#     #     Format of the src_data should be:
#     # {
#     #     "UUID": "7208979009955716-3683235938232196-
#     #             7010994181433220-202105112138550000",  # Type: str
#     #     "Tasks": "Retrospective", # Type: str
#     #     "Description": "Thoughts on how the project went.",  # Type: str
#     #     "Status": "In Progress",  # Type: str
#     #     "Assigned To": "link@twitch.tv",  # Type: str
#     #     "Jira Ticket": "ING-12342",  # Type: str
#     #     "Duration": None,  # Type: str
#     #     "Start": "2021-03-31T08:00:00",  # Type: str
#     #     "Finish": "2021-03-31T08:00:00",  # Type: str
#     #     "Predecessors": "38FS +1w",  # Type: str
#     #     "Summary": "False"  # Type: str
#     # }

#     result = smartsheet.models.Result()
#     result.message = "SUCCESS"
#     result.result_code = 0

#     @patch("data_module.smartsheet_api.get_sheet", return_value=sheet)
#     @patch("data_module.helper.get_column_map", return_value=col_map)
#     @patch("data_module.smartsheet_api.get_row", return_value=unlinked_row)
#     @patch("data_module.helper.get_cell_data",
#            return_value=pred_cell)
#     @patch("data_module.smartsheet_api.write_rows_to_sheet",
#            return_value=result)
#     def test_0(mock_0, mock_1, mock_2, mock_3, mock_4):
#         result_0 = write_data.write_predecessor_dates(src_data,
#                                                       project_data_index)
#         return result_0
#     result_1 = test_0()
#     assert result_1 is True
