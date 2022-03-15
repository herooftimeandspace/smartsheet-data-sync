import json
from unittest.mock import patch
from pathlib import Path

import pytest
import smartsheet
import uuid_module.helper as helper

_, cwd = helper.get_local_paths()
p = Path(cwd)
up_one_dir = p.parent


@pytest.fixture
def sheet():
    with open(str(up_one_dir) + '/test_fixtures/dev_program_plan.json') as f:
        sheet_json = json.load(f)
    sheet = smartsheet.models.Sheet(sheet_json)

    return sheet


@pytest.fixture
def row():
    with open(up_one_dir + 'test_fixtures/dev_program_plan_row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_copy_sheet(sheet):
    response = smartsheet_client.Sheets.copy_sheet(
        sheet.id,
        smartsheet.models.ContainerDestination({
            'destination_type': 'folder',
            'destination_id': 8062773914560388,
            'new_name': 'Program Plan Integration Test'
        })
    )
    assert response["message"] == "SUCCESS"
