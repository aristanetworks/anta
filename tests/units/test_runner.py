# Copyright (c) 2023-2024 Arista Networks, Inc.
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

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager

# Import as Result to avoid PytestCollectionWarning
from anta.result_manager.models import TestResult as Result
from anta.runner import get_coroutines, log_run_information, main, prepare_tests, run

from .test_models import FakeTest, FakeTestWithMissingTest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Sequence
    from warnings import WarningMessage

if os.name == "posix":
    # The function is not defined on non-POSIX system
    import resource

    from anta.runner import adjust_rlimit_nofile

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"
FAKE_CATALOG: AntaCatalog = AntaCatalog.from_list([(FakeTest, None)])


async def test_empty_tests(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test that when the list of tests is empty, a log is raised."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, inventory, AntaCatalog())

    assert len(caplog.record_tuples) == 1
    assert "The list of tests is empty, exiting" in caplog.records[0].message


async def test_empty_inventory(caplog: pytest.LogCaptureFixture) -> None:
    """Test that when the Inventory is empty, a log is raised."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, AntaInventory(), FAKE_CATALOG)
    assert len(caplog.record_tuples) == 3
    assert "The inventory is empty, exiting" in caplog.records[1].message


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
    msg = f'No reachable device {f"matching the tags {tags} " if tags else ""}was found.{f" Selected devices: {devices} " if devices is not None else ""}'
    assert msg in caplog.messages


@pytest.mark.skipif(os.name != "posix", reason="Cannot run this test on Windows")
def test_adjust_rlimit_nofile_valid_env(caplog: pytest.LogCaptureFixture) -> None:
    """Test adjust_rlimit_nofile with valid environment variables."""
    # pylint: disable=E0606
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


@pytest.mark.skipif(os.name != "posix", reason="Cannot run this test on Windows")
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


@pytest.mark.skipif(os.name == "posix", reason="Run this test on Windows only")
async def test_check_runner_log_for_windows(caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
    """Test log output for Windows host regarding rlimit."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    # Using dry-run to shorten the test
    await main(manager, inventory, FAKE_CATALOG, dry_run=True)
    assert "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors." in caplog.records[-3].message


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
        assert "Running on a non-POSIX system, cannot adjust the maximum number of file descriptors." in caplog.records[-3].message


@pytest.mark.parametrize(
    ("inventory", "tags", "tests", "devices_count", "tests_count"),
    [
        pytest.param({"filename": "test_inventory_with_tags.yml"}, None, None, 3, 27, id="all-tests"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, {"leaf"}, None, 2, 6, id="1-tag"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, {"leaf", "spine"}, None, 3, 9, id="2-tags"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, None, {"VerifyMlagStatus", "VerifyUptime"}, 3, 5, id="filtered-tests"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, {"leaf"}, {"VerifyMlagStatus", "VerifyUptime"}, 2, 4, id="1-tag-filtered-tests"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, {"invalid"}, None, 0, 0, id="invalid-tag"),
        pytest.param({"filename": "test_inventory_with_tags.yml"}, {"dc1"}, None, 0, 0, id="device-tag-no-tests"),
    ],
    indirect=["inventory"],
)
async def test_prepare_tests(
    caplog: pytest.LogCaptureFixture, inventory: AntaInventory, tags: set[str], tests: set[str], devices_count: int, tests_count: int
) -> None:
    """Test the runner prepare_tests function with specific tests."""
    caplog.set_level(logging.WARNING)
    catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / "test_catalog_with_tags.yml"))
    selected_tests = prepare_tests(inventory=inventory, catalog=catalog, tags=tags, tests=tests)
    if selected_tests is None:
        msg = f"There are no tests matching the tags {tags} to run in the current test catalog and device inventory, please verify your inputs."
        assert msg in caplog.messages
        return
    assert selected_tests is not None
    assert len(selected_tests) == devices_count
    assert sum(len(tests) for tests in selected_tests.values()) == tests_count


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


async def test_get_coroutines_deprecation(inventory: AntaInventory) -> None:
    """Test that get_coroutines raises a DeprecationWarning."""
    # Create selected tests with a single test
    selected_tests = prepare_tests(inventory=inventory, catalog=FAKE_CATALOG, tags=None, tests=None)

    manager = ResultManager()

    with pytest.warns(DeprecationWarning) as warning_records:
        assert selected_tests is not None
        coroutines = get_coroutines(selected_tests, manager)

        # Verify the warning
        assert len(warning_records) == 1
        warning: WarningMessage = warning_records[0]
        assert "get_coroutines" in str(warning.message)
        assert "deprecated" in str(warning.message)
        assert warning.category is DeprecationWarning

        # Verify the stacklevel
        assert warning.filename == __file__

        # Verify return type
        assert isinstance(coroutines, list)
        assert len(coroutines) == 1
        assert hasattr(coroutines[0], "__await__")

        # Await the coroutine to avoid RuntimeWarning
        await coroutines[0]


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


async def test_run_with_zero_limit() -> None:
    """Test that run raises RuntimeError when limit is 0."""
    mock_result = Mock(spec=Result)
    generator = create_test_generator([mock_result])

    with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
        await run(generator, limit=0).__anext__()


async def test_run_with_negative_limit() -> None:
    """Test that run raises RuntimeError when limit is negative."""
    mock_result = Mock(spec=Result)
    generator = create_test_generator([mock_result])

    with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
        await run(generator, limit=-1).__anext__()


async def test_run_with_empty_generator(caplog: pytest.LogCaptureFixture) -> None:
    """Test run behavior with an empty generator."""
    caplog.set_level(logging.DEBUG)

    results = [result async for result in run(EmptyGenerator(), limit=1)]  # type: ignore[arg-type]
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
    completed_results = [result async for result in run(generator, limit=2)]

    # Verify all results were returned
    assert len(completed_results) == 3

    # Verify logging messages
    assert "Concurrency limit reached: 2 tests running" in caplog.text
    assert any("Completed" in msg and "Pending count:" in msg for msg in caplog.messages)


async def test_run_immediate_stop_iteration(caplog: pytest.LogCaptureFixture) -> None:
    """Test run behavior when generator raises StopIteration immediately."""
    caplog.set_level(logging.DEBUG)

    results = [result async for result in run(EmptyGenerator(), limit=1)]  # type: ignore[arg-type]
    assert len(results) == 0
    assert "All tests have been added to the pending set" in caplog.text
    assert "No pending tests and all tests have been processed. Exiting" in caplog.text


def test_log_run_information_basic_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Test basic logging output with typical values."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(5, 3), test_count=10, max_concurrency=20, max_connections=5, file_descriptor_limit=1024)

    assert "ANTA NRFU Run Information" in caplog.text
    assert "Devices: 5 total, 3 established" in caplog.text
    assert "Tests: 10 total" in caplog.text
    assert "Max concurrent tests: 20" in caplog.text
    assert "Max connections per device: 5" in caplog.text
    assert "Max file descriptors: 1024" in caplog.text
    assert len(caplog.records) == 1


def test_log_run_information_unlimited_connections(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging when max_connections is None (unlimited)."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(3, 2), test_count=10, max_concurrency=20, max_connections=None, file_descriptor_limit=1024)

    assert "Max connections per device: Unlimited" in caplog.text
    assert "Running with unlimited HTTP connections" in caplog.text
    assert "file descriptor limit (1024)" in caplog.text
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_log_run_information_exceeding_concurrency(caplog: pytest.LogCaptureFixture) -> None:
    """Test warning when test count exceeds max concurrency."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(2, 2), test_count=30, max_concurrency=20, max_connections=5, file_descriptor_limit=1024)

    assert "Tests count (30) exceeds concurrent limit (20)" in caplog.text
    assert "Tests will be throttled" in caplog.text
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_log_run_information_exceeding_file_descriptor_limit(caplog: pytest.LogCaptureFixture) -> None:
    """Test warning when potential connections exceed file descriptor limit."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(5, 5), test_count=10, max_concurrency=20, max_connections=300, file_descriptor_limit=1024)

    assert "Potential connections (1500) exceeds file descriptor limit (1024)" in caplog.text
    assert "Connection errors may occur" in caplog.text
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_log_run_information_multiple_warnings(caplog: pytest.LogCaptureFixture) -> None:
    """Test multiple warning conditions occurring simultaneously."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(3, 3), test_count=50, max_concurrency=20, max_connections=400, file_descriptor_limit=1024)

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 2
    assert "Tests count (50) exceeds concurrent limit (20)" in caplog.text
    assert "Potential connections (1200) exceeds file descriptor limit (1024)" in caplog.text


def test_log_run_information_no_warnings(caplog: pytest.LogCaptureFixture) -> None:
    """Test case where no warnings should be logged."""
    caplog.set_level(logging.INFO)

    log_run_information(device_count=(2, 2), test_count=10, max_concurrency=20, max_connections=10, file_descriptor_limit=1024)

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 0
    assert len(caplog.records) == 1
