import logging
from unittest.mock import patch

import pytest
import smartsheet
import uuid_module.helper as helper
import uuid_module.create_jira_tickets as create_jira_tickets


logger = logging.getLogger(__name__)
_, cwd = helper.get_local_paths()


def test_build_sub_indexes_0(index_sheet_fixture):

    index_sheet, index_col_map, _, _ = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(
            "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(
            index_sheet, "index_col_map")
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(None, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_sub_indexes(index_sheet, None)


def test_build_sub_indexes_1(index_sheet_fixture):
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    sub_index_dict, sub_index_list = \
        create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
    assert isinstance(sub_index_dict, dict)
    assert isinstance(sub_index_list, list)
    assert sub_index_dict is not None
    assert sub_index_list is not None


def test_build_sub_indexes_2(index_sheet_fixture):
    index_sheet, index_col_map, _, _ = index_sheet_fixture

    @patch("uuid_module.helper.get_cell_data", return_value=None)
    def test_0(mock_0):
        sub_index_dict, sub_index_list = \
            create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
        return sub_index_dict, sub_index_list

    result_0, result_1 = test_0()
    assert isinstance(result_0, dict)
    assert isinstance(result_1, list)


def test_build_sub_indexes_3(index_sheet_fixture, cell_fixture):
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    basic_cell, _, _, _, _, _ = cell_fixture
    basic_cell.value = "None"

    @patch("uuid_module.helper.get_cell_data", return_value=basic_cell)
    def test_0(mock_0):
        sub_index_dict, sub_index_list = \
            create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
        return sub_index_dict, sub_index_list

    result_0, result_1 = test_0()
    assert isinstance(result_0, dict)
    assert isinstance(result_1, list)


def test_build_sub_indexes_4(index_sheet_fixture, cell_fixture):
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    uuid_cell, _, _, _, _, _ = cell_fixture
    uuid_cell.value = "1-2-3-4"
    jira_cell = uuid_cell
    jira_cell.value = None

    @patch("uuid_module.helper.get_cell_data", return_value=jira_cell)
    @patch("uuid_module.helper.get_cell_data", return_value=uuid_cell)
    def test_0(mock_0, mock_1):
        sub_index_dict, sub_index_list = \
            create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
        return sub_index_dict, sub_index_list

    result_0, result_1 = test_0()
    assert isinstance(result_0, dict)
    assert isinstance(result_1, list)


def test_build_sub_indexes_5(index_sheet_fixture, cell_fixture):
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    uuid_cell, _, _, _, _, _ = cell_fixture
    uuid_cell.value = "A-B-C-D"
    jira_cell = uuid_cell
    jira_cell.value = None

    @patch("uuid_module.helper.get_cell_data", return_value=jira_cell)
    @patch("uuid_module.helper.get_cell_data", return_value=uuid_cell)
    def test_0(mock_0, mock_1):
        sub_index_dict, sub_index_list = \
            create_jira_tickets.build_sub_indexes(index_sheet, index_col_map)
        return sub_index_dict, sub_index_list

    result_0, result_1 = test_0()
    assert isinstance(result_0, dict)
    assert isinstance(result_1, list)


def test_form_rows_0(row_fixture, index_sheet_fixture, sheet_fixture):
    _, col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows("row_dict", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.form_rows(row_dict, "index_col_map")
    with pytest.raises(ValueError):
        empty_row_dict = {}
        create_jira_tickets.form_rows(empty_row_dict, index_col_map)
    with pytest.raises(ValueError):
        empty_index_col_map = {}
        create_jira_tickets.form_rows(row_dict, empty_index_col_map)


def test_form_rows_1(row_fixture, index_sheet_fixture, sheet_fixture):

    _, col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0


def test_form_rows_2(row_fixture, index_sheet_fixture, sheet_fixture):

    _, col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    row_dict[row.id]['Jira Ticket'] = "Create"
    row_dict[row.id]['Inject'] = True
    row_dict[row.id]['KTLO'] = True
    rows_to_add_1 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert isinstance(rows_to_add_1, list)
    for row in rows_to_add_1:
        assert isinstance(row, smartsheet.models.row.Row)


def test_form_rows_3(row_fixture, index_sheet_fixture, sheet_fixture):

    _, col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0
    copy_0 = row_dict.copy()
    copy_0[row.id]['Jira Ticket'] = "Create"
    copy_0[row.id]['Inject'] = True
    copy_0[row.id]['KTLO'] = True
    rows_to_add_1 = create_jira_tickets.form_rows(
        copy_0, index_col_map)
    assert rows_to_add_1


def test_form_rows_4(row_fixture, index_sheet_fixture, sheet_fixture):
    _, col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture
    row, _ = row_fixture
    row_dict = {}
    row_dict[row.id] = create_jira_tickets.build_row_data(row, col_map)
    rows_to_add_0 = create_jira_tickets.form_rows(
        row_dict, index_col_map)
    assert rows_to_add_0
    copy_0 = row_dict.copy()
    copy_0[row.id]['Jira Ticket'] = "Create"
    copy_0[row.id]['Inject'] = True
    # copy_0[row.id]['KTLO'] = True
    copy_0[row.id]['Not KLTO'] = copy_0[row.id].pop('KTLO')

    rows_to_add_1 = create_jira_tickets.form_rows(
        copy_0, index_col_map)

    assert isinstance(rows_to_add_1, list)
    for row in rows_to_add_1:
        assert isinstance(row, smartsheet.models.row.Row)

    @patch.dict(index_col_map,
                {'Tasks': None})
    def test_0(mock_0):
        rows_to_add_2 = create_jira_tickets.form_rows(
            copy_0, index_col_map)
        return rows_to_add_2

    result_0 = test_0(index_col_map)
    assert result_0

    @patch.dict(row_dict, {row.id: {"Issue Type": "Epic",
                                    "Tasks": "Super Task",
                                    "Parent Issue Type": "Project",
                                    "Parent Ticket": "JAR-1234"}})
    def test_1(mock_0):
        rows_to_add_2 = create_jira_tickets.form_rows(
            row_dict, index_col_map)
        return rows_to_add_2

    result_1 = test_1(row_dict)
    assert result_1

    @patch.dict(row_dict, {row.id: {"Issue Type": "Story",
                                    "Tasks": "Super Task",
                                    "Parent Issue Type": "Epic",
                                    "Parent Ticket": "JAR-1234"}})
    def test_2(mock_0):
        rows_to_add_2 = create_jira_tickets.form_rows(
            row_dict, index_col_map)
        return rows_to_add_2

    result_2 = test_2(row_dict)
    assert result_2

    @patch.dict(row_dict, {row.id: {"Issue Type": "Story",
                                    "Tasks": "Super Task",
                                    "Parent Issue Type": "Story",
                                    "Parent Ticket": "JAR-1234"}})
    def test_3(mock_0):
        rows_to_add_2 = create_jira_tickets.form_rows(
            row_dict, index_col_map)
        return rows_to_add_2

    result_3 = test_3(row_dict)
    assert result_3


def test_get_push_tickets_sheet_0(push_tickets_sheet_fixture):
    push_tickets_sheet, push_col_map = push_tickets_sheet_fixture

    @patch("uuid_module.smartsheet_api.get_sheet",
           return_value=push_tickets_sheet)
    def test_0(mock_0):
        sheet, col_map = create_jira_tickets.get_push_tickets_sheet()
        return sheet, col_map

    result_0, result_1 = test_0()
    assert result_0 == push_tickets_sheet
    assert result_1 == push_col_map


def test_copy_jira_tickets_to_sheet_0(sheet_fixture, index_sheet_fixture):

    sheet, sheet_col_map, _, _ = sheet_fixture
    _, index_col_map, _, _ = index_sheet_fixture

    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "sheet", sheet_col_map, index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, "sheet_col_map", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, sheet_col_map, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            sheet, sheet_col_map, index_sheet_fixture, "index_col_map")


def test_copy_jira_tickets_to_sheet_1(sheet_fixture, index_sheet_fixture,
                                      cell_fixture):
    import uuid_module.create_jira_tickets as jira
    sheet, sheet_col_map, _, _ = sheet_fixture
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    basic_cell, _, _, _, _, _ = cell_fixture
    basic_cell.value = "JAR-1234"
    result = smartsheet.models.Result
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    def test_0(mock_0):
        sheets_updated = jira.copy_jira_tickets_to_sheets([sheet],
                                                          index_sheet,
                                                          index_col_map)
        return sheets_updated

    result_0 = test_0()
    assert isinstance(result_0, int)
    assert result_0 == 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.build_sub_indexes",
           return_value=[{"3027747506284420-2568506862659460-3-4": "JAR-1234"},
                         ["JAR-1234"]])
    @patch.dict(sheet_col_map, {"Tasks": 12345678900})
    def test_1(mock_0, mock_1, mock_2):
        sheets_updated = jira.copy_jira_tickets_to_sheets([sheet],
                                                          index_sheet,
                                                          index_col_map)
        return sheets_updated

    result_1 = test_1(sheet_col_map)
    assert isinstance(result_1, int)
    assert result_1 == 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.build_sub_indexes",
           return_value=[{"3027747506284420-2568506862659460-3-4": "JAR-1234"},
                         ["JAR-1234"]])
    @patch.dict(sheet_col_map, {"UUID": 12344568999, "Tasks": 12345678900})
    def test_2(mock_0, mock_1, mock_2):
        sheets_updated = jira.copy_jira_tickets_to_sheets([sheet],
                                                          index_sheet,
                                                          index_col_map)
        return sheets_updated

    result_2 = test_2(sheet_col_map)
    assert isinstance(result_2, int)
    assert result_2 == 0


def test_copy_jira_tickets_to_sheet_2(sheet_fixture, index_sheet_fixture,
                                      cell_fixture):
    import uuid_module.create_jira_tickets as jira
    sheet, sheet_col_map, _, _ = sheet_fixture
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    basic_cell, _, _, _, _, _ = cell_fixture
    basic_cell.value = "JAR-1234"
    result = smartsheet.models.Result
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.build_sub_indexes",
           return_value=[{"3027747506284420-2568506862659460-3-4": "JAR-1234"},
                         ["JAR-1234"]])
    def test_3(mock_0, mock_1):
        sheets_updated = jira.copy_jira_tickets_to_sheets([sheet],
                                                          index_sheet,
                                                          index_col_map)
        return sheets_updated

    result_3 = test_3()
    assert isinstance(result_3, int)
    assert result_3 == 0


def test_link_jira_index_to_sheet_0(index_sheet_fixture, sheet_fixture):

    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "source_sheets", index_sheet, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, "index_sheet", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet, "index_col_map")


def test_link_jira_index_to_sheet_1(index_sheet_fixture,
                                    sheet_fixture):

    index_sheet, index_col_map, _, _ = index_sheet_fixture
    sheet, _, _, _, = sheet_fixture
    source_sheets = [sheet]

    @patch("uuid_module.create_jira_tickets.build_sub_indexes",
           return_value=({}, []))
    def test(mock_0):
        sheets_updated = create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet, index_col_map)
        return sheets_updated
    sheets_updated = test()
    assert sheets_updated == 0


def test_build_row_data_0(row_fixture, sheet_fixture):

    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data("row", col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.build_row_data(row, "col_map")


def test_build_row_data_1(row_fixture, sheet_fixture):

    row, _ = row_fixture
    _, col_map, _, _ = sheet_fixture
    row_data = create_jira_tickets.build_row_data(row, col_map)
    assert isinstance(row_data, dict)


def test_create_ticket_index_0(sheet_fixture, index_sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    source_sheets = [sheet, sheet, sheet, sheet]
    _, index_col_map, _, _ = index_sheet_fixture
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            "source_sheets", index_sheet_fixture, index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, "index_sheet_fixture", index_col_map)
    with pytest.raises(TypeError):
        create_jira_tickets.copy_jira_tickets_to_sheets(
            source_sheets, index_sheet_fixture, "index_col_map")


def test_create_ticket_index_1(sheet_fixture, index_sheet_fixture):

    sheet, _, _, _ = sheet_fixture
    source_sheets = [sheet]
    index_sheet, index_col_map, _, _ = index_sheet_fixture
    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    def test(mock_0):
        ticket_index = create_jira_tickets.create_ticket_index(
            source_sheets, index_sheet, index_col_map)

        return ticket_index
    ticket_index = test()
    assert isinstance(ticket_index, (dict, smartsheet.models.Sheet))


def test_create_tickets_0():

    with pytest.raises(TypeError):
        create_jira_tickets.create_tickets("minutes")
    with pytest.raises(ValueError):
        create_jira_tickets.create_tickets(-1337)


def test_create_tickets_1(workspace_fixture, sheet_fixture,
                          index_sheet_fixture):
    import app.config as config
    import uuid_module.create_jira_tickets as jira
    workspace, _ = workspace_fixture
    sheet, _, _, _ = sheet_fixture
    index_sheet, _, _, _ = index_sheet_fixture
    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.create_jira_tickets.modify_scheduler",
           return_value="message")
    @patch("uuid_module.create_jira_tickets.create_ticket_index",
           return_value={"Row": "Data"})
    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.form_rows",
           return_value=['row 1', 'row 2'])
    @patch("uuid_module.smartsheet_api.get_sheet",
           return_value=index_sheet)
    @patch("uuid_module.get_data.refresh_source_sheets",
           return_value=[sheet])
    @patch("uuid_module.smartsheet_api.get_workspace",
           return_value=workspace)
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4, mock_5, mock_6):
        result = jira.create_tickets(config.minutes)
        return result
    result = test_0()
    assert result is True


def test_create_tickets_2(workspace_fixture, sheet_fixture,
                          index_sheet_fixture):
    import app.config as config
    import uuid_module.create_jira_tickets as jira
    workspace, _ = workspace_fixture
    sheet, _, _, _ = sheet_fixture
    index_sheet, _, _, _ = index_sheet_fixture
    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.create_jira_tickets.modify_scheduler",
           return_value="message")
    @patch("uuid_module.create_jira_tickets.create_ticket_index",
           return_value={})
    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.create_jira_tickets.form_rows",
           return_value=['row 1', 'row 2'])
    @patch("uuid_module.smartsheet_api.get_sheet",
           return_value=index_sheet)
    @patch("uuid_module.get_data.refresh_source_sheets",
           return_value=[sheet])
    @patch("uuid_module.smartsheet_api.get_workspace",
           return_value=workspace)
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4, mock_5, mock_6):
        result = jira.create_tickets(config.minutes)
        return result
    result_0 = test_0()
    assert result_0 is False


def test_modify_scheduler_0():
    import uuid_module.create_jira_tickets as jira
    with pytest.raises(TypeError):
        jira.modify_scheduler("1337")
    with pytest.raises(ValueError):
        jira.modify_scheduler(-1337)


def test_modify_scheduler_1():
    import uuid_module.create_jira_tickets as jira
    import app.config as config

    def test_0():
        config.scheduler.add_job(jira.create_tickets,
                                 'interval',
                                 args=[config.minutes],
                                 minutes=2,
                                 id="create_jira_interval")
        result = jira.modify_scheduler(30.567)
        config.scheduler.remove_all_jobs()
        return result
    result_0 = test_0()
    assert isinstance(result_0, str)
    assert "Job interval is 1 minute(s) longer than the job " in result_0
    assert "runtime. Reduced interval to 1 minutes" in result_0


def test_modify_scheduler_2():
    import uuid_module.create_jira_tickets as jira
    import app.config as config

    def test_0():
        config.scheduler.add_job(jira.create_tickets,
                                 'interval',
                                 args=[config.minutes],
                                 minutes=2,
                                 id="create_jira_interval")
        result = jira.modify_scheduler(120)
        config.scheduler.remove_all_jobs()
        return result
    result_0 = test_0()
    assert isinstance(result_0, str)
    assert "Job interval and job runtime are within 1 minute of " in result_0
    assert "each other. No changes to interval." in result_0


def test_modify_scheduler_3():
    import uuid_module.create_jira_tickets as jira
    import app.config as config

    def test_0():
        config.scheduler.add_job(jira.create_tickets,
                                 'interval',
                                 args=[config.minutes],
                                 minutes=2,
                                 id="create_jira_interval")
        result = jira.modify_scheduler(179)
        config.scheduler.remove_all_jobs()
        return result
    result_0 = test_0()
    assert isinstance(result_0, str)
    assert result_0 == "New job interval set to 3 minutes"


def test_copy_uuid_to_index_sheet_0(index_sheet_fixture):
    # TypeError / ValueError
    pass


def test_copy_uuid_to_index_sheet_1(index_sheet_fixture):
    #
    # index_sheet, index_col_map = index_sheet_fixture
    # @patch("uuid_module.create_jira_tickets.build_sheet_sub_inded",
    #    return_value={})
    # def test_0(mock_0):
    # result = copy_uuid_to_index_sheet(index_sheet, index_col_map)
    # assert result is False
    pass


def test_copy_uuid_to_index_sheet_2(index_sheet_fixture):
    #
    # index_sheet, index_col_map = index_sheet_fixture
    # @patch("uuid_module.create_jira_tickets.build_sheet_sub_inded",
    #    return_value={})
    # def test_0(mock_0):
    # result = copy_uuid_to_index_sheet(index_sheet, index_col_map)
    # assert result is True
    pass


def test_copy_errors_to_sheet_0(sheet_fixture, push_tickets_sheet_fixture,
                                row_fixture):
    import uuid_module.create_jira_tickets as jira
    sheet, col_map, _, _ = sheet_fixture
    push_tickets_sheet, push_col_map = push_tickets_sheet_fixture
    row, _ = row_fixture
    cell_0 = None

    result = smartsheet.models.Result()
    result.message = "SUCCESS"
    result.result_code = 0

    @patch("uuid_module.smartsheet_api.write_rows_to_sheet",
           return_value=result)
    @patch("uuid_module.smartsheet_api.get_row", return_value=row)
    @patch("uuid_module.helper.get_column_map", return_value=col_map)
    @patch("uuid_module.smartsheet_api.get_sheet", return_value=sheet)
    @patch("uuid_module.helper.get_cell_data", return_value=cell_0)
    @patch("uuid_module.create_jira_tickets.get_push_tickets_sheet",
           return_value=[push_tickets_sheet, push_col_map])
    def test_0(mock_0, mock_1, mock_2, mock_3, mock_4, mock_5):
        success_count, failure_count, skip_count = jira.copy_errors_to_sheet()
        return success_count, failure_count, skip_count

    result_0, result_1, result_2 = test_0()
    assert isinstance(result_0, int)
    assert isinstance(result_1, int)
    assert isinstance(result_2, int)
