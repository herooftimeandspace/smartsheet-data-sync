import os

import pytest


@pytest.fixture
def env_fixture():
    return "--debug"


@pytest.fixture
def env_dict():
    value = {}
    value = {'env': '--debug', 'env_msg': "Using Staging variables for "
             "workspace_id and Jira index sheet. Set workspace_id to: "
             "[2618107878500228], index_sheet to: 5786250381682564, and "
             "minutes to: 525600. Pushing tickets to 3312520078354308",
             'workspace_id': [2618107878500228],
             'index_sheet': 5786250381682564,
             'minutes': 525600,
             'push_tickets_sheet': 3312520078354308}
    return value


def set_init_fixture():
    import app.config as config
    config.init(["--debug"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_get_secret(env_fixture):
    import app.config as config
    secret_name = config.get_secret_name(env_fixture)
    assert secret_name == "staging/smartsheet-data-sync/svc-api-token"
    retrieved_secret = config.get_secret(secret_name)
    assert retrieved_secret == os.environ["SMARTSHEET_ACCESS_TOKEN"]


def test_get_secret_name(env_fixture):
    import app.config as config
    with pytest.raises(TypeError):
        actual = config.get_secret_name(1)
    with pytest.raises(ValueError):
        actual = config.get_secret_name("--super_secret")

    expected = "staging/smartsheet-data-sync/svc-api-token"
    actual = config.get_secret_name(env_fixture)
    assert expected == actual


def test_case_0(env_fixture, env_dict):
    import app.config as module_0
    set_init_fixture()
    var_0 = module_0.set_env_vars(env_fixture)
    assert isinstance(var_0, dict)
    assert module_0.env == env_dict['env']
    assert module_0.env_msg == env_dict['env_msg']
    assert module_0.workspace_id == env_dict['workspace_id']
    assert module_0.index_sheet == env_dict['index_sheet']
    assert module_0.minutes == env_dict['minutes']
    assert module_0.push_tickets_sheet == env_dict['push_tickets_sheet']
    assert module_0.app_vars.dev_jira_idx_sheet == 5786250381682564
    assert module_0.app_vars.dev_minutes == 525600
    assert module_0.app_vars.dev_workspace_id == [2618107878500228]
    assert module_0.app_vars.dev_push_jira_tickets_sheet == 3312520078354308
    assert module_0.app_vars.prod_jira_idx_sheet == 5366809688860548
    assert module_0.app_vars.prod_minutes == 65
    assert module_0.app_vars.prod_workspace_id == [8158274374657924,
                                                   1479840747546500,
                                                   6569226535233412]
    var_1 = module_0.app_vars.prod_push_jira_tickets_sheet
    assert var_1 is None
    assert module_0.logger.filters == []
    assert module_0.logger.name == 'app.config'
    assert module_0.logger.level == 0
    assert module_0.logger.propagate is True
    assert module_0.logger.handlers == []
    # assert module_0.logger.disabled is False


def test_case_1():
    import app.config as module_0
    set_init_fixture()
    str_0 = '|Y%X/\r\x0b(\n!'
    var_0 = module_0.get_secret(str_0)
    assert var_0 is None
    var_1 = module_0.get_secret_name()
    assert var_1 == 'staging/smartsheet-data-sync/svc-api-token'
    var_2 = module_0.get_secret(var_1)
    assert len(var_2) == 37
