log_location = "logs/"
"""Location to save logs
    """
module_log_name = "main.log"
"""The main log written to disk
    """
# PROD
workspace_id = [8158274374657924, 1479840747546500, 6569226535233412]
"""List of workspace IDs. Workspace IDs are Type: int.
    """
jira_idx_sheet = "5366809688860548"
"""Jira Index Sheet ID. Type: str
    """

# INTEGRATION TESTS
dev_workspace_id = [2618107878500228]
"""Single Workspace ID for Integration Testing, so that tests can run without
   affecting active Prod data. Workspace Type: list, Workspace IDs Type: int
   """
dev_jira_idx_sheet = "5786250381682564"
"""Jira Index Sheet in Dev. Type: str
   """

uuid_col = "UUID"
"""UUID column name. Type: str
    """
task_col = "Tasks"
"""Tasks column name. Type: str
    """
description_col = "Description"
"""Description column name. Type: str
    """
status_col = "Status"
"""Status column name. Type: str
    """
assignee_col = "Assigned To"
"""Assignee column name. Type: str
    """
jira_col = "Jira Ticket"
"""Jira ticket column name. Type: str
    """
summary_col = "Summary"
"""Summary column name. Type: str
    """
start_col = "Start"
"""Start column name. Type: str
    """
finish_col = "Finish"
"""Finish column name. Type: str
    """
duration_col = "Duration"
"""Duration column name. Type: str
    """
predecessor_col = "Predecessors"
"""Predecessors column name. Type: str
    """

index_columns = [task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col]
"""List of all columns in the UUID Index Sheet. Type: list
    """
jira_index_columns = [task_col, description_col,
                      status_col, assignee_col, jira_col,
                      duration_col, start_col, finish_col, predecessor_col]
"""List of all columns in the Jira Index Sheet. Type: list
    """
sheet_columns = [uuid_col, task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col,
                 summary_col]
"""List of columns found in Project or Program sheets. Type: list
    """
sync_columns = [status_col, assignee_col, task_col,
                start_col, duration_col]
"""List of columns to use during Cell link syncs. Type: list
    """

minutes = 65
"""The maximum number of minutes into the past the get_timestamp function
    should look before filtering out results. Type: int
    """
