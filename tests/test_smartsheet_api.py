import json
import os
import logging
import pytest
import smartsheet
from uuid_module.smartsheet_api import (get_row, get_sheet, get_workspace,
                                        write_rows_to_sheet)
from uuid_module.variables import dev_minutes
from uuid_module.helper import get_secret, get_secret_name
cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def sheet():
    with open(cwd + '/dev_program_plan.json') as f:
        sheet_json = json.load(f)
    sheet = smartsheet.models.Sheet(sheet_json)
    return sheet


@pytest.fixture
def row():
    with open(cwd + '/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


def test_write_rows_to_sheet(row, sheet):
    rows_to_write = [row]
    with pytest.raises(TypeError):
        write_rows_to_sheet("rows_to_write", sheet)
    with pytest.raises(TypeError):
        write_rows_to_sheet(rows_to_write, "sheet")
    with pytest.raises(TypeError):
        write_rows_to_sheet(rows_to_write, sheet, write_method=1)
    with pytest.raises(ValueError):
        write_rows_to_sheet([], sheet)


def test_get_workspace():
    with pytest.raises(TypeError):
        get_workspace("workspace_id")


def test_get_sheet(sheet):
    sheet_id = sheet.id
    with pytest.raises(TypeError):
        get_sheet("sheet_id", minutes=dev_minutes)
    with pytest.raises(TypeError):
        get_sheet(sheet_id, minutes="dev_minutes")


def test_get_row(sheet, row):
    sheet_id = sheet.id
    row_id = row.id
    with pytest.raises(TypeError):
        get_row("sheet_id", row_id)
    with pytest.raises(TypeError):
        get_row(sheet_id, "row_id")
