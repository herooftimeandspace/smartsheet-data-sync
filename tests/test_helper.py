import json
import os

import pytest
import smartsheet
import datetime
from freezegun import freeze_time
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, has_cell_link, json_extract,
                                truncate, chunks, get_secret, get_secret_name)
import logging

true = True
false = False
null = None

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


@pytest.fixture
def cell():
    with open(cwd + '/dev_cell_with_url_and_incoming_link.json') as f:
        cell_json = json.load(f)
    cell = smartsheet.models.Cell(cell_json)
    return cell


@pytest.fixture
def col_name():
    col_name = "Tasks"
    return col_name


@pytest.fixture
def col_map():
    col_map = {
        'Actual Inject LoE': 482457047852932,
        'Actual Planned LoE': 4986056675223428,
        'Allocation %': 5760112861177732,
        'Assigned To': 1256513233807236,
        'Change': 763932024563588,
        'Child Projects': 4141631745091460,
        'Comments': 8011912674862980,
        'Confidence': 6111956582066052,
        'Created': 7660068953974660,
        'Current Quarter': 8785968860817284,
        'Description': 2171306908116868,
        'Duration': 8926706349172612,
        'Estimated Inject LoE': 2734256861538180,
        'Estimated LoE': 1608356954695556,
        'Estimated Planned LoE': 7237856488908676,
        'Finish': 4634212954335108,
        'Hierarchy': 8363756395751300,
        'Initiative': 5267531651934084,
        'Inject': 5549006628644740,
        'Issue Type': 4877680976914308,
        'Jira Sync': 6956381512198020,
        'Jira Ticket': 6886012768020356,
        'KTLO': 6817156137543556,
        'Launch Calendar': 2452781884827524,
        'Launch Date Row': 1045407001274244,
        'Level': 7519331465619332,
        'LoE': 4423106721802116,
        'Modified': 2030569419761540,
        'Modified Copy': 6534169047132036,
        'Next Quarter Task': 200982071142276,
        'Parent': 6393431558776708,
        'Parent Issue Type': 633554282538884,
        'Parent Team': 3578681791670148,
        'Parent Ticket': 374081349543812,
        'ParentUUID': 5830481605355396,
        'Predecessors': 3508313047492484,
        'Priority': 8082281419040644,
        'Program': 3015731838248836,
        'Project Key': 1326881977984900,
        'Quarter': 2382413140649860,
        'Quarter Rollup': 4704581698512772,
        'RowID': 3156469326604164,
        'Start': 130613326964612,
        'Status': 3297206814959492,
        'Summary': 4282369233446788,
        'Tasks': 7800806442329988,
        'Team': 6674906535487364,
        'UUID': 8645231372461956,
        'Year': 1889831931406212,
        '← Hide Everything to the Left': 3860156768380804,
    }
    return col_map


@pytest.fixture
def bad_cell():
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
    return bad_cell


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
def json_extract_fixture():
    with open(cwd + '/dev_cell_with_formula.json') as f:
        cell_json = json.load(f)
    return cell_json, "formula"


@pytest.fixture
def simple_list():
    return [1, 2, 3, 4, 5, 6]


@pytest.fixture
def env_fixture():
    return "--debug"


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

    with open(cwd + '/dev_cell_basic.json') as f:
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


def test_get_column_map(sheet, col_map):
    with pytest.raises(TypeError):
        get_column_map("Sheet")
    assert get_column_map(sheet) == col_map


def test_has_cell_link(cell, bad_cell, direction):
    with pytest.raises(TypeError):
        has_cell_link("cell", direction)
    with pytest.raises(TypeError):
        has_cell_link(cell, 7)
    with pytest.raises(ValueError):
        has_cell_link(cell, "Sideways")
    assert has_cell_link(cell, direction) == "OK"
    assert has_cell_link(bad_cell, direction) is "Unlinked"
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
    assert get_cell_value(
        row, col_name, col_map) == "Finalize resource / Scope impact"


def test_json_extract(json_extract_fixture):
    obj, key = json_extract_fixture
    with pytest.raises(TypeError):
        json_extract("String", -1)
    with pytest.raises(TypeError):
        json_extract(obj, -1)
    assert json_extract(obj, key) == ["=IFERROR(PARENT(UUID@row), \"\")"]


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


def test_get_secret(env_fixture):
    secret_name = get_secret_name(env_fixture)
    assert secret_name == "staging/smartsheet-data-sync/svc-api-token"
    retrieved_secret = get_secret(secret_name)
    assert retrieved_secret == os.environ["SMARTSHEET_ACCESS_TOKEN"]


def test_get_secret_name(env_fixture):
    with pytest.raises(TypeError):
        actual = get_secret_name(1)
    with pytest.raises(ValueError):
        actual = get_secret_name("--super_secret")

    expected = "staging/smartsheet-data-sync/svc-api-token"
    actual = get_secret_name(env_fixture)
    assert expected == actual
