import json
import logging
import os

# import smartsheet
from uuid_module.build_data import build_row, dest_indexes
from uuid_module.get_data import load_jira_index
from uuid_module.helper import (get_cell_value, get_cell_data, get_column_map,
                                json_extract)
from uuid_module.variables import (assignee_col, jira_col, jira_idx_sheet,
                                   predecessor_col, start_col, status_col,
                                   task_col, uuid_col)

logger = logging.getLogger(__name__)

project_col = "Jira Project"

"""Finds all rows with the "Sync Jira" column checked and copies specific
    rows and data to the Jira Index sheet. On next Jira Index sheet sync,
    copies the Jira ticket into the Jira Ticket column with the row
    associated with the UUID.
    """
