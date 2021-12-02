import json
import os

import pytest
import smartsheet
import datetime
from freezegun import freeze_time
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, has_cell_link, json_extract,
                                truncate, chunks)

true = True
false = False
null = None

cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def sheet():
    with open(cwd + '/sheet.json') as f:
        sheet_json = json.load(f)
    sheet = smartsheet.models.Sheet(sheet_json)
    return sheet


@pytest.fixture
def row():
    with open(cwd + '/row.json') as f:
        row_json = json.load(f)
    row = smartsheet.models.Row(row_json)
    return row


@pytest.fixture
def cell():
    with open(cwd + '/cell.json') as f:
        cell_json = json.load(f)
    cell = smartsheet.models.Cell(cell_json)
    return cell


@pytest.fixture
def col_name():
    col_name = "Benny's Adventure Team"
    return col_name


@pytest.fixture
def col_map():
    col_map = {}
    col_map["Benny's Adventure Team"] = 752133921468837
    return col_map


@pytest.fixture
def direction():
    return "In"


@pytest.fixture
def number():
    return 3.1415


@pytest.fixture
def decimals():
    return 3


@pytest.fixture
def obj():
    with open(cwd + '/cell.json') as f:
        cell_json = json.load(f)
    return cell_json


@pytest.fixture
def key():
    return "formula"


@pytest.fixture
def simple_list():
    return [1, 2, 3, 4, 5, 6]


def test_get_cell_data(row, col_name, col_map):
    with pytest.raises(TypeError):
        get_cell_data("Row", col_name, col_map)
    with pytest.raises(TypeError):
        get_cell_data(row, 1, col_map)
    with pytest.raises(TypeError):
        get_cell_data(row, col_name, "col_map")
    with pytest.raises(KeyError):
        keyerror_col_map = {}
        keyerror_col_map["Jira Issue"] = "JAR-1234"
        get_cell_data(row, col_name, keyerror_col_map)

    with open(cwd + '/cell.json') as f:
        cell_json = json.load(f)
    test_fixture_cell_data = smartsheet.models.Cell(cell_json)
    test_cell_data = get_cell_data(row, col_name, col_map)
    assert (test_cell_data.value,
            test_cell_data.column_id,
            test_cell_data.column_type,
            test_cell_data.formula) == (
        test_fixture_cell_data.value,
        test_fixture_cell_data.column_id,
        test_fixture_cell_data.column_type,
        test_fixture_cell_data.formula)


def test_get_column_map(sheet):
    with pytest.raises(TypeError):
        get_column_map("Sheet")
    assert get_column_map(sheet) == {"Benny's Adventure Team": 752133921468837}


def test_has_cell_link(cell, direction):
    with pytest.raises(TypeError):
        has_cell_link("cell", direction)
    with pytest.raises(TypeError):
        has_cell_link(cell, 7)
    with pytest.raises(ValueError):
        has_cell_link(cell, "Sideways")
    with pytest.raises(KeyError):
        bad_cell = {
            "columnId": 752133921468837,
            "columnType": "TEXT_NUMBER",
            "displayValue": "Lumine",
            "formula": "=UUID@row",
            "hyperlink": {
                "reportId": 674477165909395,
                "sheetId": 117648125440672,
                "sightId": 859583955564213,
                "url": "https://genshin.gg"
            },
            "image": {
                "altText": "Benny's favorite food",
                "height": 25,
                "id": "937767591144840",
                "width": 25
            },
            "objectValue": {
                "objectType": "ABSTRACT_DATETIME"
            },
            "overrideValidation": true,
            "strict": true,
            "value": "Lumine"
        }
        bad_cell = smartsheet.models.Cell(bad_cell)
        has_cell_link(bad_cell, direction) == "Unlinked"
    assert has_cell_link(cell, direction) == "Linked"
    try:
        has_cell_link(bad_cell, direction)
    except KeyError as k:
        assert str(k) == str("'Unlinked'")

    try:
        has_cell_link(bad_cell, "Out")
    except KeyError as k:
        assert str(k) == str("'Unlinked'")


def test_get_cell_value(row, col_name, col_map):
    with pytest.raises(TypeError):
        get_cell_value("Row", col_name, col_map)
    with pytest.raises(TypeError):
        get_cell_value(row, 1, col_map)
    with pytest.raises(TypeError):
        get_cell_value(row, col_name, "col_map")
    assert get_cell_value(row, col_name, col_map) == "Lumine"


def test_json_extract(obj, key):
    with pytest.raises(TypeError):
        json_extract("String", -1)
    with pytest.raises(TypeError):
        json_extract(obj, -1)
    assert json_extract(obj, key) == ["=UUID@row"]


def test_truncate(number, decimals):
    with pytest.raises(TypeError):
        truncate("Benny's Adventure Team", 4)
    with pytest.raises(TypeError):
        truncate(number, "decimals")
    with pytest.raises(ValueError):
        truncate(number, -1)
    assert truncate(number, decimals) == 3.141


@freeze_time("2012-01-14 12:13:00")
def test_get_timestamp(decimals):
    with pytest.raises(TypeError):
        get_timestamp("number")
    with pytest.raises(ValueError):
        get_timestamp(-5)
    modified_since, modified_since_iso = get_timestamp(decimals)
    assert datetime.datetime.now() == datetime.datetime(2012, 1, 14, 12, 13, 0)
    assert modified_since == datetime.datetime(
        2012, 1, 14, 12, 10, 00)  # "2012-01-14T12:10:00"
    assert modified_since_iso == datetime.datetime(
        2012, 1, 14, 12, 10, 00).isoformat()  # "2012-01-14T12:10:00"


def test_chunks(simple_list, decimals):
    with pytest.raises(TypeError):
        for i in chunks("simple_list", 3):
            pass
    with pytest.raises(TypeError):
        for i in chunks(simple_list, "Four"):
            pass
    with pytest.raises(ValueError):
        for i in chunks(simple_list, -1):
            pass
    with pytest.raises(ValueError):
        for i in chunks(simple_list, 0):
            pass
    with pytest.raises(ValueError):
        for i in chunks(simple_list, 10):
            pass
    for i in chunks(simple_list, decimals):
        assert len(i) == 3
