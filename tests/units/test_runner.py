# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.runner.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta.inventory import AntaInventory
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main

if TYPE_CHECKING:
    from pytest import LogCaptureFixture


@pytest.mark.asyncio
async def test_runner_empty_tests(caplog: LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """
    Test that when the list of tests is empty, a log is raised

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    manager = ResultManager()
    await main(manager, test_inventory, [], tags=[])

    assert len(caplog.record_tuples) == 1
    assert "The list of tests is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio
async def test_runner_empty_inventory(caplog: LogCaptureFixture) -> None:
    """
    Test that when the Inventory is empty, a log is raised

    caplog is the pytest fixture to capture logs
    """
    manager = ResultManager()
    inventory = AntaInventory()
    # This is not vaidated in this test
    tests: list[tuple[type[AntaTest], AntaTest.Input]] = [(AntaTest, {})]  # type: ignore[type-abstract]
    await main(manager, inventory, tests, tags=[])

    assert len(caplog.record_tuples) == 1
    assert "The inventory is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio
async def test_runner_no_selected_device(caplog: LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """
    Test that when the list of established device

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    manager = ResultManager()
    # This is not vaidated in this test
    tests: list[tuple[type[AntaTest], AntaTest.Input]] = [(AntaTest, {})]  # type: ignore[type-abstract]

    await main(manager, test_inventory, tests, tags=[])

    assert "No device in the established state 'True' was found. There is no device to run tests against, exiting" in [record.message for record in caplog.records]

    #  Reset logs and run with tags
    caplog.clear()
    await main(manager, test_inventory, tests, tags=["toto"])

    assert "No device in the established state 'True' matching the tags ['toto'] was found. There is no device to run tests against, exiting" in [
        record.message for record in caplog.records
    ]
