# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
conftest.py - used to store anta specific fixtures used for tests
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pytest import Metafunc

# Load fixtures from dedicated file tests/lib/fixture.py
# As well as pytest_asyncio plugin to test co-routines
pytest_plugins = [
    "tests.lib.fixture",
    "pytest_asyncio",
]

# Enable nice assert messages
# https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("tests.lib.anta")

# Placeholder to disable logging of some external libs
for _ in ("asyncio", "httpx"):
    logging.getLogger(_).setLevel(logging.CRITICAL)


def build_test_id(val: dict[str, Any]) -> str:
    """
    build id for a unit test of an AntaTest subclass

    {
        "name": "meaniful test name",
        "test": <AntaTest instance>,
        ...
    }
    """
    return f"{val['test'].__module__}.{val['test'].__name__}-{val['name']}"


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """
    This function is called during test collection.
    It will parametrize test cases based on the `DATA` data structure defined in `tests.units.anta_tests` modules.
    See `tests/units/anta_tests/README.md` for more information on how to use it.
    Test IDs are generated using the `build_test_id` function above.
    """
    if "tests.units.anta_tests" in metafunc.module.__package__:
        # This is a unit test for an AntaTest subclass
        metafunc.parametrize("data", metafunc.module.DATA, ids=build_test_id)
