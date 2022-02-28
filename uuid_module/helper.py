import base64
import json
import logging
import math
from datetime import datetime, timedelta
import smartsheet
import app.config as config


from uuid_module.variables import (dev_jira_idx_sheet, dev_minutes,
                                   dev_push_jira_tickets_sheet,
                                   dev_workspace_id, prod_jira_idx_sheet,
                                   prod_minutes, prod_push_jira_tickets_sheet,
                                   prod_workspace_id)

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
        KeyError: Raises KeyError if the column name isn't in the dictionary

    Returns:
        cell (Cell): A Cell object or None if the column is not found in the
                     map.
    """
    if not isinstance(row, smartsheet.models.row.Row):
        raise TypeError("Row is not a Smartsheet Row type object")
    elif not isinstance(column_name, str):
        raise TypeError("Column name must be a string")
    elif not isinstance(column_map, dict):
        raise TypeError("Column Map must be a dict of ColNames:ColIDs")

    try:
        column_id = column_map[column_name]
    except KeyError:
        msg = str("Column not found: {}").format(column_name)
        logging.debug(msg)
        raise KeyError(msg)
        # return None
    else:
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
        err = str("Sheet must be a Smartsheet Sheet object,"
                  "not {}").format(type(sheet))
        raise TypeError(err)

    column_map = {}
    for column in sheet.columns:
        column_map[column.title] = column.id
    return column_map


def has_cell_link(old_cell, direction):
    """Determine if an existing cell already has a cell link, which direction
       and whether it needs to be repaired. Returning None currently disabled
       because it caused the script to skip valid cells that should have been
       linked.

    Args:
        old_cell (Cell): The Cell object to check.
        direction (str): Whether to check incoming or outgoing cell links.

    Raises:
        TypeError: Validates old_cell is a Smartsheet cell object
        TypeError: Validates direction is a string
        ValueError: Validates direction is either 'In' or 'Out'
        KeyError: If the old_cell doesn't have the extended attributes for
                  cell links raises as 'Unlinked'

    Returns:
        str: "Linked" if status is "OK", "Broken" if staus is "BROKEN",
             "Unlinked" if the cell doesn't have a cell link property. If the
             cell link type is 'linksOutToCells', always return "Linked".
    """
    if not isinstance(old_cell, smartsheet.models.cell.Cell):
        msg = str("Old Cell should be type: Cell not type: {}"
                  "").format(type(old_cell))
        raise TypeError(msg)
    if not isinstance(direction, str):
        msg = str("Direction should type: str not type: {}"
                  "").format(type(direction))
        raise TypeError(msg)
    if direction not in ("In", "Out"):
        msg = str("Direction should be either 'In' or 'Out' not '{}'"
                  "").format(direction)
        raise ValueError(msg)

    # Load the cell values as a json object
    cell_json = json.loads(str(old_cell))

    if direction == "In":
        # Check the status of the link.
        try:
            linked_cell = cell_json['linkInFromCell']
        except KeyError:
            return "Unlinked"

        status = linked_cell['status']
        return status
        # if status == 'OK':
        #     return "Linked"
        # elif status == 'BROKEN':
        #     return "Broken"
    elif direction == "Out":
        # Always set to Linked if the value exists, unless it's invalid.
        try:
            linked_cell = cell_json['linksOutToCells']
            return "Linked"
        except KeyError:
            return "Unlinked"
    else:
        return None


def get_cell_value(row, col_name, col_map):
    """
    Get the value of the cell or return None

    Args:
        row (Row): The row of data that contains the IDs
        col_name (str): The name of the referenced column
        col_map (dict): The map of Column Name: Column ID

    Raises:
        TypeError: Validates row is a Smartsheet Row object
        TypeError: Validates col_name is a string
        TypeError: Validates col_map is a dict

    Returns:
        str: The value of the cell.
        none: If the cell doesn't exist or has a null value.
    """

    # Validate data types.
    if not isinstance(row, smartsheet.models.row.Row):
        raise TypeError("Row is not a Smartsheet Row type object")
    elif not isinstance(col_name, str):
        raise TypeError("Column name must be a string")
    elif not isinstance(col_map, dict):
        raise TypeError("Column Map must be a dict of ColNames:ColIDs")

    try:
        cell = get_cell_data(row, col_name, col_map)
    except KeyError:
        cell = None
    if cell is None or cell.value is None:
        msg = str("Cell is 'None' or cell value is 'None'. "
                  "Returning 'None'").format()
        logging.debug(msg)
        return None
    else:
        return str(cell.value)


def json_extract(obj, key):
    """Recursively fetch values from nested JSON.

    Args:
        obj (json): The JSON object to pars through
        key (str): The key to search for

    Raises:
        TypeError: If the objects passed in aren't a dict or string,
                   respectively.

    Returns:
        str: The value if a key matches inside the obj JSON
    """

    # Validate data types before attempting to process.
    if not isinstance(obj, dict):
        raise TypeError("Obj must be a dict (json).")
    if not isinstance(key, str):
        raise TypeError("Key must be a string.")

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
        TypeError: Validates the number is actually a number.
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
        TypeError: Validates source is a list
        TypeError: Validates n is an int
        ValueError: Validates n must be non-zero
        ValueError: Validates n > 0
        ValueError: Validates length of list is greater than n

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
    if n == 0:
        msg = str("Second argument must be non-zero, not {}"
                  "").format(type(n))
        raise ValueError(msg)
    if n < 0:
        msg = str("Second argument must be greater than zero, not {}"
                  "").format(type(n))
        raise ValueError(msg)
    if len(source) < n:
        msg = str("Length of list is less than the chunk integer. "
                  "List length: {}, chunk size: {}").format(len(source), n)
        raise ValueError(msg)

    for i in range(0, len(source), n):
        yield source[i:i + n]
