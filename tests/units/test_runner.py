# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import logging
import resource
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta import logger
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import adjust_rlimit_nofile, main, prepare_tests

if TYPE_CHECKING:
    from typing import Any, Callable

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"

@pytest.mark.parametrize(
    ("test_inventory", "test_catalog"),
    [
        pytest.param("test_inventory_large.yml", "test_catalog_large.yml", id="large-50_devices-7688_tests"),
        pytest.param("test_inventory_medium.yml", "test_catalog_medium.yml", id="medium-6_devices-228_tests"),
        pytest.param("test_inventory.yml", "test_catalog.yml", id="small-3_devices-3_tests"),
    ],
    indirect=True,
)
def test_runner(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory, test_catalog: AntaCatalog, aio_benchmark: Callable[..., Any]) -> None:
    """Test and benchmark ANTA runner.

    caplog is the pytest fixture to capture logs.
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    aio_benchmark(main, manager, test_inventory, test_catalog)


@pytest.mark.asyncio()
async def test_runner_empty_tests(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """Test that when the list of tests is empty, a log is raised.

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, test_inventory, AntaCatalog())

    assert len(caplog.record_tuples) == 1
    assert "The list of tests is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio()
async def test_runner_empty_inventory(caplog: pytest.LogCaptureFixture, test_catalog: AntaCatalog) -> None:
    """Test that when the Inventory is empty, a log is raised.

    caplog is the pytest fixture to capture logs
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    inventory = AntaInventory()
    await main(manager, inventory, test_catalog)
    assert len(caplog.record_tuples) == 1
    assert "The inventory is empty, exiting" in caplog.records[0].message


@pytest.mark.asyncio()
async def test_runner_no_selected_device(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory, test_catalog: AntaCatalog) -> None:
    """Test that when there is no reachable device, a log is raised.

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, test_inventory, test_catalog)

    assert "No reachable device was found." in [record.message for record in caplog.records]

    #  Reset logs and run with tags
    caplog.clear()
    await main(manager, test_inventory, test_catalog, tags={"toto"})

    assert "No reachable device matching the tags {'toto'} was found." in [record.message for record in caplog.records]


def test_adjust_rlimit_nofile_valid_env(caplog: pytest.LogCaptureFixture) -> None:
    """Test adjust_rlimit_nofile with valid environment variables."""
    with (
        caplog.at_level(logging.DEBUG),
        patch.dict("os.environ", {"ANTA_NOFILE": "20480"}),
        patch("anta.runner.resource.getrlimit") as getrlimit_mock,
        patch("anta.runner.resource.setrlimit") as setrlimit_mock,
    ):
        # Simulate the default system limits
        system_limits = (8192, 1048576)

        # Setup getrlimit mock return value
        getrlimit_mock.return_value = system_limits

        # Simulate setrlimit behavior
        def side_effect_setrlimit(resource_id: int, limits: tuple[int, int]) -> None:
            _ = resource_id
            getrlimit_mock.return_value = (limits[0], limits[1])

        setrlimit_mock.side_effect = side_effect_setrlimit

        result = adjust_rlimit_nofile()

        # Assert the limits were updated as expected
        assert result == (20480, 1048576)
        assert "Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: 8192 | Hard Limit: 1048576" in caplog.text
        assert "Setting soft limit for open file descriptors for the current ANTA process to 20480" in caplog.text

        setrlimit_mock.assert_called_once_with(resource.RLIMIT_NOFILE, (20480, 1048576))


def test_adjust_rlimit_nofile_invalid_env(caplog: pytest.LogCaptureFixture) -> None:
    """Test adjust_rlimit_nofile with valid environment variables."""
    with (
        caplog.at_level(logging.DEBUG),
        patch.dict("os.environ", {"ANTA_NOFILE": "invalid"}),
        patch("anta.runner.resource.getrlimit") as getrlimit_mock,
        patch("anta.runner.resource.setrlimit") as setrlimit_mock,
    ):
        # Simulate the default system limits
        system_limits = (8192, 1048576)

        # Setup getrlimit mock return value
        getrlimit_mock.return_value = system_limits

        # Simulate setrlimit behavior
        def side_effect_setrlimit(resource_id: int, limits: tuple[int, int]) -> None:
            _ = resource_id
            getrlimit_mock.return_value = (limits[0], limits[1])

        setrlimit_mock.side_effect = side_effect_setrlimit

        result = adjust_rlimit_nofile()

        # Assert the limits were updated as expected
        assert result == (16384, 1048576)
        assert "The ANTA_NOFILE environment variable value is invalid" in caplog.text
        assert caplog.records[0].levelname == "WARNING"
        assert "Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: 8192 | Hard Limit: 1048576" in caplog.text
        assert "Setting soft limit for open file descriptors for the current ANTA process to 16384" in caplog.text

        setrlimit_mock.assert_called_once_with(resource.RLIMIT_NOFILE, (16384, 1048576))


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    ("tags", "expected_tests_count", "expected_devices_count"),
    [
        (None, 22, 3),
        ({"leaf"}, 9, 3),
        ({"invalid_tag"}, 0, 0),
    ],
    ids=["no_tags", "leaf_tag", "invalid_tag"],
)
async def test_prepare_tests(
    caplog: pytest.LogCaptureFixture,
    test_inventory: AntaInventory,
    tags: set[str] | None,
    expected_tests_count: int,
    expected_devices_count: int,
) -> None:
    """Test the runner prepare_tests function."""
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)

    catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / "test_catalog_with_tags.yml"))
    selected_tests = prepare_tests(inventory=test_inventory, catalog=catalog, tags=tags, tests=None)

    if selected_tests is None:
        assert expected_tests_count == 0
        expected_log = f"There are no tests matching the tags {tags} to run in the current test catalog and device inventory, please verify your inputs."
        assert expected_log in caplog.text
    else:
        assert len(selected_tests) == expected_devices_count
        assert sum(len(tests) for tests in selected_tests.values()) == expected_tests_count


@pytest.mark.asyncio()
async def test_prepare_tests_with_specific_tests(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """Test the runner prepare_tests function with specific tests."""
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)

    catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / "test_catalog_with_tags.yml"))
    selected_tests = prepare_tests(inventory=test_inventory, catalog=catalog, tags=None, tests={"VerifyMlagStatus", "VerifyUptime"})

    assert selected_tests is not None
    assert len(selected_tests) == 3
    assert sum(len(tests) for tests in selected_tests.values()) == 5


@pytest.mark.asyncio()
async def test_runner_dry_run(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """Test that when dry_run is True, no tests are run.

    caplog is the pytest fixture to capture logs
    test_inventory is a fixture that gives a default inventory for tests
    """
    logger.setup_logging(logger.Log.INFO)
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    catalog_path = Path(__file__).parent.parent / "data" / "test_catalog.yml"
    catalog = AntaCatalog.parse(catalog_path)

    await main(manager, test_inventory, catalog, dry_run=True)

    # Check that the last log contains Dry-run
    assert "Dry-run" in caplog.records[-1].message
