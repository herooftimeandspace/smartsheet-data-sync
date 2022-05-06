import os
import pytest


@pytest.fixture
def env_dict():
    import uuid_module.variables as app_vars
    dev = {'env': '--dev', 'env_msg': "Using Dev variables for "
           "workspace_id and Jira index sheet. Set workspace_id to: "
           "[7802463043512196], index_sheet to: 5786250381682564, and "
           "minutes to: 525600. Pushing tickets to 3312520078354308",
           'workspace_id': [app_vars.dev_workspace_id],
           'index_sheet': app_vars.dev_jira_idx_sheet,
           'minutes': app_vars.dev_minutes,
           'push_tickets_sheet': app_vars.dev_push_jira_tickets_sheet}
    staging = {'env': '--staging', 'env_msg': "Using Staging variables for "
               "workspace_id and Jira index sheet. Set workspace_id to: "
               "[2618107878500228], index_sheet to: 5786250381682564, and "
               "minutes to: 130. Pushing tickets to 3312520078354308",
               'workspace_id': [app_vars.stg_workspace_id],
               'index_sheet': app_vars.stg_jira_idx_sheet,
               'minutes': app_vars.stg_minutes,
               'push_tickets_sheet': app_vars.stg_push_jira_tickets_sheet}
    prod = {'env': '--prod', 'env_msg': "Using Prod environment variables for "
            "workspace_id and Jira index sheet. Set workspace_id to: "
            "[8158274374657924, 1479840747546500, 6569226535233412], "
            "index_sheet to: 5366809688860548, and "
            "minutes to: 65. Pushing tickets to None",
            'workspace_id': [app_vars.prod_workspace_id],
            'index_sheet': app_vars.prod_jira_idx_sheet,
            'minutes': app_vars.prod_minutes,
            'push_tickets_sheet': app_vars.prod_push_jira_tickets_sheet}
    canary = {'env': '--dev', 'env_msg': "Invalid flag: --canary. Using "
              "Dev variables. Set workspace_id to: "
              "[7802463043512196], index_sheet to: 5786250381682564, and "
              "minutes to: 525600. Pushing tickets to 3312520078354308",
              'workspace_id': [app_vars.dev_workspace_id],
              'index_sheet': app_vars.dev_jira_idx_sheet,
              'minutes': app_vars.dev_minutes,
              'push_tickets_sheet': app_vars.dev_push_jira_tickets_sheet}
    return dev, staging, prod, canary


def set_init_fixture():
    import app.config as config
    config.init(["--dev"])
    global smartsheet_client
    smartsheet_client = config.smartsheet_client


def test_get_secret_0(env_fixture):
    import app.config as config
    secret_name = config.get_secret_name(env_fixture)
    assert secret_name == "staging/smartsheet-data-sync/svc-api-token"
    retrieved_secret = config.get_secret(secret_name)
    assert retrieved_secret == os.environ["SMARTSHEET_ACCESS_TOKEN"]


# def test_get_secret_1(env_fixture):
#     import app.config as config

#     @patch("boto3.client.get_secret_value", return_value="Nope")
#     def test_0(mock_0):
#         binary_secret = config.get_secret_name(env_fixture)
#         return binary_secret

#     result_0 = test_0()
#     assert result_0


def test_get_secret_name_0(env_fixture):
    import app.config as config
    with pytest.raises(TypeError):
        actual = config.get_secret_name(1)
    with pytest.raises(ValueError):
        actual = config.get_secret_name("--super_secret")

    expected = "staging/smartsheet-data-sync/svc-api-token"
    actual = config.get_secret_name(env_fixture)
    assert expected == actual


def test_get_secret_name_1():
    import app.config as config

    def test_0():
        expected = "staging/smartsheet-data-sync/svc-api-token"
        actual = config.get_secret_name("--dev")
        if expected == actual:
            return True
        else:
            return False

    def test_1():
        expected = "staging/smartsheet-data-sync/svc-api-token"
        actual = config.get_secret_name("--staging")
        if expected == actual:
            return True
        else:
            return False

    def test_2():
        expected = "prod/smartsheet-data-sync/svc-api-token"
        actual = config.get_secret_name("--prod")
        if expected == actual:
            return True
        else:
            return False

    result_0 = test_0()
    result_1 = test_1()
    result_2 = test_2()
    assert result_0 is True
    assert result_1 is True
    assert result_2 is True


def test_set_env_vars_0():
    import app.config as config
    with pytest.raises(TypeError):
        config.set_env_vars(1337)


def test_set_env_vars_1(env_dict):
    debug, _, _, _ = env_dict
    import app.config as config
    var_0 = config.set_env_vars("--dev")
    assert isinstance(var_0, dict)
    assert config.env == debug['env']
    assert config.env_msg == debug['env_msg']
    assert config.workspace_id == debug['workspace_id'][0]
    assert config.index_sheet == debug['index_sheet']
    assert config.minutes == debug['minutes']
    assert config.push_tickets_sheet == debug['push_tickets_sheet']


def test_set_env_vars_2(env_dict):
    _, staging, _, _ = env_dict
    import app.config as config
    var_0 = config.set_env_vars("--staging")
    assert isinstance(var_0, dict)
    assert var_0['env'] == staging['env']
    assert var_0['env_msg'] == staging['env_msg']
    assert var_0['workspace_id'] == staging['workspace_id'][0]
    assert var_0['index_sheet'] == staging['index_sheet']
    assert var_0['minutes'] == staging['minutes']
    assert var_0['push_tickets_sheet'] == staging['push_tickets_sheet']


def test_set_env_vars_3(env_dict):
    _, _, prod, _ = env_dict
    import app.config as config
    var_0 = config.set_env_vars("--prod")
    assert isinstance(var_0, dict)
    assert var_0['env'] == prod['env']
    assert var_0['env_msg'] == prod['env_msg']
    assert var_0['workspace_id'] == prod['workspace_id'][0]
    assert var_0['index_sheet'] == prod['index_sheet']
    assert var_0['minutes'] == prod['minutes']
    assert var_0['push_tickets_sheet'] == prod['push_tickets_sheet']


def test_set_env_vars_4(env_dict):
    _, _, _, canary = env_dict
    import app.config as config
    var_0 = config.set_env_vars("--canary")
    assert isinstance(var_0, dict)
    assert var_0['env'] == canary['env']
    assert var_0['env_msg'] == canary['env_msg']
    assert var_0['workspace_id'] == canary['workspace_id'][0]
    assert var_0['index_sheet'] == canary['index_sheet']
    assert var_0['minutes'] == canary['minutes']
    assert var_0['push_tickets_sheet'] == canary['push_tickets_sheet']


def test_set_env_vars_5(env_fixture, env_dict):
    import app.config as module_0
    debug, _, _, _ = env_dict
    set_init_fixture()
    var_0 = module_0.set_env_vars(env_fixture)
    assert isinstance(var_0, dict)
    assert module_0.env == debug['env']
    assert module_0.env_msg == debug['env_msg']
    assert module_0.workspace_id == debug['workspace_id'][0]
    assert module_0.index_sheet == debug['index_sheet']
    assert module_0.minutes == debug['minutes']
    assert module_0.push_tickets_sheet == debug['push_tickets_sheet']
    assert module_0.app_vars.dev_jira_idx_sheet == 5786250381682564
    assert module_0.app_vars.dev_minutes == 525600
    assert module_0.app_vars.dev_workspace_id == [7802463043512196]
    assert module_0.app_vars.dev_push_jira_tickets_sheet == 3312520078354308
    assert module_0.app_vars.stg_jira_idx_sheet == 5786250381682564
    assert module_0.app_vars.stg_minutes == 130
    assert module_0.app_vars.stg_workspace_id == [2618107878500228]
    assert module_0.app_vars.stg_push_jira_tickets_sheet == 3312520078354308
    assert module_0.app_vars.prod_jira_idx_sheet == 5366809688860548
    assert module_0.app_vars.prod_minutes == 65
    assert module_0.app_vars.prod_workspace_id == [8158274374657924,
                                                   1479840747546500,
                                                   6569226535233412]
    assert module_0.app_vars.prod_push_jira_tickets_sheet is None
    assert module_0.logger.filters == []
    assert module_0.logger.name == 'app.config'
    assert module_0.logger.level == 0
    assert module_0.logger.propagate is True
    assert module_0.logger.handlers == []
    # assert module_0.logger.disabled is False


def test_set_logging_config_0():
    import app.config as config
    with pytest.raises(TypeError):
        config.set_logging_config(1337)
    with pytest.raises(ValueError):
        config.set_logging_config("--canary")


def test_set_logging_config_1():
    import app.config as config
    import uuid_module.variables as app_vars
    import logging
    result_0 = config.set_logging_config("--dev")
    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_location = os.path.join(cwd, app_vars.log_location)
    assert result_0["version"] == 1
    assert result_0["formatters"] == {
        'f': {'format':
              "%(asctime)s - %(levelname)s - %(message)s"}
    }
    assert result_0["handlers"] == {
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'f',
            'level': logging.DEBUG,
            'filename': log_location + app_vars.module_log_name
        },
        'docker': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.DEBUG,
            'stream': 'ext://sys.stdout'
        }
    }
    assert result_0["root"] == {
        'handlers': ['docker'],  # 'console', 'file'
        'level': logging.DEBUG,
        'disable_existing_loggers': False
    }


def test_set_logging_config_2():
    import app.config as config
    import logging
    result_0 = config.set_logging_config("--staging")
    assert result_0["version"] == 1
    assert result_0["formatters"] == {
        'f': {'format':
              "%(asctime)s - %(levelname)s - %(message)s"}
    }
    assert result_0["handlers"] == {
        'docker': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.INFO,
            'stream': 'ext://sys.stdout'
        }
    }
    assert result_0["root"] == {
        'handlers': ['docker'],  # 'console', 'file'
        'level': logging.DEBUG,
        'disable_existing_loggers': False
    }


def test_set_logging_config_3():
    import app.config as config
    import logging
    result_0 = config.set_logging_config("--prod")
    assert result_0["version"] == 1
    assert result_0["formatters"] == {
        'f': {'format':
              "%(asctime)s - %(levelname)s - %(message)s"}
    }
    assert result_0["handlers"] == {
        'docker': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.INFO,
            'stream': 'ext://sys.stdout'
        }
    }
    assert result_0["root"] == {
        'handlers': ['docker'],  # 'console', 'file'
        'level': logging.DEBUG,
        'disable_existing_loggers': False
    }


# def test_init_0():
#     import app.config as config

#     @patch("os.mkdir", return_value="False", side_effect=FileExistsError)
#     def test_0(mock_0):
#         with pytest.raises(FileExistsError):
#             config.init(["--dev"])
#             return True

#     assert test_0() is True


# def test_init_1():
#     import app.config as config

#     @patch("os.environ", return_value="config", side_effect=TypeError)
#     def test_0(mock_0):
#         with pytest.raises(TypeError):
#             config.init(["--dev"])
#             return True

#     assert test_0() is True


def test_validate_inputs_0():
    import app.config as module_0
    set_init_fixture()
    str_0 = '|Y%X/\r\x0b(\n!'
    var_0 = module_0.get_secret(str_0)
    assert var_0 is None
    var_1 = module_0.get_secret_name()
    assert var_1 == 'staging/smartsheet-data-sync/svc-api-token'
    var_2 = module_0.get_secret(var_1)
    assert len(var_2) == 37
