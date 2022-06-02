# import json
import logging

import pytest
import smartsheet
import uuid_module.bidirectional_sync as sync
import uuid_module.helper as helper

# from unittest.mock import patch

# import uuid_module.variables as app_vars
# from freezegun import freeze_time

_, cwd = helper.get_local_paths()
logger = logging.getLogger(__name__)


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_compare_dates_0(cell_history_fixture):
    cell_history = cell_history_fixture
    with pytest.raises(TypeError):
        sync.compare_dates(cell_history, 1337)
    pass


def test_compare_dates_1(index_cell_history, plan_cell_history):
    pass


def test_rebuild_cell_0(cell, column_id):
    pass


def test_rebuild_cell_1(cell, column_id):
    pass


def test_build_row_0():
    pass


def test_build_row_1():
    pass


def test_drop_dupes_0():
    with pytest.raises(TypeError):
        sync.drop_dupes(1337)
    with pytest.raises(ValueError):
        sync.drop_dupes([])


def test_drop_dupes_1(row_fixture):
    single_row = smartsheet.models.Row()
    single_row.id = 1337
    row_list = [row_fixture, row_fixture, row_fixture, single_row]
    unique = sync.drop_dupes(row_list)
    assert unique[0].id == 1337
