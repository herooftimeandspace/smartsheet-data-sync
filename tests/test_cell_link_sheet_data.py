import json
import logging
import re

from uuid_module.helper import (chunks, get_cell_data, get_cell_value,
                                get_column_map, has_cell_link, json_extract)
from uuid_module.variables import (assignee_col, description_col, duration_col,
                                   jira_col, predecessor_col, start_col,
                                   status_col, task_col)
from uuid_module.write_data import write_predecessor_dates
import base64
import json
import logging
import os
from collections import defaultdict

import pytest
import pytz
import smartsheet
from freezegun import freeze_time
from pytest_mock import mocker
from uuid_module.build_data import build_linked_cell, dest_indexes, build_row
from uuid_module.get_data import (get_all_row_data, get_all_sheet_ids,
                                  get_blank_uuids, get_secret, get_secret_name,
                                  get_sub_indexes, load_jira_index,
                                  refresh_source_sheets)
from uuid_module.helper import (get_cell_data, get_cell_value, get_column_map,
                                get_timestamp, has_cell_link, json_extract)
from uuid_module.variables import (assignee_col, jira_col, jira_idx_sheet,
                                   jira_index_columns, sheet_columns,
                                   status_col, summary_col, task_col, uuid_col,
                                   workspace_id, minutes)
from uuid_module.cell_link_sheet_data import write_uuid_cell_links

cwd = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


def test_write_uuid_cell_links(project_data_index, source_sheets,
                               smartsheet_client):
    write_uuid_cell_links(project_data_index, source_sheets,
                          smartsheet_client)
