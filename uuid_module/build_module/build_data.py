import logging
import os
from collections import defaultdict

from uuid_module import has_cell_link, get_column_id
from uuid_module.variables import jira_col

# jira_col = os.getenv('JIRA_COL')

logger = logging.getLogger(__name__)

# Helper function to pass in data to create a cell and cell link


def build_linked_cell(jira_index_sheet, jira_index_col_map, dest_col_map,
                      idx_row_id, colunn, smartsheet_client):
    new_cell_link = smartsheet_client.models.CellLink()
    new_cell_link.sheet_id = jira_index_sheet.id
    new_cell_link.row_id = int(idx_row_id)
    new_cell_link.column_id = int(jira_index_col_map[colunn])

    new_cell = smartsheet_client.models.Cell()
    new_cell.column_id = int(dest_col_map[colunn])
    new_cell.value = smartsheet_client.models.ExplicitNull()
    new_cell.link_in_from_cell = new_cell_link

    return new_cell


# Helper function to create indexes on the destination
# sheet and rows. Faster than pulling sheet data from the
# API because we already have the data from the
# project_data dictionary
# Returns a list of destination sheet IDs and a list of
# destination row IDs.
# project_data is a dict from the get_all_row_data function
def dest_indexes(project_data):
    dest_sheet_index = defaultdict(list)
    # dest_row_index = defaultdict(list)
    for uuid, ticket in project_data.items():
        dest_sheet_id = uuid.split("-")[0]
        # dest_row_id = uuid.split("-")[1]
        dest_sheet_index[dest_sheet_id].append(ticket)
        # dest_row_index[dest_row_id].append(ticket)
    return dest_sheet_index,  # dest_row_index


# Function to build new cell links, unlink broken links, or do
# nothing if the cell link status is "OK". Used to remove
# unchanged rows from the update list.
# Returns new_row if any cells need to be linked or unlinked
# Returns None if no action needed
def build_row(row, columns_to_link, dest_col_map, jira_index_sheet,
              jira_index_col_map, idx_row_id, smartsheet_client):
    new_row = smartsheet_client.models.Row()
    new_row.id = row.id
    for col in columns_to_link:
        old_cell = get_column_id(row, col, dest_col_map)
        cell_check = has_cell_link(old_cell, 'In')
        if cell_check == "Linked":
            msg = str("Valid cell link: RowID {} | ColName {} | "
                      "Cell Value {}").format(row.id, col,
                                              old_cell.link_in_from_cell)
            logging.debug(msg)
        elif cell_check == "Unlinked":
            link_cell = build_linked_cell(jira_index_sheet,
                                          jira_index_col_map,
                                          dest_col_map,
                                          idx_row_id,
                                          col,
                                          smartsheet_client)
            new_row.cells.append(link_cell)
            msg = "No Cell Link: Row ID {} | ColName {} | Cell link {}".format(
                row.id, col, link_cell.link_in_from_cell)
            logging.debug(msg)
        elif cell_check == "Broken":
            unlink_cell = smartsheet_client.models.Cell()
            unlink_cell.id = int(dest_col_map[col])
            unlink_cell.value = old_cell.value
            new_row.cells.append(unlink_cell)
            msg = str("Broken Cell Link: Row ID {} | ColName {} | "
                      "Cell link {}".format(row.id, col,
                                            unlink_cell.link_in_from_cell))
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
