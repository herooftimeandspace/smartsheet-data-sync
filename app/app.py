# import logging

import data_module.create_jira_tickets as create_jira_tickets
import sync_module.bidirectional_sync as jira_sync
import uuid_module.uuid as uuid

import app.config as config


def main():
    """Configures the scheduler to run jobs. Interval jobs are configured with
      initial defaults, but automatically adapt based on run-time per job.
      Cron jobs are scheduled to run daily with a longer lookback to catch
      any data that was not synced.

    Returns:
        bool: Returns True if main successfully initialized and scheduled jobs,
              False if not.
    """
    # Write UUIDs to blank cells in program plans.
    # Job 1 starts with 30 second intervals.
    # Job 2 runs once daily at 1am UTC and looks back 7 days
    config.scheduler.add_job(uuid.write_uuids_to_sheets,
                             'interval',
                             args=[config.minutes],
                             seconds=30,
                             id="write_uuids_interval")

    config.scheduler.add_job(uuid.write_uuids_to_sheets,
                             'cron',
                             args=[10080],
                             day='*/1',
                             hour='1',
                             id="write_uuids_cron")

    # Create new Jira tickets from Smartsheet.
    # Job 1 starts with 2 minute intervals.
    # Job 2 runs once daily at 1am UTC and looks back 7 days
    config.scheduler.add_job(create_jira_tickets.create_tickets,
                             'interval',
                             args=[config.minutes],
                             minutes=2,
                             id="create_jira_interval")

    config.scheduler.add_job(create_jira_tickets.create_tickets,
                             'cron',
                             args=[10080],
                             day='*/1',
                             hour='1',
                             id="create_jira_cron")

    # Sync data between the Jira Index Sheet and all sheets in the workspace
    # with a Jira Ticket column. By proxy, syncs data with Jira through the
    # Index Sheet
    # Job 1 starts with 15 second intervals.
    # Job 2 runs once daily at 1am UTC and looks back 7 days
    config.scheduler.add_job(jira_sync.bidirectional_sync,
                             'interval',
                             args=[config.minutes],
                             seconds=15,
                             id="sync_jira_interval")

    config.scheduler.add_job(jira_sync.bidirectional_sync,
                             'cron',
                             args=[10080],
                             day='*/1',
                             hour='1',
                             id="sync_jira_cron")

    return True
