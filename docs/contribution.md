# How to contribute to ANTA

Contribution model is based on a fork-model. Don't push to arista-netdevops-community/anta directly. Always do a branch in your repository and create a PR.

To help development, open your PR as soon as possible even in draft mode. It helps other to know on what you are working on and avoid duplicate PRs.

## Install repository

Run these commands to install:

- The package [ANTA](https://github.com/arista-netdevops-community/anta/blob/master/anta) and its dependencies
- ANTA cli executable.

```shell
# Clone repository
git clone https://github.com/arista-netdevops-community/anta.git
cd network-test-automation

# Install module in editable mode
pip install -e .
```

Run these commands to verify:

```bash
# Check python installation
$ pip list

# Check version using cli
$ anta --version
anta, version 0.6.0
```

### Install development requirements

Run pip to install anta and its developement tools.

```
pip install 'anta[dev]'
```

> This command has to be done after you install repository with commands provided in previous section.

Then, tox is configued with few environment to run CI locally:

```bash
tox list
default environments:
clean  -> run the test driver with /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/bin/python3.9
py38   -> run the test driver with py38
py39   -> run the test driver with py39
py310  -> run the test driver with py310
lint   -> check the code style
type   -> check typing
report -> run the test driver with /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/bin/python3.9

additional environments:
3.8    -> run the test driver with 3.8
3.9    -> run the test driver with 3.9
3.10   -> run the test driver with 3.10
```

## Code linting

```bash
tox -e lint
[...]
lint: commands[0]> flake8 --max-line-length=165 --config=/dev/null anta
lint: commands[1]> flake8 --max-line-length=165 --config=/dev/null scripts
lint: commands[2]> flake8 --max-line-length=165 --config=/dev/null tests
lint: commands[3]> pylint anta

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

lint: commands[4]> pylint scripts

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 7.15/10, +2.85)

.pkg: _exit> python /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/lib/python3.9/site-packages/\
pyproject_api/_backend.py True setuptools.build_meta
  lint: OK (28.37=setup[7.03]+cmd[0.38,0.23,0.25,11.07,9.41] seconds)
  congratulations :) (28.45 seconds)
```

## Code Typing

```bash
tox -e type

type: commands[0]> mypy --config-file=pyproject.toml anta
Success: no issues found in 38 source files
type: commands[1]> mypy --config-file=pyproject.toml scripts
Success: no issues found in 6 source files
.pkg: _exit> python /home/tom/.pyenv/versions/3.9.9/envs/arista-anta/lib/python3.9/site-packages/\
pyproject_api/_backend.py True setuptools.build_meta
  type: OK (28.80=setup[24.54]+cmd[3.35,0.90] seconds)
  congratulations :) (28.89 seconds)
```

## Unit tests

To keep high quality code, we require to provide a Pytest for every tests implemented in ANTA.

All submodule should have its own pytest section under `tests/units/anta_tests/<submodule-name>`. In this directory, you should have 3 files:

- `__init__.py`: Just because it is used as a python module
- `data.py`: Where all your parametrize go. So all your test information should be located here
- `test_exc.py`: Pytest file with test definition.

A pytest definition should be similar to this template:

```python
# -*- coding: utf-8 -*-

"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.hardware import VerifyAdverseDrops
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_<TEST_NAME>

@pytest.mark.parametrize("test_data", INPUT_<TEST_NAME>, ids=generate_test_ids_list(INPUT_<TEST_NAME>))
def test_<TEST_CASE>(mocked_device: MagicMock, test_data: Any) -> None:
    """Check <TEST_CASE>."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = <TEST_CASE>(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
```

The `mocked_device` object is a fixture defined in Pytest to represent an InventoryDevice and the parametrize `test_data` is a list of dictionries with structure:

```python
INPUT_RUNNING_CONFIG: List[Dict[str, Any]] = [
  # Test Case #1
    {
        "name": "failure",
        "eos_data": ["blah blah"],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["blah blah"]
    },
    # Test Case #2
    {
      ...
    },
]
```

Where we have:

- `name`: Name of the test displayed by Pytest
- `eos_data`: a list of data coming from EOS.
- `side_effect`: defined for futur use.
- `expected_result`: Result we expect for this test
- `expected_messages`: Optional messages we expect for the test.

!!! info "Use Anta CLI to get test data"
    To complete this block, you can use [`anta debug`](./cli/debug.md) commands to get `AntaCommand` output to use in your test.

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

## Test your documentation

Writing documentation is crucial but managing links can be cumbersome. To be sure there is no 404, you can use [`muffet`](https://github.com/raviqqe/muffet) with this cli:

```bash
muffet -c 2 --color=always http://127.0.0.1:8000 -e fonts.gstatic.com
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](https://github.com/arista-netdevops-community/anta/tree/81ec7f90246879217d713c9873fa485ddcb0955e/.github/workflows).
We can view the result [here](https://github.com/arista-netdevops-community/anta/actions)
