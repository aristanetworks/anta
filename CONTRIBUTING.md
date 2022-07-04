# Contributions guide

Contributions are welcome.
Please open an issue and submit a PR.

## Requirements

The file [requirements-dev.txt](requirements-dev.txt) has the required packages to contribute:

- `lazydocs` is used by the script [generate-functions-documentation.py](documentation/generate-functions-documentation.py) to generate the functions documentation in markdown format from the functions docstring.
- `pytest` is required to use the script [unit_test.py](tests/unit_test.py) in order to test the functions defined in the directory [anta](anta).
- `pytest-cov` is used to produce code coverage reports.
- `pylint` is a linter for python.
- `yamllint` is a linter for YAML files.

## To use yamllint

Run the command `yamllint -c .yamllint.yml .`

## To use pylint

Run the command `pylint $(git ls-files '-.py')`

## To run unit tests

To run the unit tests that test the functions defined in the directory [anta](anta), run the following commands from the `tests` directory:

```bash
py.test --cov=anta -vv
```

## To generate documentation functions

To generate from the functions docstring the documentation in markdown format in the directory [documentation](documentation), run these commands from the root of the repository:

```shell
python documentation/generate-functions-documentation.py
ls documentation
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](.github/workflows).
We can view the result [here](https://github.com/arista-netdevops-community/network-test-automation/actions).