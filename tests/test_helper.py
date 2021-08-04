import json
from typing import Type
import pytest
import smartsheet
import os

from uuid_module.helper import (get_cell_value, get_cell_data,
                                get_column_map, has_cell_link, json_extract,
                                truncate)

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


def test_get_cell_value(row, col_name, col_map):
    with pytest.raises(TypeError):
        get_cell_value("Row", col_name, col_map)
    with pytest.raises(TypeError):
        get_cell_value(row, 1, col_map)
    with pytest.raises(TypeError):
        get_cell_value(row, col_name, "col_map")
    # with pytest.raises(AttributeError):
    #     get_cell_value(row, "Test", col_map)
    assert get_cell_value(row, col_name, col_map) == "Lumine"


def test_get_cell_data(row, col_name, col_map):
    with pytest.raises(TypeError):
        get_cell_data("Row", col_name, col_map)
    with pytest.raises(TypeError):
        get_cell_data(row, 1, col_map)
    with pytest.raises(TypeError):
        get_cell_data(row, col_name, "col_map")

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
    assert get_column_map(sheet) == {"Benny's Adventure Team": 752133921468837}


def test_has_cell_link(cell, direction):
    assert has_cell_link(cell, direction) == "Linked"


def test_json_extract(obj, key):
    with pytest.raises(TypeError):
        json_extract("String", -1)
    with pytest.raises(TypeError):
        json_extract(obj, -1)
    assert json_extract(obj, key) == ["=UUID@row"]


def test_truncate(number, decimals):
    with pytest.raises(TypeError):
        truncate("Benny's Adventure Team", 4)
    with pytest.raises(ValueError):
        truncate(obj, -1)
    assert truncate(number, decimals) == 3.141


# def test_raises_exception_on_non_string_arguments():
