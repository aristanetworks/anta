# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.runner.py."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.catalog import AntaCatalog
from anta.runner import prepare_tests

from .test_models import FakeTest

if TYPE_CHECKING:
    from anta.inventory import AntaInventory

if os.name == "posix":
    # The function is not defined on non-POSIX system
    import resource

    from anta.runner import adjust_rlimit_nofile

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"
FAKE_CATALOG: AntaCatalog = AntaCatalog.from_list([(FakeTest, None)])


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
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


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.skipif(os.name != "posix", reason="Cannot run this test on Windows")
def test_adjust_rlimit_nofile_invalid_env(caplog: pytest.LogCaptureFixture) -> None:
    """Test adjust_rlimit_nofile with invalid environment variables."""
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


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.skipif(os.name != "posix", reason="Cannot run this test on Windows")
def test_adjust_rlimit_nofile_value_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test adjust_rlimit_nofile with invalid environment variables."""
    with (
        caplog.at_level(logging.DEBUG),
        patch.dict("os.environ", {"ANTA_NOFILE": "666"}),
        patch("anta.runner.resource.getrlimit") as getrlimit_mock,
        patch("anta.runner.resource.setrlimit") as setrlimit_mock,
    ):
        # Simulate the default system limits
        system_limits = (8192, 1048576)

        # Setup getrlimit mock return value
        getrlimit_mock.return_value = system_limits

        # Simulate setrlimit behavior raising ValueError
        def side_effect_setrlimit(_resource_id: int, _limits: tuple[int, int]) -> None:
            msg = "not allowed to raise maximum limit"
            raise ValueError(msg)

        setrlimit_mock.side_effect = side_effect_setrlimit

        result = adjust_rlimit_nofile()

        # Assert the limits were *NOT* updated as expected
        assert result == system_limits
        assert "Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: 8192 | Hard Limit: 1048576" in caplog.text
        assert caplog.records[-1].levelname == "WARNING"
        assert "Failed to set soft limit for open file descriptors for the current ANTA process" in caplog.records[-1].getMessage()

        setrlimit_mock.assert_called_once_with(resource.RLIMIT_NOFILE, (666, 1048576))


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
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
