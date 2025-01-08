# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import main, prepare_tests

from .test_models import FakeTest, FakeTestWithMissingTest

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
