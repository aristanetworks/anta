# How to contribute to ANTA

Contribution model is based on a fork-model. Don't push to arista-netdevops-community/anta directly. Always do a branch in your forked repository and create a PR.

To help development, open your PR as soon as possible even in draft mode. It helps other to know on what you are working on and avoid duplicate PRs.

## Create a development environement

Run the following commands to create an ANTA development environement:

```bash
# Clone repository
$ git clone https://github.com/arista-netdevops-community/anta.git
$ cd anta

# Install ANTA in editable mode and its development tools
$ pip install -e .[dev]

# Verify installation
$ pip list -e
Package Version Editable project location
------- ------- -------------------------
anta    0.6.0   /mnt/lab/projects/anta
```

Then, [`tox`](https://tox.wiki/) is configued with few environments to run CI locally:

```bash
$ tox list -d
default environments:
clean  -> Erase previous coverage reports
lint   -> Check the code style
type   -> Check typing
py38   -> Run pytest with py38
py39   -> Run pytest with py39
py310  -> Run pytest with py310
py311  -> Run pytest with py311
report -> Generate coverage report
```

### Code linting

```bash
tox -e lint
[...]
lint: commands[0]> black --check --diff --color .
All done! ✨ 🍰 ✨
104 files would be left unchanged.
lint: commands[1]> isort --check --diff --color .
Skipped 7 files
lint: commands[2]> flake8 --max-line-length=165 --config=/dev/null anta
lint: commands[3]> flake8 --max-line-length=165 --config=/dev/null tests
lint: commands[4]> pylint anta

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

.pkg: _exit> python /Users/guillaumemulocher/.pyenv/versions/3.8.13/envs/anta/lib/python3.8/site-packages/pyproject_api/_backend.py True setuptools.build_meta
  lint: OK (19.26=setup[5.83]+cmd[1.50,0.76,1.19,1.20,8.77] seconds)
  congratulations :) (19.56 seconds)
```

### Code Typing

```bash
tox -e type

[...]
type: commands[0]> mypy --config-file=pyproject.toml anta
Success: no issues found in 52 source files
.pkg: _exit> python /Users/guillaumemulocher/.pyenv/versions/3.8.13/envs/anta/lib/python3.8/site-packages/pyproject_api/_backend.py True setuptools.build_meta
  type: OK (46.66=setup[24.20]+cmd[22.46] seconds)
  congratulations :) (47.01 seconds)
```

> NOTE: Typing is configured quite strictly, do not hesitate to reach out if you have any questions, struggles, nightmares.

## Unit tests

To keep high quality code, we require to provide a Pytest for every tests implemented in ANTA.

All submodule should have its own pytest section under `tests/units/anta_tests/<submodule-name>`. In this directory, you should have 3 files:

- `__init__.py`: Just because it is used as a python module
- `data.py`: Where all your parametrize go. So all your test information should be located here
- `test_exc.py`: Pytest file with test definition.

A pytest definition should be similar to this template:

```python
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
- `side_effect`: used to inject template and test parameters (look for some examples in the existing tests)
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

``` bash
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

> NOTE: It could happen that pre-commit and tox disagree on something, in that case please open an issue on Github so we can take a look.. It is most probably wrong configuration on our side.

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

### Checking links

Writing documentation is crucial but managing links can be cumbersome. To be sure there is no dead links, you can use [`muffet`](https://github.com/raviqqe/muffet) with the following command:

```bash
muffet -c 2 --color=always http://127.0.0.1:8000 -e fonts.gstatic.com
```

## Continuous Integration

GitHub actions is used to test git pushes and pull requests. The workflows are defined in this [directory](https://github.com/arista-netdevops-community/anta/tree/main/.github/workflows). We can view the results [here](https://github.com/arista-netdevops-community/anta/actions).
