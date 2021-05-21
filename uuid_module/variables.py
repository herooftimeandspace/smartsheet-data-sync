log_location = "logs/"
"""Location to save logs
    """
module_log_name = "main.log"
"""The main log written to disk
    """

workspace_id = [1014869735565188, 1498352056592260]
"""List of workspace IDs
    """
uuid_col = "UUID"
"""UUID column name
    """
task_col = "Tasks"
"""Tasks column name
    """
description_col = "Description"
"""Description column name
    """
status_col = "Status"
"""Status column name
    """
assignee_col = "Assigned To"
"""Assignee column name
    """
jira_col = "Jira Ticket"
"""Jira ticket column name
    """
summary_col = "Summary"
"""Summary column name
    """
start_col = "Start"
"""Start column name
    """
finish_col = "Finish"
"""Finish column name
    """
duration_col = "Duration"
"""Duration column name
    """
predecessor_col = "Predecessors"
"""Predecessors column name
    """
jira_idx_sheet = "5366809688860548"
"""Jira Index Sheet ID
    """


index_columns = [task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col]
"""List of all columns in the UUID Index Sheet
    """
jira_index_columns = [task_col, description_col,
                      status_col, assignee_col, jira_col,
                      duration_col, start_col, finish_col, predecessor_col]
"""List of all columns in the Jira Index Sheet
    """
sheet_columns = [uuid_col, task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col,
                 summary_col]
"""List of columns found in Project or Program sheets
    """
sync_columns = [status_col, assignee_col, task_col,
                start_col, duration_col]
"""List of columns to use during Cell link syncs
    """
