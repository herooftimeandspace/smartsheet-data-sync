log_location = "logs/"
uuid_log_name = "uuid.log"
compare_log_name = "comparison.log"
module_log_name = "uuid_module.log"

workspace_id = [1014869735565188, 1498352056592260]
uuid_col = "UUID"
task_col = "Tasks"
description_col = "Description"
status_col = "Status"
assignee_col = "Assigned To"
jira_col = "Jira Ticket"
summary_col = "Summary"
start_col = "Start"
finish_col = "Finish"
duration_col = "Duration"
predecessor_col = "Predecessors"
jira_idx_sheet = "5366809688860548"


index_columns = [task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col]
jira_index_columns = [task_col, description_col,
                      status_col, assignee_col, jira_col,
                      duration_col, start_col, finish_col, predecessor_col]
sheet_columns = [uuid_col, task_col, description_col,
                 status_col, assignee_col, jira_col,
                 duration_col, start_col, finish_col, predecessor_col,
                 summary_col]
sync_columns = [status_col, assignee_col, task_col,
                start_col, duration_col]
