import pytest
import data_module.helper as helper

_, cwd = helper.get_local_paths()


@pytest.fixture
def env_dict():
    value = {}
    value = {'env': '--debug', 'env_msg': "Using Staging variables for "
             "workspace_id and Jira index sheet. Set workspace_id to: "
             "[7802463043512196], index_sheet to: 5786250381682564, and "
             "minutes to: 525600. Pushing tickets to 3312520078354308",
             'workspace_id': [7802463043512196],
             'index_sheet': 5786250381682564,
             'minutes': 525600,
             'push_tickets_sheet': 3312520078354308}
    return value


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_main_0():
    import app.app as app
    import app.config as config
    set_init_fixture()
    result = app.main()
    assert result is True

    def test_0():
        jobs = config.scheduler.get_jobs()
        return jobs

    result_0 = test_0()
    assert len(result_0) == 6
