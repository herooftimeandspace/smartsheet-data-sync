# Rebuild Docs
pdoc -o docs/ -d google uuid_module

# Flake tests
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./*.py
flake8 --max-line-length=80 --per-file-ignores="__init__.py:F401" ./uuid_module/*.py

# Ignored depreciation warnings for libraries outside our control
pytest --debug -W ignore::DeprecationWarning --cov-config=.coveragerc --cov=./ -vvv | tee ./logs/pytest.log