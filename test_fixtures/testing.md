# Introduction
Testing within the Smartsheet Data Sync app primarily done with PyTest and Flake. The testing suite is broken into three sets:
* Fixtures (test_fixtures): Generic testing fixtures loaded and used by multiple tests suites
* Integration Tests (test_integration): Integration tests that use the Smartsheet Dev workspace to test connection to the API.
* Unit Tessts (test_unit): Unit tests that check the individual functions, variables and outputs.

Pytest's config is pulled from `.coveragerc` and coverage output is saved to `.coverage`

## TL:DR
For ease of use, run `./test_fixtures/run_tests.sh` to execute Flake and PyTest unit tests.

# Commands
## PDoc
API documentation is generated with pdoc. Documentation is formatted to the Google docstring format. Running the command `pdoc -o docs/ -d google uuid_module data_module sync_module app` will regernate all documentation and save it to the `docs/` folder. You can then open `index.html` to view supporting documentation. Most functions are annotated. If you find one that isn't, please add annotations.

## Flake
Flake is used for syntax consistency. Max line length is `80`. Flake should generally skip the `__init__.py` files in each submodule. Example: `flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./*.py`

## PyTest
PyTest can be used to run the unit tests, integration tests or both. General command syntax is `pytest test_unit/ --debug -x -W ignore::DeprecationWarning --cov-config=.coveragerc --cov=./ -vvv | tee ./logs/pytest_unit.log`. In this example, only the unit tests are run, using the `--debug` flag. We automatically quit if any tests fails using the `-x` flag, and ignore DepreciationWarnings while testing with `-W ignore::DepreciationWarning`. We use `.coveragerc` to control what we test and what is ignored, and output is controlled by the `--cov` flag. Lastly, we create a pipe to `tee` so that we can capture the Pytest output in the console as well as a log file for examination.

# CICD Pipeline
Flake and PyTest are automatically executed as part of the `gitlab-ci.yml` CICD pipeline. Depending on the branch only certain test suites will run. Committing changes to `debug`, `staging`, or `main` will automatically run the full suite of unit and integration tests. All other branches will only run unit tests.