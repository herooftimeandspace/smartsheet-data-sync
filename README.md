| Branch | Status      | Coverage |
| ------- | ----------- | ----------- |
| Prod | [![pipeline status](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/main/pipeline.svg)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/main) | [![coverage report](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/main/coverage.svg?job=coverage&key_text=Python+3.7+Coverage&key_width=140)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/main) | 
| Staging | [![pipeline status](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/staging/pipeline.svg)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/staging) | [![coverage report](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/main/coverage.svg?job=coverage&key_text=Python+3.7+Coverage&key_width=140)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/staging)    |
| Dev | [![pipeline status](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/staging/pipeline.svg)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/debug) | [![coverage report](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/badges/main/coverage.svg?job=coverage&key_text=Python+3.7+Coverage&key_width=140)](https://gitlab-dev.video.xarth.tv/cmpbad/smartsheet-data-sync-gitlab/-/commits/debug)    |

# Overview
This Smartsheet Data Sync application is designed create and sync data across multiple sheets and Jira without needing to create a Jira Connector per sheet. It uses run several modules on a timed basis. The modules perform the following actions:
1. Queries the Smartsheet API for all sheets across one or more workspaces
2. Builds a list of all rows that have a UUID column.
3. Generates and saves a UUID for each row where the UUID is missing. The UUID is a combination of Sheet ID, Row ID, UUID Column ID and the datetime when the row was created. An example of a UUID is `4148711732340612-845458703968132-2182574767400836-202105112136590000`
4. Links UUIDs to a Jira Index Sheet.
5. Creates cell links between the Jira Index Sheet and any sheet where a Jira Issue is inserted in the `Jira Ticket` column. 


# Setup
## Python
Python prequisites are:
1. python >= 3.7 - < 3.9 recommended due to Smartsheet kit issues.
2. smartsheet-python-sdk - Smartsheet API toolkit
3. apscheduler - Schedules cron / interval jobs
4. boto3 - Toolkit for interacting with AWS services
5. pytest - Code testing
6. pytest-cov - Code coverage reporting
7. pytest-xdist - Support module for pytest-cov
8. pdoc - Lightweight API documentation generator

These libraries are automatically installed when the docker image is built, but you will need them installed locally to test the app without using Docker. Pyenv is recommended.

## AWS
1. AWS Account with Admin Role
2. [AWS Secrets Manager](https://us-west-2.console.aws.amazon.com/secretsmanager/home?region=us-west-2#!/listSecrets)
3. [Copilot](https://aws.github.io/copilot-cli/)

## Docker
1. Docker - For Copilot builds
2. Docker Compose - For local dev

## Smartsheet Setup
### Smartsheet API Token
For development you can use your own API token. For production, this should be a service account in Smartsheet.
1. Go to [Smartsheet](https://app.smartsheet.com/folders/personal)
2. Click on your user icon
3. Click on `Personal Settings...`
4. Click on API Access
5. Click on `Generate new access token`
6. Copy the API access token to your clipboard

### Jira Index Sheet
You will need to create a new Smartsheet sheet. It can be named and saved anywhere you like, but you will need to know the Sheet ID and configure that in your variables, as noted below. You can name the columns anything you like. Recommended presets are in the `variables.py` file. For consistency, _every_ Sheet you wish to sync data with should use the _exact_ same column names, including spelling and punctuation. Mismatched column names will be skipped during the sync process. The Jira Index Sheet should have the following columns:
* Summary: Jira ticket title
* Assigned To: Email address of the assignee in Jira
* Status: Status of the ticket in Jira
* Jira Ticket: The Jira Issue ID
* UUID: The UUID created by this application.

### Sheet Setup
In addition to the sheet columns listed above, you will also need the following columns. _Every_ Sheet you wish to sync data with should use the _exact_ same column names, including spelling and punctuation. Mismatched column names will be skipped during the sync process. Configure all names in `variables.py`.
* Tasks: Equivalent to the "Summary" field in Jira
* Description: Equivalent to the "Description" field in Jira
* Summary: A checkbox used for the summary section of Control Center provisioned Project or Program Plans. Ignored if not present.
* Start: Start date of the line item. Used for dependency adjustments.
* Finish: Calculated from Start date and Duration
* Duration: Duration of the line item in days or weeks. Eg. `7d` or `5w`
* Predecessors: The row number of the predecessor. Start date will be keyed off the dates in the predecessor row.

### Smartsheet Jira Connector
You will need access to the Smartsheet Jira Connector. This can be granted by any Smartsheet Admin. For development you can use your own Smartsheet account. For production, this should be a service account in Smartsheet.
1. Navigate to the [Smartsheet Jira Connector](https://connectors.smartsheet.com/c/jira)
2. Log in using your Smartsheet credentials, and allow access.
3. Click `Add Workflow`
4. Configure the workflow. You will want a bidirectional sync, to create a new Sheet or designate a sheet already created, and designate one or more Jira projects to sync. During the setup you will be able to create filters that narrow down the scope of the data synced between Jira and Smartsheet. Disable grouping by ticket type. Ensure that you sync the following columns: `Summary`, `Status`, and `Assignee` Recommended: Create and save a Jira filter before creating the connector to ensure you only sync the tickets you intend.

## Variables
The `variables.py` file holds the static information needed to process API requests. Several fields will need to be modified to suit your environment
1. `workspace_id` is a list of Smartsheet Workspace IDs. Workspace IDs can be found by right clicking on a workspace in Smartsheet, and selecting `Properties`. An example with 2 workspaces is `workspace_id = [1014869735565188, 1498352056592260]`
2. `jira_idx_sheet` is a string, which contains the sheet ID of the centralized sheet where the Smartsheet Jira Connector synchronizes Jira tickets with Smartsheet. The sheet ID can be found by right clicking on the sheet you have designated to store and sync Jira tickets, and selecting `Properties`.

# Running the App
By default, the app uses [APScheduler](https://apscheduler.readthedocs.io/en/stable/userguide.html) to run multiple functions in timed intervals. For example, the API query to pull down every sheet from the workspaces is configured for `30 seconds`. Timing is controlled through the `scheduler.add_job` functions. Time can be tweaked based on the number of workspaces and sheets that need to be parsed. More sheets = longer recommended intervals.

# Developer's Guide
For testing, you can comment out the APScheduler start section and enable the `main()` function to run each module once.

## Locally in Terminal
Your local terminal will need an environment variable for `SMARTSHEET_ACCESS_TOKEN` which was generated during setup. Run the `__main__.py` app in terminal. Logs will output to the /logs/ folder and the console.

The app accepts one of 3 arguments for debug, staging, and prod deployments. The app will accept any of the following:
1. -d, -debug, --debug
2. -s, -staging, --staging
3. -p, -prod, --prod

Setting the -d flag will enable DEBUG level logging in an output file under /logs. This is useful if API calls fail and you need to figure out which sheets are causing the issue. Setting -s or -p will pull the staging or prod API tokens as defined in Secrets Manager, and only output INFO level logging in the console.

## Locally with Docker
Build and run the latest Docker configuration using `docker-compose up --build -d`. Docker will build the AWS and Smartsheet-Data-Sync containers that allow access to AWS Secrets and run the app. The default logging level when running locally is DEBUG. The Python app will pipe logs to the /logs/ folder as well as the Docker Logs console.

## Staging / Production
Once code is ready for deployment, create a pull request for the `staging` branch. This will automatically trigger a Gitlab CI/CD pipeline to deploy changes to the Staging environment in AWS. Similarly, pull requests from `staging` to `main` will trigger the pipeline to deploy the Prod environment in AWS. Commits directly to `main` are disabled.

# API Documentation
[API documentation](docs/index.html) is generated by pdoc. Run `pdoc -o docs/ uuid_module -d google` in the root directory to regenerate API documentation.