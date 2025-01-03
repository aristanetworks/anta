---
anta_title: How to contribute to ANTA
---
<!--
  ~ Copyright (c) 2023-2025 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

Contribution model is based on a fork-model. Don't push to aristanetworks/anta directly. Always do a branch in your forked repository and create a PR.

To help development, open your PR as soon as possible even in draft mode. It helps other to know on what you are working on and avoid duplicate PRs.

## Create a development environment

Run the following commands to create an ANTA development environment:

```bash
# Clone repository
$ git clone https://github.com/aristanetworks/anta.git
$ cd anta

# Install ANTA in editable mode and its development tools
$ pip install -e .[dev]
# To also install the CLI
$ pip install -e .[dev,cli]

# Verify installation
$ pip list -e
Package Version Editable project location
------- ------- -------------------------
anta    1.2.0   /mnt/lab/projects/anta
```

Then, [`tox`](https://tox.wiki/) is configured with few environments to run CI locally:

```bash
$ tox list -d
default environments:
clean  -> Erase previous coverage reports
lint   -> Check the code style
type   -> Check typing
py39   -> Run pytest with py39
py310  -> Run pytest with py310
py311  -> Run pytest with py311
py312  -> Run pytest with py312
report -> Generate coverage report
```

### Code linting

```bash
tox -e lint
[...]
lint: commands[0]> ruff check .
All checks passed!
lint: commands[1]> ruff format . --check
158 files already formatted
lint: commands[2]> pylint anta

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

lint: commands[3]> pylint tests

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

  lint: OK (22.69=setup[2.19]+cmd[0.02,0.02,9.71,10.75] seconds)
  congratulations :) (22.72 seconds)
```

### Code Typing

```bash
tox -e type

[...]
type: commands[0]> mypy --config-file=pyproject.toml anta
Success: no issues found in 68 source files
type: commands[1]> mypy --config-file=pyproject.toml tests
Success: no issues found in 82 source files
  type: OK (31.15=setup[14.62]+cmd[6.05,10.48] seconds)
  congratulations :) (31.18 seconds)
```

> NOTE: Typing is configured quite strictly, do not hesitate to reach out if you have any questions, struggles, nightmares.

## Unit tests with Pytest

To keep high quality code, we require to provide a **Pytest** for every tests implemented in ANTA.

All submodule should have its own pytest section under `tests/units/anta_tests/<submodule-name>.py`.

### How to write a unit test for an AntaTest subclass

The Python modules in the `tests.units.anta_tests` package define test parameters for AntaTest subclasses unit tests.
A generic test function is written for all unit tests of the `AntaTest` subclasses.
In order for your unit tests to be correctly collected, you need to import the generic test function even if not used in the Python module.

The `pytest_generate_tests` function definition in `conftest.py` is called during test collection.

The `pytest_generate_tests` function will parametrize the generic test function based on the `DATA` constant defined in modules in the `tests.units.anta_tests` package.

See https://docs.pytest.org/en/7.3.x/how-to/parametrize.html#basic-pytest-generate-tests-example

The `DATA` constant is a list of dictionaries used to parametrize the test. A `TypedDict` has been defined to ease the writing of such constant and leverage `mypy` type checking.

``` python
class AtomicResult(TypedDict):
    """Expected atomic result of a unit test of an AntaTest subclass."""

    result: Literal["success", "failure", "skipped"]  # The expected status of this atomic result.
    description: str  # The expected description of this atomic result.
    messages: NotRequired[list[str]]  # The expected messages of this atomic result. The strings can be a substrings of the actual messages.
    inputs: NotRequired[dict[str, Any]]  # The inputs registered with this atomic result.


class Expected(TypedDict):
    """Expected result of a unit test of an AntaTest subclass."""

    result: Literal["success", "failure", "skipped"]  # The expected status of this unit test.
    messages: NotRequired[list[str]]  # The expected messages of the test. The strings can be a substrings of the actual messages.
    atomic_results: NotRequired[list[AtomicResult]]  # The list of expected atomic results.


class AntaUnitTest(TypedDict):
    """The parameters required for a unit test of an AntaTest subclass."""

    name: str  # Test name as displayed by Pytest.
    test: type[AntaTest]  # An AntaTest subclass imported in the test module - e.g. VerifyUptime.
    inputs: NotRequired[dict[str, Any]]  # The test inputs of this unit test.
    eos_data: list[dict[str, Any] | str]  # List of command outputs used to mock EOS commands during this unit test.
    expected: Expected  # The expected result of this unit test.
```

Test example for `anta.tests.system.VerifyUptime` AntaTest.

``` python
# Import your AntaTest
from anta.tests.system import VerifyUptime

# Import the generic test function
from tests.units.anta_tests import test

# Define test parameters
DATA: list[AntaUnitTest] = [
   {
        # Arbitrary test name.
        "name": "success",
        # Must be an AntaTest subclass definition
        "test": VerifyUptime,
        # JSON output of the 'show uptime' EOS command as defined in VerifyUptime.commands
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
        # The expected message can be a substring of the actual message.
        "expected": {"result": "failure", "messages": ["Device uptime is 665.15 seconds"]},
    },
]
```

Test example for `anta.tests.connectivity.VerifyReachability` AntaTest that contains atomic results.

``` python
from anta.tests.connectivity import VerifyReachability
from tests.units.anta_tests import test

DATA: list[AntaUnitTest] = [

    {
        "name": "failure-ip",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.11", "source": "10.0.0.5"}, {"destination": "10.0.0.2", "source": "10.0.0.5"}]},
        "eos_data": [
            {
                "messages": [
                    """ping: sendmsg: Network is unreachable
                ping: sendmsg: Network is unreachable
                PING 10.0.0.11 (10.0.0.11) from 10.0.0.5 : 72(100) bytes of data.

                --- 10.0.0.11 ping statistics ---
                2 packets transmitted, 0 received, 100% packet loss, time 10ms


                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "failure",
            "messages": ["Unreachable Destination 10.0.0.11 from 10.0.0.5 in VRF default"],
            # This test has implemented atomic results.
            # Expected atomic results must be specified or the test will fail.
            "atomic_results": [
                {
                    # Expected atomic result description
                    "description": "Destination 10.0.0.11 from 10.0.0.5 in VRF default",
                    # If the atomic result is tied to a subset of the test inputs, it needs to be expected here.
                    "inputs": {
                        "destination": "10.0.0.11",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "10.0.0.5",
                        "vrf": "default",
                    },
                    # Expected atomic result status
                    "result": "failure",
                    # If the atomic result returns messages, it needs to be expected otherwise test will fail.
                    # The expected message can be a substring of the actual message.
                    "messages": ["Unreachable Destination 10.0.0.11 from 10.0.0.5 in VRF default"],

                },
                {
                    "description": "Destination 10.0.0.2 from 10.0.0.5 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "10.0.0.5",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
    }
```

## Git Pre-commit hook

```bash
pip install pre-commit
pre-commit install
```

When running a commit or a pre-commit check:

``` bash
❯ pre-commit
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check for added large files..............................................Passed
check for merge conflicts................................................Passed
Check and insert license on Python files.................................Passed
Check and insert license on Markdown files...............................Passed
Run Ruff linter..........................................................Passed
Run Ruff formatter.......................................................Passed
Check code style with pylint.............................................Passed
Checks for common misspellings in text files.............................Passed
Check typing with mypy...................................................Passed
Check Markdown files style...............................................Passed
```

## Configure MYPYPATH

In some cases, mypy can complain about not having `MYPYPATH` configured in your shell. It is especially the case when you update both an anta test and its unit test. So you can configure this environment variable with:

```bash
# Option 1: use local folder
export MYPYPATH=.

# Option 2: use absolute path
export MYPYPATH=/path/to/your/local/anta/repository
```

## Documentation

[`mkdocs`](https://www.mkdocs.org/) is used to generate the documentation. A PR should always update the documentation to avoid documentation debt.

### Install documentation requirements

Run pip to install the documentation requirements from the root of the repo:

```bash
pip install -e .[doc]
```

### Testing documentation

You can then check locally the documentation using the following command from the root of the repo:

```bash
mkdocs serve
```

By default, `mkdocs` listens to http://127.0.0.1:8000/, if you need to expose the documentation to another IP or port (for instance all IPs on port 8080), use the following command:

```bash
mkdocs serve --dev-addr=0.0.0.0:8080
```

### Build class diagram

To build class diagram to use in API documentation, you can use `pyreverse` part of `pylint` with [`graphviz`](https://graphviz.org/) installed for jpeg generation.

```bash
pyreverse anta --colorized -a1 -s1 -o jpeg -m true -k --output-directory docs/imgs/uml/ -c <FQDN anta class>
```

Image will be generated under `docs/imgs/uml/` and can be inserted in your documentation.

### Checking links

Writing documentation is crucial but managing links can be cumbersome. To be sure there is no dead links, you can use [`muffet`](https://github.com/raviqqe/muffet) with the following command:

```bash
muffet -c 2 --color=always http://127.0.0.1:8000 -e fonts.gstatic.com -b 8192
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](https://github.com/aristanetworks/anta/tree/main/.github/workflows). The results can be viewed [here](https://github.com/aristanetworks/anta/actions).
