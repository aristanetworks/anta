# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from httpx import Limits

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager

# Import as Result to avoid PytestCollectionWarning
from anta.result_manager.models import TestResult as Result
from anta.runner import RunnerContext, _log_run_information, _run, _setup_inventory, _setup_tests, main

from .test_models import FakeTest, FakeTestWithMissingTest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Sequence


DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"
FAKE_CATALOG: AntaCatalog = AntaCatalog.from_list([(FakeTest, None)])


async def test_empty_tests(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test that when the list of tests is empty, a log is raised."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, inventory, AntaCatalog())

    # On Windows, there is an extra log message when the runner context tries
    # to adjust the file descriptor limit at the beginning of the main function.
    if os.name != "posix":
        record_tuples = 2
        record_index = 1
    else:
        record_tuples = 1
        record_index = 0

    assert len(caplog.record_tuples) == record_tuples
    assert "The list of tests is empty, exiting" in caplog.records[record_index].message


async def test_empty_inventory(caplog: pytest.LogCaptureFixture) -> None:
    """Test that when the Inventory is empty, a log is raised."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, AntaInventory(), FAKE_CATALOG)

    # On Windows, there is an extra log message when the runner context tries
    # to adjust the file descriptor limit at the beginning of the main function.
    if os.name != "posix":
        record_tuples = 4
        record_index = 2
    else:
        record_tuples = 3
        record_index = 1

    assert len(caplog.record_tuples) == record_tuples
    assert "The inventory is empty, exiting" in caplog.records[record_index].message


@pytest.mark.parametrize(
    ("inventory", "tags", "devices"),
    [
        pytest.param({"count": 1, "reachable": False}, None, None, id="not-reachable"),
        pytest.param({"filename": "test_inventory_with_tags.yml", "reachable": False}, {"leaf"}, None, id="not-reachable-with-tag"),
        pytest.param({"count": 1, "reachable": True}, {"invalid-tag"}, None, id="reachable-with-invalid-tag"),
        pytest.param({"filename": "test_inventory_with_tags.yml", "reachable": True}, None, {"invalid-device"}, id="reachable-with-invalid-device"),
        pytest.param({"filename": "test_inventory_with_tags.yml", "reachable": False}, None, {"leaf1"}, id="not-reachable-with-device"),
        pytest.param({"filename": "test_inventory_with_tags.yml", "reachable": False}, {"leaf"}, {"leaf1"}, id="not-reachable-with-device-and-tag"),
        pytest.param({"filename": "test_inventory_with_tags.yml", "reachable": False}, {"invalid"}, {"invalid-device"}, id="reachable-with-invalid-tag-and-device"),
    ],
    indirect=["inventory"],
)
async def test_no_selected_device(caplog: pytest.LogCaptureFixture, inventory: AntaInventory, tags: set[str], devices: set[str]) -> None:
    """Test that when the list of established devices is empty a log is raised."""
    caplog.set_level(logging.WARNING)
    manager = ResultManager()
    await main(manager, inventory, FAKE_CATALOG, tags=tags, devices=devices)
    msg = f"No reachable device {f'matching the tags {tags} ' if tags else ''}was found.{f' Selected devices: {devices} ' if devices is not None else ''}"
    assert msg in caplog.messages


@pytest.mark.skipif(os.name == "posix", reason="Run this test on Windows only")
async def test_check_runner_log_for_windows(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test log output for Windows host regarding rlimit."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    # Using dry-run to shorten the test
    await main(manager, inventory, FAKE_CATALOG, dry_run=True)
    assert "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors." in caplog.text


# We could instead merge multiple coverage report together but that requires more work than just this.
@pytest.mark.skipif(os.name != "posix", reason="Fake non-posix for coverage")
async def test_check_runner_log_for_windows_fake(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test log output for Windows host regarding rlimit."""
    with patch("os.name", new="win32"):
        del sys.modules["anta.runner"]
        from anta.runner import main  # pylint: disable=W0621

        caplog.set_level(logging.INFO)
        manager = ResultManager()
        # Using dry-run to shorten the test
        await main(manager, inventory, FAKE_CATALOG, dry_run=True)
        assert "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors." in caplog.text


@pytest.mark.parametrize(
    ("runner_context", "devices_count", "tests_count"),
    [
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": None,
                "tests": None,
                "dry_run": True,
            },
            3,
            27,
            id="all-tests",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": {"leaf"},
                "tests": None,
                "dry_run": True,
            },
            2,
            6,
            id="1-tag",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": {"leaf", "spine"},
                "tests": None,
                "dry_run": True,
            },
            3,
            9,
            id="2-tags",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": None,
                "tests": {"VerifyMlagStatus", "VerifyUptime"},
                "dry_run": True,
            },
            3,
            5,
            id="filtered-tests",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": {"leaf"},
                "tests": {"VerifyMlagStatus", "VerifyUptime"},
                "dry_run": True,
            },
            2,
            4,
            id="1-tag-filtered-tests",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": {"invalid"},
                "tests": None,
                "dry_run": True,
            },
            0,
            0,
            id="invalid-tag",
        ),
        pytest.param(
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "tags": {"dc1"},
                "tests": None,
                "dry_run": True,
            },
            0,
            0,
            id="device-tag-no-tests",
        ),
    ],
    indirect=["runner_context"],
)
async def test_setup_tests(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext, devices_count: int, tests_count: int) -> None:
    """Test the runner setup_tests function."""
    caplog.set_level(logging.WARNING)

    # _setup_inventory should be called first to populate selected_inventory and inventory_stats in runner_context
    with pytest.raises(RuntimeError, match="The inventory is not set in the ANTA run context. Make sure to run ANTA from the main function."):
        _setup_tests(runner_context)

    await _setup_inventory(runner_context)
    result = _setup_tests(runner_context)
    if result is False:
        msg = f"There are no tests matching the tags {runner_context.tags} to run in the current test catalog and device inventory, please verify your inputs."
        assert msg in caplog.messages
        return

    assert runner_context.selected_tests is not None
    assert len(runner_context.selected_tests) == devices_count
    assert sum(len(tests) for tests in runner_context.selected_tests.values()) == tests_count


@pytest.mark.parametrize(
    "runner_context",
    [
        {
            "inventory": "test_inventory_with_tags.yml",
            "catalog": "test_catalog_with_tags.yml",
            "dry_run": True,
        },
    ],
    indirect=["runner_context"],
)
async def test_log_run_information_default(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext) -> None:
    """Test the runner _log_run_information function with default values."""
    caplog.set_level(logging.INFO)

    # _setup_inventory should be called first to populate selected_inventory and inventory_stats in runner_context
    with pytest.raises(RuntimeError, match="The inventory stats are not set in the ANTA run context. Make sure to run ANTA from the main function."):
        _log_run_information(runner_context)

    await _setup_inventory(runner_context)
    _setup_tests(runner_context)
    _log_run_information(runner_context)

    expected_output = [
        "ANTA NRFU Run Information",
        "Devices:",
        "  Total: 3",
        "  Selected: 0 (dry-run mode)",
        "Tests: 27 total",
        "Limits:",
        "  Max concurrent tests: 10000",
        "  Total potential connections: 300",
        "  Max file descriptors: 16384",
    ]
    for line in expected_output:
        assert line in caplog.text


@pytest.mark.parametrize(
    "runner_context",
    [
        {
            "inventory": "test_inventory_with_tags.yml",
            "catalog": "test_catalog_with_tags.yml",
            "httpx_limits": Limits(max_connections=5, max_keepalive_connections=5),
            "dry_run": True,
        },
    ],
    indirect=["runner_context"],
)
async def test_log_run_information_max_connections(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext) -> None:
    """Test the runner _log_run_information function with custom max connections."""
    caplog.set_level(logging.INFO)

    # _setup_inventory should be called first to populate selected_inventory and inventory_stats in runner_context
    with pytest.raises(RuntimeError, match="The inventory stats are not set in the ANTA run context. Make sure to run ANTA from the main function."):
        _log_run_information(runner_context)

    await _setup_inventory(runner_context)
    _setup_tests(runner_context)
    _log_run_information(runner_context)

    expected_output = [
        "ANTA NRFU Run Information",
        "Devices:",
        "  Total: 3",
        "  Selected: 0 (dry-run mode)",
        "Tests: 27 total",
        "Limits:",
        "  Max concurrent tests: 10000",
        "  Total potential connections: 15",
        "  Max file descriptors: 16384",
    ]
    for line in expected_output:
        assert line in caplog.text


@pytest.mark.parametrize(
    "runner_context",
    [
        {
            "inventory": "test_inventory_with_tags.yml",
            "catalog": "test_catalog_with_tags.yml",
            "httpx_limits": Limits(max_connections=None, max_keepalive_connections=None),
            "dry_run": True,
        },
    ],
    indirect=["runner_context"],
)
async def test_log_run_information_unlimited(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext) -> None:
    """Test the runner _log_run_information function with unlimited max connections."""
    caplog.set_level(logging.WARNING)

    await _setup_inventory(runner_context)
    _setup_tests(runner_context)
    _log_run_information(runner_context)

    warning = "Running with unlimited connections. Connection errors may occur due to file descriptor limit (16384)."
    assert warning in caplog.text


@pytest.mark.parametrize(
    "runner_context",
    [
        {
            "inventory": "test_inventory_with_tags.yml",
            "catalog": "test_catalog_with_tags.yml",
            "max_concurrency": 20,
            "dry_run": True,
        },
    ],
    indirect=["runner_context"],
)
async def test_log_run_information_concurrency_limit(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext) -> None:
    """Test the runner _log_run_information function with higher tests count than concurrency limit."""
    caplog.set_level(logging.WARNING)

    await _setup_inventory(runner_context)
    _setup_tests(runner_context)
    _log_run_information(runner_context)

    warning = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled."
    assert warning in caplog.text


@pytest.mark.parametrize(
    "runner_context",
    [
        {
            "inventory": "test_inventory_with_tags.yml",
            "catalog": "test_catalog_with_tags.yml",
            "file_descriptor_limit": 128,
            "dry_run": True,
        },
    ],
    indirect=["runner_context"],
)
async def test_log_run_information_file_descriptor(caplog: pytest.LogCaptureFixture, runner_context: RunnerContext) -> None:
    """Test the runner _log_run_information function with higher connections count than file descriptor limit."""
    caplog.set_level(logging.WARNING)

    await _setup_inventory(runner_context)
    _setup_tests(runner_context)
    _log_run_information(runner_context)

    warning = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur."
    assert warning in caplog.text


async def test_dry_run(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test that when dry_run is True, no tests are run."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, inventory, FAKE_CATALOG, dry_run=True)
    assert "Dry-run mode, exiting before running the tests." in caplog.records[-1].message


async def test_cannot_create_test(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test that when an Exception is raised during test instantiation, it is caught and a log is raised."""
    caplog.set_level(logging.CRITICAL)
    manager = ResultManager()
    catalog = AntaCatalog.from_list([(FakeTestWithMissingTest, None)])  # type: ignore[type-abstract]
    await main(manager, inventory, catalog)
    msg = (
        "There is an error when creating test tests.units.test_models.FakeTestWithMissingTest.\nIf this is not a custom test implementation: "
        "Please reach out to the maintainer team or open an issue on Github: https://github.com/aristanetworks/anta.\nTypeError: "
    )
    msg += (
        "Can't instantiate abstract class FakeTestWithMissingTest without an implementation for abstract method 'test'"
        if sys.version_info >= (3, 12)
        else "Can't instantiate abstract class FakeTestWithMissingTest with abstract method test"
    )
    assert msg in caplog.messages


# Helper classes and functions for testing _run function of the runner module
class EmptyGenerator:
    """Helper class to create an empty async generator."""

    def __aiter__(self) -> AsyncIterator[Coroutine[Any, Any, Result]]:
        """Make this class an async iterator."""
        return self

    async def __anext__(self) -> Coroutine[Any, Any, Result]:
        """Raise StopAsyncIteration."""
        raise StopAsyncIteration


async def mock_test_coro(result: Result) -> Result:
    """Mock coroutine simulating a test."""
    # Simulate some work
    await asyncio.sleep(0.1)
    return result


async def create_test_generator(results: Sequence[Result]) -> AsyncGenerator[Coroutine[Any, Any, Result], None]:
    """Create a test generator yielding mock test coroutines."""
    for result in results:
        yield mock_test_coro(result)


# Tests for the _run function of the runner module
async def test_run_with_zero_limit() -> None:
    """Test that run raises RuntimeError when limit is 0."""
    mock_result = Mock(spec=Result)
    generator = create_test_generator([mock_result])

    with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
        await _run(generator, limit=0).__anext__()


async def test_run_with_negative_limit() -> None:
    """Test that run raises RuntimeError when limit is negative."""
    mock_result = Mock(spec=Result)
    generator = create_test_generator([mock_result])

    with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
        await _run(generator, limit=-1).__anext__()


async def test_run_with_empty_generator(caplog: pytest.LogCaptureFixture) -> None:
    """Test run behavior with an empty generator."""
    caplog.set_level(logging.DEBUG)

    results = [result async for result in _run(EmptyGenerator(), limit=1)]  # type: ignore[arg-type]
    assert len(results) == 0
    assert "All tests have been added to the pending set" in caplog.text
    assert "No pending tests and all tests have been processed. Exiting" in caplog.text


async def test_run_with_concurrent_limit(caplog: pytest.LogCaptureFixture) -> None:
    """Test run behavior with concurrent limit."""
    caplog.set_level(logging.DEBUG)

    # Create 3 mock results
    results = [Mock(spec=Result) for _ in range(3)]
    generator = create_test_generator(results)

    # Run with limit of 2 to test concurrency limit
    completed_results = [result async for result in _run(generator, limit=2)]

    # Verify all results were returned
    assert len(completed_results) == 3

    # Verify logging messages
    assert "Concurrency limit reached: 2 tests running" in caplog.text
    assert any("Completed" in msg and "Pending count:" in msg for msg in caplog.messages)


async def test_run_immediate_stop_iteration(caplog: pytest.LogCaptureFixture) -> None:
    """Test run behavior when generator raises StopIteration immediately."""
    caplog.set_level(logging.DEBUG)

    results = [result async for result in _run(EmptyGenerator(), limit=1)]  # type: ignore[arg-type]
    assert len(results) == 0
    assert "All tests have been added to the pending set" in caplog.text
    assert "No pending tests and all tests have been processed. Exiting" in caplog.text
