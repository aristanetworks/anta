# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta._runner.py."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
import respx
from pydantic import ValidationError

from anta._runner import AntaRunner, AntaRunnerFilter
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"


class TestAntaRunner:
    """Test AntaRunner class."""

    def test_init(self) -> None:
        """Test basic initialization."""
        runner = AntaRunner(inventory=AntaInventory(), catalog=AntaCatalog(), manager=ResultManager())
        assert runner.manager is not None
        assert len(runner.inventory.devices) == 0
        assert len(runner.catalog.tests) == 0
        assert len(runner.manager.results) == 0

        # Check private attributes are initialized
        assert runner._selected_inventory is None
        assert runner._selected_tests is None
        assert runner._inventory_stats is None
        assert runner._total_tests == 0
        assert runner._potential_connections is None

        # Check default settings
        assert runner._settings.max_concurrency == 50000

    async def test_reset(self, inventory: AntaInventory) -> None:
        """Test AntaRunner.reset method."""
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        await runner.run(dry_run=True)

        # After a run, the following attributes should be set
        assert runner._selected_inventory is not None
        assert runner._selected_tests is not None
        assert runner._inventory_stats is not None
        assert runner._total_tests != 0
        assert runner._potential_connections is not None

        runner.reset()

        # After reset, the following attributes should be None
        assert runner._selected_inventory is None
        assert runner._selected_tests is None
        assert runner._inventory_stats is None
        assert runner._total_tests == 0
        assert runner._potential_connections is None

    async def test_dry_run(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner with dry-run mode."""
        caplog.set_level(logging.INFO)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        await runner.run(dry_run=True)

        # In dry-run mode, the selected inventory is the original inventory
        assert runner._selected_inventory == runner.inventory

        # In dry-run mode, the inventory stats total should match the original inventory length
        assert runner._inventory_stats is not None
        assert runner._inventory_stats.total == len(runner.inventory)

        assert "Dry-run mode, exiting before running the tests." in caplog.records[-1].message

    async def test_invalid_filters(self) -> None:
        """Test AntaRunner with invalid filters."""
        runner = AntaRunner(inventory=AntaInventory(), catalog=AntaCatalog())
        with pytest.raises(ValidationError, match="1 validation error for AntaRunnerFilter"):
            await runner.run(filters=AntaRunnerFilter(devices="invalid", tests=None, tags=None), dry_run=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("filters", "expected_devices", "expected_tests"),
        [
            pytest.param(
                AntaRunnerFilter(devices=None, tests=None, tags=None),
                3,
                27,
                id="all-tests",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests=None, tags={"leaf"}),
                2,
                6,
                id="1-tag",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests=None, tags={"leaf", "spine"}),
                3,
                9,
                id="2-tags",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags=None),
                3,
                5,
                id="filtered-tests",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags={"leaf"}),
                2,
                4,
                id="1-tag-filtered-tests",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests=None, tags={"invalid"}),
                0,
                0,
                id="invalid-tag",
            ),
            pytest.param(
                AntaRunnerFilter(devices=None, tests=None, tags={"dc1"}),
                0,
                0,
                id="device-tag-no-tests",
            ),
        ],
    )
    async def test_run_filters(self, caplog: pytest.LogCaptureFixture, filters: AntaRunnerFilter, expected_devices: int, expected_tests: int) -> None:
        """Test AntaRunner with different filters."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        await runner.run(filters, dry_run=True)

        # Check when all tests are filtered out
        if expected_devices == 0 and expected_tests == 0:
            assert runner._total_tests == 0
            assert runner._selected_tests is None
            msg = f"There are no tests matching the tags {filters.tags} to run in the current test catalog and device inventory, please verify your inputs."
            assert msg in caplog.messages
            return

        assert runner._selected_tests is not None
        assert len(runner._selected_tests) == expected_devices
        assert sum(len(tests) for tests in runner._selected_tests.values()) == expected_tests

    async def test_multiple_runs_no_manager(self) -> None:
        """Test multiple runs without a ResultManager instance."""
        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)

        # When no manager is provided, the instance attribute should be None
        assert runner.manager is None

        first_run_manager = await runner.run(dry_run=True)
        assert isinstance(first_run_manager, ResultManager)
        assert len(first_run_manager.results) == 27

        second_run_manager = await runner.run(dry_run=True)
        assert isinstance(second_run_manager, ResultManager)
        assert len(second_run_manager.results) == 27

        # Should still be None since no manager was provided
        assert runner.manager is None

    async def test_multiple_runs_with_manager(self) -> None:
        """Test multiple runs with a provided ResultManager instance."""
        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        manager = ResultManager()
        runner = AntaRunner(inventory=inventory, catalog=catalog, manager=manager)

        # When a manager is provided, the instance attribute should be set
        assert runner.manager is not None

        first_run_manager = await runner.run(dry_run=True)
        assert len(first_run_manager.results) == 27
        assert first_run_manager.results == runner.manager.results

        # When a manager is provided, results from subsequent runs are appended to the manager
        second_run_manager = await runner.run(dry_run=True)
        assert len(second_run_manager.results) == 54
        assert first_run_manager.results == second_run_manager.results

        # Check that the manager attribute is still set with the total results
        assert len(manager.results) == 54

    async def test_log_run_information_default(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner log information with default values."""
        caplog.set_level(logging.INFO)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        await runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 50000",
            "  Total potential connections: 300",
            f"  Max file descriptors: {runner._settings.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    async def test_log_run_information_concurrency_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner log run information with higher tests count than concurrency limit."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        runner._settings.max_concurrency = 20
        await runner.run(dry_run=True)

        warning = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled."
        assert warning in caplog.text

    @pytest.mark.skipif(os.name != "posix", reason="Veriy unlikely to happen on non-POSIX systems due to sys.maxsize")
    async def test_log_run_information_file_descriptor_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner log run information with higher connections count than file descriptor limit."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        runner._settings._file_descriptor_limit = 128
        await runner.run(dry_run=True)

        warning = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur."
        assert warning in caplog.text

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    @respx.mock
    async def test_run(self, inventory: AntaInventory) -> None:
        """Test AntaRunner regular run."""
        # Mock the eAPI requests
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip route vrf default").respond(
            json={"result": [{"vrfs": {"default": {"routes": {}}}}]}
        )
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_routing.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        results = await runner.run()

        assert len(results.results) == 15
        for result in results.results:
            assert result.result == "failure"
