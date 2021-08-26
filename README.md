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
1. Python >= 3.7
2. smartsheet-python-sdk
3. apscheduler
4. pytest
5. pdoc

These libraries are automatically installed when the docker image is built, but you will need them installed locally to test the app without using Docker. Pyenv is recommended.

## AWS
1. AWS Secrets
2. CodePipeline
3. Copilot
4. Fargate

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

## Dockerfile
Note: .gitignore automatically ignores the `.env` and `Dockerfile` files. Ensure that you don't upload your credentials to the repo.
1. Copy the `Dockerfile_example` file to the root directory and rename to `Dockerfile`
2. Replace `[API ACCESS TOKEN]` with your Smartsheet API token.
3. Save.

## .env File
1. Copy the `env_example` file to the root directory and rename to `.env`
2. Replace `[API ACCESS TOKEN]` with your Smartsheet API token.
3. Save.

## Variables
The `variables.py` file holds the static information needed to process API requests. Several fields will need to be modified to suit your environment
1. `workspace_id` is a list of Smartsheet Workspace IDs. Workspace IDs can be found by right clicking on a workspace in Smartsheet, and selecting `Properties`. An example with 2 workspaces is `workspace_id = [1014869735565188, 1498352056592260]`
2. `jira_idx_sheet` is a string, which contains the sheet ID of the centralized sheet where the Smartsheet Jira Connector synchronizes Jira tickets with Smartsheet. The sheet ID can be found by right clicking on the sheet you have designated to store and sync Jira tickets, and selecting `Properties`.


# Running the App
By default, the app uses APScheduler to run multiple functions in timed intervals. For example, the API query to pull down every sheet from the workspaces is configured for `40 seconds`. Timing is controlled through the `scheduler.add_job` functions. Time can be tweaked based on the number of workspaces and sheets that need to be parsed. More sheets = longer recommended intervals.

For testing, you can comment out the APScheduler start section and enable the `main()` function to run each module once.

## Locally
Your local terminal will need an environment variable for `SMARTSHEET_ACCESS_TOKEN` which was generated during setup. Run the `__main__.py` app in terminal. Logs will output to the /logs/ folder and the console.


## Docker
1. Build the latest Docker image using `docker build -t uuid .`
2. Run the Docker image in detached mode with `docker run -d -v $(pwd):/uuid --name manage_uuids uuid`

The Python app will pipe logs to the /logs/ folder as well as the Docker Logs console.

# API Documentation
API documentation can be found in the /docs folder, and is generated by pdoc. Run `pdoc -o docs/ uuid_module -d google` in the root directory to regenerate API documentation.