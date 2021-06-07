import logging
import json
import math

logger = logging.getLogger(__name__)


def get_cell_data(row, column_name, column_map):
    """Gets the cell data from a row via column name

    Args:
        row (Row): The row of data that contains the IDs
        column_name (str): The name of the referenced column
        column_map (dict): The map of Column Name: Column ID

    Returns:
        int: The column ID
    """
    try:
        column_id = column_map[column_name]
    except KeyError:
        logging.debug("Column not found: " + str(column_name))
        return None
    else:
        return row.get_column(column_id)


def get_column_map(sheet):
    """Creates a map of column names to column IDs

    Args:
        sheet (sheet): The sheet containing column names and IDs

    Returns:
        dict: A map of Column Name: Column ID
    """
    column_map = {}
    for column in sheet.columns:
        column_map[column.title] = column.id
    return column_map


def has_cell_link(old_cell, direction):
    """Helper function to determine if an existing cell already has a cell
       link.

    Args:
        old_cell (Cell): The Cell object to check.
        direction (str): Whether to check incoming or outgoing cell links.

    Returns:
        str: "Linked" if status is "OK", "Broken" if staus is "BROKEN",
             None if the cell doesn't have a value and "Unlinked" if the
             cell doesn't have a cell link property. If the cell link
             type is 'linksOutToCells' always return "Linked".
    """
    cell_json = json.loads(str(old_cell))
    if direction == "In":
        try:
            linked_cell = cell_json['linkInFromCell']
            status = linked_cell['status']
            if status == 'OK':
                return "Linked"
            elif status == 'BROKEN':
                return "Broken"
        except KeyError:
            if old_cell.value is None:
                return None
            return "Unlinked"
    elif direction == "Out":
        try:
            linked_cell = cell_json['linksOutToCells']
            return "Linked"
        except KeyError:
            if old_cell.value is None:
                return None
            return "Unlinked"


def get_cell_value(row, col_name, col_map):
    """
    Get the value of the cell or return None
    """
    cell = get_cell_data(row, col_name, col_map)
    if cell is None or cell.value is None:
        try:
            msg = str("Cell is {} or cell value is {}. "
                      "Returning 'None'").format(cell, cell.value)
        except AttributeError:
            msg = str("Cell is {}. Returning 'None'"
                      "").format(cell)

        logging.debug(msg)
        return None
    else:
        return str(cell.value)


def json_extract(obj, key):
    """
    Recursively fetch values from nested JSON.
    """
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
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor
