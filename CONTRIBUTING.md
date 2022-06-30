Contributions are welcome.

Please open an issue and submit a PR.

### Requirements

The file [requirements-dev.txt](requirements-dev.txt) has the required packages to contribute:
* `lazydocs` is used by the script [generate_functions_documentation.py](generate_functions_documentation.py) to generate the functions documentation in markdown format from the functions docstring.
* `pytest` is required to use the script [unit_test.py](unit_test.py) in order to test the functions defined in the directory [nta](nta).
* `pytest-cov` is used to produce code coverage reports.
* `pylint` is a linter for python.
* `yamllint` is a linter for YAML files.

### To use yamllint

Run the command `yamllint -c .yamllint.yml .`

### To use pylint

Run the command `pylint $(git ls-files '*.py')`

### To run unit tests

To run the unit tests that test the functions defined in the directory [nta](nta), run the command `py.test` or `py.test -vv` or `py.test --cov .` or `py.test --cov . -vv`

### To generate documentation functions

To generate from the functions docstring the documentation in markdown format in the directory [documentation](documentation), run these commands:

```shell
python generate_functions_documentation.py
ls documentation
```
