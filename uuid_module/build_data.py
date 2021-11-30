import logging
from collections import defaultdict
from uuid_module.helper import get_cell_data, has_cell_link

logger = logging.getLogger(__name__)


def build_linked_cell(jira_index_sheet, jira_index_col_map, dest_col_map,
                      idx_row_id, colunn, smartsheet_client):
    """Helper function to build the Cell object and cell link properties

    Args:
        jira_index_sheet (Sheet object): The Sheet object where the Jira
                                         data is stored
        jira_index_col_map (dict): The column name:id map for the
                                   Jira Index sheet
        dest_col_map (dict): The column name:id map for the destination sheet
        idx_row_id (str): The row ID in the Jira Index sheet where the cell
                          link will pull data
        colunn (str): The name of the column to write to in both sheets
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        Cell: The cell object to be written back to the destination, with
              link to the Jira Index Sheet.
    """
    new_cell_link = smartsheet_client.models.CellLink()
    new_cell_link.sheet_id = jira_index_sheet.id
    new_cell_link.row_id = int(idx_row_id)
    new_cell_link.column_id = int(jira_index_col_map[colunn])

    new_cell = smartsheet_client.models.Cell()
    new_cell.column_id = int(dest_col_map[colunn])
    new_cell.value = smartsheet_client.models.ExplicitNull()
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

    Returns:
        dict: a list of destination sheet IDs and a list of
              destination row IDs.
    """
    dest_sheet_index = defaultdict(list)
    # dest_row_index = defaultdict(list)
    for uuid, ticket in project_data.items():
        if uuid is None:
            continue
        else:
            dest_sheet_id = uuid.split("-")[0]
            dest_sheet_index[dest_sheet_id].append(ticket)
    return dest_sheet_index,  # dest_row_index


def build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
              jira_index_col_map, idx_row_id, smartsheet_client):
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
        idx_row_id (str): The row ID in the Jira Index sheet where the cell
                          link will pull data
        smartsheet_client (Object): The Smartsheet client to interact
                                    with the API

    Returns:
        Row: If cells were appended to the row, returns the new row, otherwise
             returns None.
    """
    new_row = smartsheet_client.models.Row()
    new_row.id = row.id
    for col in columns_to_link:
        old_cell = get_cell_data(row, col, dest_col_map)
        try:
            cell_check = has_cell_link(old_cell, 'In')
        except KeyError as e:
            if str(e) == str("'Unlinked'"):
                cell_check = "Unlinked"
            else:
                raise KeyError

        if cell_check == "Linked":
            msg = str("Valid cell link: RowID {} | Row Number {} | "
                      "ColName {} | Cell Value {}").format(row.id,
                                                           row.row_number, col,
                                                           old_cell.
                                                           link_in_from_cell)
            logging.debug(msg)
        elif cell_check == "Unlinked":
            link_cell = build_linked_cell(jira_index_sheet,
                                          jira_index_col_map,
                                          dest_col_map,
                                          idx_row_id,
                                          col,
                                          smartsheet_client)
            new_row.cells.append(link_cell)
            msg = str("No Cell Link: Row ID {} | Row Number {} | "
                      "ColName {} | Cell link {}").format(
                row.id, row.row_number, col, link_cell.link_in_from_cell)
            logging.debug(msg)
        elif cell_check == "Broken":
            unlink_cell = smartsheet_client.models.Cell()
            unlink_cell.id = int(dest_col_map[col])
            unlink_cell.value = old_cell.value
            new_row.cells.append(unlink_cell)
            msg = str("Broken Cell Link: Row ID {} | Row Number {} | "
                      "ColName {} | Cell link {}".format(row.id,
                                                         row.row_number, col,
                                                         unlink_cell.
                                                         link_in_from_cell))
            logging.debug(msg)
        elif cell_check is None:
            msg = str("Cell is valid and unlinked, but is {}. Continuing "
                      "to the next cell.").format(cell_check)
            logging.debug(msg)
        else:
            logging.warning("Unknown state for cell links.")
    if new_row.cells:
        return new_row
    else:
        return None
