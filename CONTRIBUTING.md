# Contributions guide

Contributions are welcome.
Please open an issue and submit a PR.

## Requirements

The file [requirements-dev.txt](requirements-dev.txt) has the required packages to contribute:

- `lazydocs` is used by the script [generate-functions-documentation.py](docs/generate-functions-documentation.py) to generate the functions documentation in markdown format from the functions docstring
- `pytest` is required to test the package [anta](anta)
- `pytest-cov` is used to produce code coverage reports
- `pylint` is a linter for python
- `yamllint` is a linter for YAML files

## To use yamllint

Run the command `yamllint -c .yamllint.yml .`

## To use pylint

Run the command `pylint $(git ls-files '-.py')`

## To run unit tests

To test the Python module [tests](anta/tests.py) of the package anta, run the following commands from the `tests` directory:

```bash
py.test --cov=anta -vv
py.test units/antatests_test.py -vv --cov=anta.tests
```

## To generate documentation functions

To generate from the docstring the documentation in markdown format in the directory [api](docs/api), run these commands from the root of the repository:

```shell
python documentation/generate-functions-documentation.py
ls docs/api
```

## Git Pre-commit hook

```bash
pip install pre-commit
pre-commit install
```

When running a commit or a pre-commit check:

```
❯ echo "import foobaz" > test.py && git add test.py
❯ pre-commit
pylint...................................................................Failed
- hook id: pylint
- exit code: 22

************* Module test
test.py:1:0: C0114: Missing module docstring (missing-module-docstring)
test.py:1:0: E0401: Unable to import 'foobaz' (import-error)
test.py:1:0: W0611: Unused import foobaz (unused-import)
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](.github/workflows).
We can view the result [here](https://github.com/arista-netdevops-community/network-test-automation/actions)
