<!--
  ~ Copyright (c) 2023 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

## How to write a unit test for an AntaTest subclass

The Python modules in this folder define test parameters for AntaTest subclasses unit tests.
A generic test function is written for all unit tests in `tests.lib.anta` module.
The `pytest_generate_tests` function definition in `conftest.py` is called during test collection.
The `pytest_generate_tests` function will parametrize the generic test function based on the `DATA` data structure defined in `tests.units.anta_tests` modules.
See https://docs.pytest.org/en/7.3.x/how-to/parametrize.html#basic-pytest-generate-tests-example

In order for your unit tests to be correctly collected, you need to import the generic test function even if not used in the Python module.

Test example for `anta.tests.system.VerifyUptime` AntaTest.

``` python
# Import the generic test function
from tests.lib.anta import test  # noqa: F401

# Import your AntaTest
from anta.tests.system import VerifyUptime

# Define test parameters
DATA: list[dict[str, Any]] = [
   {
        # Arbitrary test name
        "name": "success",
        # Must be an AntaTest definition
        "test": VerifyUptime,
        # Data returned by EOS on which the AntaTest is tested
        "eos_data": [{"upTime": 1186689.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        # Dictionary to instantiate VerifyUptime.Input
        "inputs": {"minimum": 666},
        # Expected test result
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyUptime,
        "eos_data": [{"upTime": 665.15, "loadAvg": [0.13, 0.12, 0.09], "users": 1, "currentTime": 1683186659.139859}],
        "inputs": {"minimum": 666},
        # If the test returns messages, it needs to be expected otherwise test will fail.
        # NB: expected messages only needs to be included in messages returned by the test. Exact match is not required.
        "expected": {"result": "failure", "messages": ["Device uptime is 665.15 seconds"]},
    },
]
```
