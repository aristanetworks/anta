Contributions are welcome.

Please open an issue and submit a PR.

### Requirements

The file [requirements-dev.txt](requirements-dev.txt) has the required packages to contribute.
In addition to the packages that are already in the file [requirements.txt](requirements.txt), it also has:
* The package `lazydocs` that is used by the script [generate_functions_documentation.py](generate_functions_documentation.py) to generate the functions documentation in markdown format from the functions docstring.
* The package `pytest` that is required to use the script [unit_test.py](unit_test.py) in order to test the functions defined in the directory [test_eos](test_eos).

### To run unit tests

To run the unit tests that test the functions defined in the directory [test_eos](test_eos), run the command `py.test` or `py.test -vv`

### To generate documentation functions

To generate from the functions docstring the documentation in markdown format in the directory [documentation](documentation), run these commands:

```shell
python generate_functions_documentation.py
ls documentation
```
