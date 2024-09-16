# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import logging
import resource
from pathlib import Path
from unittest.mock import patch

import pytest

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.runner import adjust_rlimit_nofile, main, prepare_tests

from .test_models import FakeTest, FakeTestWithMissingTest

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


async def test_no_selected_device(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """Test that when the list of established device."""
    caplog.set_level(logging.INFO)
    manager = ResultManager()
    await main(manager, test_inventory, FAKE_CATALOG)

    assert "No reachable device was found." in [record.message for record in caplog.records]

    #  Reset logs and run with tags
    caplog.clear()
    await main(manager, test_inventory, FAKE_CATALOG, tags={"toto"})

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


async def test_prepare_tests_with_specific_tests(caplog: pytest.LogCaptureFixture, test_inventory: AntaInventory) -> None:
    """Test the runner prepare_tests function with specific tests."""
    caplog.set_level(logging.INFO)

    catalog: AntaCatalog = AntaCatalog.parse(str(DATA_DIR / "test_catalog_with_tags.yml"))
    selected_tests = prepare_tests(inventory=test_inventory, catalog=catalog, tags=None, tests={"VerifyMlagStatus", "VerifyUptime"})

    assert selected_tests is not None
    assert len(selected_tests) == 3
    assert sum(len(tests) for tests in selected_tests.values()) == 5


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
    assert (
        "There is an error when creating test tests.units.test_models.FakeTestWithMissingTest.\nIf this is not a custom test implementation: "
        "Please reach out to the maintainer team or open an issue on Github: https://github.com/aristanetworks/anta.\nTypeError: "
        "Can't instantiate abstract class FakeTestWithMissingTest without an implementation for abstract method 'test'" in caplog.messages
    )
