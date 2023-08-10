# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
conftest.py - used to store anta specific fixtures used for tests
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest import Metafunc

# Load fixtures from dedicated file tests/lib/fixture.py
pytest_plugins = [
    "tests.lib.fixture",
]

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
    if "tests.units.anta_tests" in metafunc.module.__package__:
        # This is a unit test for an AntaTest subclass
        metafunc.parametrize("data", metafunc.module.DATA, ids=build_test_id)
