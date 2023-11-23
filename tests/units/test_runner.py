# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.runner.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta import logger
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import main

from .test_models import FakeTest

if TYPE_CHECKING:
    from pytest import LogCaptureFixture

FAKE_CATALOG: AntaCatalog = AntaCatalog.from_list([(FakeTest, None)])


@pytest.mark.asyncio
async def test_runner_empty_tests(caplog: LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """
    Test that when the list of tests is empty, a log is raised

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    logger.setup_logging("INFO")
    manager = ResultManager()
    await main(manager, test_inventory, AntaCatalog())

    assert len(caplog.record_tuples) == 1
    assert "The list of tests is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio
async def test_runner_empty_inventory(caplog: LogCaptureFixture) -> None:
    """
    Test that when the Inventory is empty, a log is raised

    caplog is the pytest fixture to capture logs
    """
    logger.setup_logging("INFO")
    manager = ResultManager()
    inventory = AntaInventory()
    await main(manager, inventory, FAKE_CATALOG)
    assert len(caplog.record_tuples) == 1
    assert "The inventory is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio
async def test_runner_no_selected_device(caplog: LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """
    Test that when the list of established device

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    logger.setup_logging("INFO")
    manager = ResultManager()
    await main(manager, test_inventory, FAKE_CATALOG)

    assert "No device in the established state 'True' was found. There is no device to run tests against, exiting" in [record.message for record in caplog.records]

    #  Reset logs and run with tags
    caplog.clear()
    await main(manager, test_inventory, FAKE_CATALOG, tags=["toto"])

    assert "No device in the established state 'True' matching the tags ['toto'] was found. There is no device to run tests against, exiting" in [
        record.message for record in caplog.records
    ]
