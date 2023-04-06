import logging
from collections import defaultdict

import smartsheet

import data_module.helper as helper

logger = logging.getLogger(__name__)


def build_linked_cell(jira_index_sheet, jira_index_col_map, dest_col_map,
                      idx_row_id, column):
    """Helper function to build the Cell object and cell link properties

    Args:
        jira_index_sheet (Sheet object): The Sheet object where the Jira
                                         data is stored
        jira_index_col_map (dict): The column name:id map for the
                                   Jira Index sheet
        dest_col_map (dict): The column name:id map for the destination sheet
        idx_row_id (int): The row ID in the Jira Index sheet where the cell
                          link will pull data
        column (str): The name of the column to write to in both sheets

    Raises:
        TypeError: Jira Index Sheet must be a Smartsheet Sheet object
        TypeError: Index Column Map must be a dict
        TypeError: Destination Column Map must be a dict
        TypeError: Index Row ID must be a string
        TypeError: Column must be a string
        ValueError: Index column map must not be empty
        ValueError: Destination column map must not be empty
        ValueError: Index Row ID must be a positive integer

    Returns:
        Cell: The cell object to be written back to the destination, with
              link to the Jira Index Sheet.
    """
    if not isinstance(jira_index_sheet, smartsheet.models.sheet.Sheet):
        msg = str("Jira Index Sheet must be type: smartsheet.models.sheet, not"
                  " {}").format(type(jira_index_sheet))
        raise TypeError(msg)
    if not isinstance(jira_index_col_map, dict):
        msg = str("Jira Index column map must be type: dict, not"
                  " {}").format(type(jira_index_col_map))
        raise TypeError(msg)
    if not isinstance(dest_col_map, dict):
        msg = str("Destination column map must be type: dict, not"
                  " {}").format(type(jira_index_sheet))
        raise TypeError(msg)
    if not isinstance(idx_row_id, int):
        msg = str("Jira Index Row ID must be type: int, not"
                  " {}").format(type(idx_row_id))
        raise TypeError(msg)
    if not isinstance(column, str):
        msg = str("Column must be type: str, not"
                  " {}").format(type(column))
        raise TypeError(msg)
    if not jira_index_col_map:
        msg = str("Jira Index column map must not be empty."
                  "").format()
        raise ValueError(msg)
    if not dest_col_map:
        msg = str("Destination Sheet column map must not be empty."
                  "").format()
        raise ValueError(msg)
    if not idx_row_id > 0:
        msg = str("Jira Index row ID must not be zero or negative."
                  "").format()
        raise ValueError(msg)

    new_cell_link = smartsheet.models.CellLink()
    new_cell_link.sheet_id = jira_index_sheet.id
    new_cell_link.row_id = idx_row_id
    new_cell_link.column_id = int(jira_index_col_map[column])

    new_cell = smartsheet.models.Cell()
    new_cell.column_id = int(dest_col_map[column])
    new_cell.value = smartsheet.models.ExplicitNull()
    new_cell.link_in_from_cell = new_cell_link

    return new_cell


def dest_indexes(project_data):
    """Helper function to create indexes on the destination sheet
       and rows. Faster than pulling data from the API because the app
       already has the data from the project_data dictionary

    Args:
        project_data (dict): The dictionary with all project rows
                             and relevant data from the
                             get_all_row_data function.

    Raises:
        TypeError: Project data must be a dict

    Returns:
        dict: a list of destination sheet IDs and a list of
              destination row IDs.
    """
    if not isinstance(project_data, dict):
        msg = str("Project data must be type: dict, not"
                  " {}").format(type(project_data))
        raise TypeError(msg)

    dest_sheet_index = defaultdict(list)
    # dest_row_index = defaultdict(list)
    for uuid, ticket in project_data.items():
        if uuid is None:
            continue
        else:
            dest_sheet_id = uuid.split("-")[0]
            dest_sheet_id = int(dest_sheet_id)
            # {Sheet ID (int): Jira Ticket (str)}
            dest_sheet_index[dest_sheet_id].append(ticket)
    return dest_sheet_index,  # dest_row_index


def build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
              jira_index_col_map, idx_row_id):
    """Function to build new cell links, unlink broken links, or
       do nothing if the cell link status is OK. Used to remove
       unchanged rows from the update list.

    Args:
        row (Row): The row to reference when looking up link
                   statuses.
        columns_to_link (list): List of columns that we want to
                                link together
        jira_index_sheet (Sheet object): The Sheet object where the Jira
                                         data is stored
        jira_index_col_map (dict): The column name:id map for the
                                   Jira Index sheet
        dest_col_map (dict): The column name:id map for the destination sheet
        idx_row_id (int): The row ID in the Jira Index sheet where the cell
                          link will pull data

    Raises:
        TypeError: Row must be a Smartsheet Row object
        TypeError: Columns to link must be a list of column IDs
        TypeError: Destination Column Map must be a dict of
                   Column Names: Column IDs
        TypeError: Jira Index Sheet must be a Smartsheet Sheet object
        TypeError: Jira Index Column Map must be a dict of
                   Column Names: Column IDs
        TypeError: Jira Index Row ID must be an int

    Returns:
        Row: If cells were appended to the row, returns the new row, otherwise
             returns None.
    """
    if not isinstance(row, smartsheet.models.row.Row):
        msg = str("Row must be type: smartsheet.models.row, not"
                  " {}").format(type(row))
        raise TypeError(msg)
    if not isinstance(columns_to_link, list):
        msg = str("Columns to link must be type: list, not"
                  " {}").format(type(columns_to_link))
        raise TypeError(msg)
    if not isinstance(dest_col_map, dict):
        msg = str("Destination column map must be type: dict, not"
                  " {}").format(type(jira_index_sheet))
        raise TypeError(msg)
    if not isinstance(jira_index_sheet, smartsheet.models.sheet.Sheet):
        msg = str("Jira Index Sheet must be type: smartsheet.models.sheet, not"
                  " {}").format(type(jira_index_sheet))
        raise TypeError(msg)
    if not isinstance(jira_index_col_map, dict):
        msg = str("Jira Index Column Map must be type: dict, not"
                  " {}").format(type(jira_index_col_map))
        raise TypeError(msg)
    if not isinstance(idx_row_id, int):
        msg = str("Jira Index Row ID must be type: int, not"
                  " {}").format(type(idx_row_id))
        raise TypeError(msg)

    new_row = smartsheet.models.Row()
    new_row.id = row.id
    for col in columns_to_link:
        old_cell = helper.get_cell_data(row, col, dest_col_map)
        cell_check = helper.has_cell_link(old_cell, 'In')

        if not cell_check:
            msg = str("Cell is valid and unlinked, but is {}. Continuing "
                      "to the next cell.").format(cell_check)
            logging.debug(msg)
            continue

        if cell_check in ("Linked", "OK"):
            msg = str("Valid cell link: RowID {} | Row Number {} | "
                      "ColName {} | Cell Value {}"
                      "").format(row.id, row.row_number, col,
                                 old_cell.link_in_from_cell)
            logging.debug(msg)
            continue

        if cell_check in ("Unlinked", "INVALID"):
            link_cell = build_linked_cell(jira_index_sheet,
                                          jira_index_col_map,
                                          dest_col_map,
                                          idx_row_id,
                                          col)
            new_row.cells.append(link_cell)
            msg = str("No Cell Link: Row ID {} | Row Number {} | "
                      "ColName {} | Cell link {}").format(
                row.id, row.row_number, col, link_cell.link_in_from_cell)
            logging.debug(msg)
            continue

        if cell_check in ("Broken", "BROKEN"):
            unlink_cell = smartsheet.models.Cell()
            unlink_cell.column_id = int(dest_col_map[col])
            unlink_cell.value = old_cell.value
            new_row.cells.append(unlink_cell)
            msg = str("Unlinking Broken Cell Link: Row ID {} | "
                      "Row Number {} | ColName {} | Cell link {}"
                      "").format(row.id, row.row_number, col,
                                 unlink_cell.link_in_from_cell)
            logging.debug(msg)
            continue
    if new_row.cells:
        return new_row
    else:
        return None
