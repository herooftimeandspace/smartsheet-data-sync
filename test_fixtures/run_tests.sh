# Rebuild Docs
pdoc -o docs/ -d google uuid_module data_module sync_module app

# Flake tests
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./app/*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./uuid_module/*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./data_module/*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./sync_module/*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./test_unit/*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./test_integration/*.py

# Ignored depreciation warnings for libraries outside our control
pytest test_unit/ --debug -x -W ignore::DeprecationWarning --cov-config=.coveragerc --cov=./ -vvv | tee ./logs/pytest_unit.log
# pytest test_integration/ --debug -x -W ignore::DeprecationWarning --cov-config=.coveragerc --cov=./ -vvv | tee ./logs/pytest_integration.log
# pytest test_unit/ test_integration/ --debug -x -W ignore::DeprecationWarning --cov-config=.coveragerc --cov=./ -vvv | tee ./logs/pytest_all.log