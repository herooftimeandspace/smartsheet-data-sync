import logging
import math
import os
from datetime import datetime, timedelta
from pathlib import Path

import smartsheet

logger = logging.getLogger(__name__)


def get_cell_data(row, column_name, column_map):
    """Gets the cell data from a row via column name

    Args:
        row (Row): The row of data that contains the IDs
        column_name (str): The name of the referenced column
        column_map (dict): The map of Column Name: Column ID

    Raises:
        TypeError: Validates row is a Smartsheet Row object
        TypeError: Validates column_name is a string
        TypeError: Validates column_map is a dict
        ValueError: Column map must not be empty
        TypeError: Column map keys must be type str
        TypeError: Column map values must be type int
        ValueError: Column map values must be positive integers
        KeyError: Column Name must exist in the column map

    Returns:
        cell (Cell): A Cell object or None if the column is not found in the
                     map.
    """
    if not isinstance(row, smartsheet.models.row.Row):
        raise TypeError("Row is not a Smartsheet Row type object")
    if not isinstance(column_name, str):
        raise TypeError("Column name must be a string")
    if not isinstance(column_map, dict):
        raise TypeError("Column Map must be a dict of ColNames:ColIDs")
    if not column_map:
        raise ValueError("Column Map must not be empty.")
    for k, v in column_map.items():
        if not isinstance(k, str):
            raise TypeError("Column map keys must be type: str")
        if not isinstance(v, int):
            raise TypeError("Column IDs must be type: int")
        if not v > 0:
            raise ValueError("Column IDs must be a positive integer")
    if column_name not in column_map.keys():
        msg = str("Column not found: {}").format(column_name)
        raise KeyError(msg)

    column_id = column_map[column_name]
    return row.get_column(column_id)


def get_column_map(sheet):
    """Creates a map of column names to column IDs

    Args:
        sheet (sheet): The sheet containing column names and IDs

    Raises:
        TypeError: Validates sheet is a Smartsheet Sheet object

    Returns:
        dict: A map of Column Name: Column ID
    """
    if not isinstance(sheet, smartsheet.models.sheet.Sheet):
        msg = str("Sheet must be a Smartsheet Sheet object,"
                  "not {}").format(type(sheet))
        raise TypeError(msg)

    column_map = {}
    for column in sheet.columns:
        column_map[column.title] = column.id
    return column_map


def has_cell_link(old_cell, direction, **kwargs):
    """Determine if an existing cell already has a cell link, which direction
       and whether it needs to be repaired. If kwargs are passed when
       direction is set to 'Out', validates that the sheet_id and row_id passed
       in kwargs match a sheet.id and row.id in the links_out_to_cells
       object_value. If kwargs are invalid, re-runs the function without
       the kwargs.

    Args:
        old_cell (Cell): The Cell object to check.
        direction (str): Whether to check incoming or outgoing cell links.

    Raises:
        TypeError: old_cell must be a Smartsheet cell object
        TypeError: Direction must be a str
        ValueError: Direction must be either 'In' or 'Out', case-sensitive
        TypeError: Kwargs passed must be dict or None
        TypeError: Kwarg names must be str
        TypeError: Kwarg values must be int

    Returns:
        str: Returns the status of the cell link if the value exists. Returns
             "Unlinked" if the link_in_to_cell or links_out_to_cells properties
             return AttributeError or IndexError
    """
    if not isinstance(old_cell, smartsheet.models.cell.Cell):
        msg = str("Old Cell should be type: Cell not type: {}"
                  "").format(type(old_cell))
        raise TypeError(msg)
    if not isinstance(direction, str):
        msg = str("Direction should type: str not type: {}"
                  "").format(type(direction))
        raise TypeError(msg)
    if not isinstance(kwargs, (dict, type(None))):
        msg = str("Keyword Args should be type: dict or None not type: {}"
                  "").format(type(kwargs))
        raise TypeError(msg)
    if isinstance(kwargs, dict):
        for k, v in kwargs.items():
            if not isinstance(k, str):
                msg = str("Keyword Args key should be type: str not type: {}"
                          "").format(type(k))
                raise TypeError(msg)
            if not isinstance(v, int):
                msg = str("Keyword Args value should be type: int not type: {}"
                          "").format(type(v))
                raise TypeError(msg)
    if direction not in ("In", "Out"):
        msg = str("Direction should be either 'In' or 'Out' not '{}'"
                  "").format(direction)
        raise ValueError(msg)

    if direction == "In":
        # Check the status of the link.
        try:
            status = old_cell.link_in_from_cell.status
            msg = str("Cell Data: Value {} | Col ID {} | \n"
                      "Link In Status {} | Linked In Sheet ID {} | "
                      "Linked In Row ID {} | Linked In Col ID {} | "
                      "Linked In Sheet Name {}"
                      "").format(old_cell.value, old_cell.column_id,
                                 old_cell.link_in_from_cell.status,
                                 old_cell.link_in_from_cell.sheet_id,
                                 old_cell.link_in_from_cell.row_id,
                                 old_cell.link_in_from_cell.column_id,
                                 old_cell.link_in_from_cell.sheet_name)
            logging.debug(msg)
            return str(status)
        except AttributeError:
            return "Unlinked"

    if direction == "Out" and not kwargs:
        try:
            status = old_cell.links_out_to_cells[0].status
            msg = str("Cell Data: Value {} | Col ID {} | \n"
                      "Link Out Status {} | Linked Out Sheet ID {} | "
                      "Linked Out Row ID {} | Linked Out Col ID {} | "
                      "Linked Out Sheet Name {}"
                      "").format(old_cell.value, old_cell.column_id,
                                 old_cell.links_out_to_cells[0].status,
                                 old_cell.links_out_to_cells[0].sheet_id,
                                 old_cell.links_out_to_cells[0].row_id,
                                 old_cell.links_out_to_cells[0].column_id,
                                 old_cell.links_out_to_cells[0].sheet_name)
            logging.debug(msg)
            return str(status)
        except IndexError:
            return "Unlinked"

    if direction == "Out" and kwargs:
        # Check to make sure only the sheet_id and row_id kwargs were passed.
        def check_value_exist(test_dict, *values):
            return all(v in test_dict for v in values)
        result = check_value_exist(kwargs.keys(),
                                   "sheet_id", "row_id")
        if result:
            sheet_id = kwargs["sheet_id"]
            row_id = kwargs["row_id"]
        else:
            # If the wrong kwargs were passed, re-run without kwargs
            has_cell_link(old_cell, "Out")
        # Check to see if our IDs are in the link_out object
        for link in old_cell.links_out_to_cells:
            msg = str("Cell Data: Value {} | Col ID {} | \n"
                      "Link Out Status {} | Linked Out Sheet ID {} | "
                      "Linked Out Row ID {} | Linked Out Col ID {} | "
                      "Linked Out Sheet Name {} \n"
                      "Kwarg Sheet ID {} | Kwarg Row ID {}"
                      "").format(old_cell.value,
                                 old_cell.column_id, link.status,
                                 link.sheet_id, link.row_id, link.column_id,
                                 link.sheet_name, sheet_id, row_id)
            logging.debug(msg)
            if sheet_id == link.sheet_id:
                msg = str("Expected Sheet ID {} | Linked Sheet ID {}"
                          "").format(sheet_id, link.sheet_id)
                logging.debug(msg)
                sheet_match = True
            if row_id == link.row_id:
                msg = str("Expected Row ID {} | Linked Row ID {}"
                          "").format(row_id, link.row_id)
                logging.debug(msg)
                row_match = True

            if sheet_match and row_match:
                status = str(link.status)
                msg = str("Sheet ID and Row ID match Cell Link data, "
                          "breaking loop and returning {}").format(status)
                logging.debug(msg)
                break
            else:
                continue
        else:
            return "Unlinked"
        return status


def json_extract(obj, key):
    """Recursively fetch values from nested JSON.

    Args:
        obj (dict): The JSON object to pars through
        key (str): The key to search for

    Raises:
        TypeError: Obj must be a json dict
        TypeError: Key must be a str
        ValueError: Obj must not be empty
        ValueError: Key must not be empty

    Returns:
        str: The value if a key matches inside the obj JSON
    """

    # Validate data types before attempting to process.
    if not isinstance(obj, dict):
        raise TypeError("Obj must be a dict (json).")
    if not isinstance(key, str):
        raise TypeError("Key must be a string.")
    if not obj:
        raise ValueError("'Obj' must not be empty")
    if not key:
        raise ValueError("'Key' must not be empty")

    # Create an empty list as an 'array'
    arr = []

    def extract(obj, arr, key):
        # Recursively search for values of key in JSON tree.
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def truncate(number, decimals=0):
    """Return a value truncated to a specific number of decimal places.

    Args:
        number (int): The number to truncate
        decimals (int, optional): The number of decimal places to truncate.
                                  Defaults to 0.

    Raises:
        TypeError: Number must be a float
        TypeError: Decimals must be an int
        ValueError: Validates that the decimal is 0 or more.

    Returns:
        int: The number, truncated to the number of decimal places.
    """

    # Validate data types before attempting to process.
    if not isinstance(decimals, int):
        msg = str("Decimal must be an int, not {}").format(type(decimals))
        raise TypeError(msg)
    if not isinstance(number, float):
        msg = str("Number must be an float, not {}").format(type(number))
        raise TypeError(msg)
    if decimals <= 0:
        msg = str("Decimal places has to be 1 or more, not {}"
                  "").format(decimals)
        raise ValueError(msg)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor


def get_timestamp(number):
    """Subtracts the number intput from the current time to generate a
       timestamp N number of minutes ago.

    Args:
        number (int): Number of seconds

    Raises:
        TypeError: Validates number is an int
        ValueError: Ensures minutes is > 0

    Returns:
        string: an ISO8601 compliant timestamp
    """
    if not isinstance(number, int):
        raise TypeError("Number of minutes must be an integer.")
    elif number <= 0:
        raise ValueError("Number of minutes must be greater than zero.")

    date = datetime.now()
    delta = timedelta(minutes=number)
    modified_since = date - delta
    modified_since = modified_since.replace(microsecond=0)  # .isoformat()
    modified_since_iso = modified_since.replace(microsecond=0).isoformat()
    return modified_since, modified_since_iso


def chunks(source, n):
    """Yield successive n-sized chunks from source.

    Args:
        source (list): The list of objects to chunk
        n (int): The number of items in the list to chunk together

    Raises:
        TypeError: Source must be a list
        TypeError: n must be an Int
        ValueError: n must be non-zero
        ValueError: n must be greater than zero
        ValueError: Length of the list must be greater than n

    Yields:
        source (list): The sub-list of chunked items
    """
    # Validate data types before attempting to process.
    if not isinstance(source, list):
        msg = str("Source must be a list, not {}").format(type(source))
        raise TypeError(msg)
    if not isinstance(n, int):
        msg = str("Second argument must be type: int, not {}"
                  "").format(type(n))
        raise TypeError(msg)
    if n <= 0:
        msg = str("Second argument must be greater than zero, not {}"
                  "").format(type(n))
        raise ValueError(msg)
    if len(source) < n:
        msg = str("Length of list is less than the chunk integer. "
                  "List length: {}, chunk size: {}").format(len(source), n)
        raise ValueError(msg)

    for i in range(0, len(source), n):
        yield source[i:i + n]


def get_local_paths():
    """Get the local path for the project so that we can redirect logging
    and test fixtures to the correct directories

    Returns:
        str: The root directory of the project
        str: THe directory where test fixtures are located in the project
    """
    cwd = os.path.dirname(os.path.abspath(__file__))
    p = Path(cwd)
    root = str(p.parent)
    fixtures_dir = p.parent
    fixtures_dir = str(str(fixtures_dir) + "/test_fixtures")
    return root, fixtures_dir
