# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta._runner.py."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import respx
from pydantic import ValidationError

from anta._runner import AntaRunner, AntaRunnerFilter
from anta.catalog import AntaCatalog
from anta.result_manager import ResultManager
from anta.settings import AntaRunnerSchedulingStrategy

if TYPE_CHECKING:
    from anta.inventory import AntaInventory

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"


class TestAntaRunnerBasic:
    """Test AntaRunner basic functionality."""

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "manager": ResultManager()}], indirect=True
    )
    def test_init(self, anta_runner: AntaRunner) -> None:
        """Test basic initialization."""
        assert anta_runner.manager is not None
        assert len(anta_runner.inventory.devices) == 3
        assert len(anta_runner.catalog.tests) == 11
        assert len(anta_runner.manager.results) == 0

        # Check private attributes are initialized
        assert anta_runner._selected_inventory is None
        assert anta_runner._selected_tests is None
        assert anta_runner._inventory_stats is None
        assert anta_runner._total_tests == 0
        assert anta_runner._potential_connections is None

        # Check default settings
        assert anta_runner._settings.max_concurrency == 10000
        assert anta_runner._settings.scheduling_strategy == "device-by-device"
        assert anta_runner._settings.scheduling_tests_per_device == 100

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_reset(self, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.reset method."""
        await anta_runner.run(dry_run=True)

        # After a run, the following attributes should be set
        assert anta_runner._selected_inventory is not None
        assert anta_runner._selected_tests is not None
        assert anta_runner._inventory_stats is not None
        assert anta_runner._total_tests != 0
        assert anta_runner._potential_connections is not None

        anta_runner.reset()

        # After reset, the following attributes should be None
        assert anta_runner._selected_inventory is None
        assert anta_runner._selected_tests is None
        assert anta_runner._inventory_stats is None
        assert anta_runner._total_tests == 0
        assert anta_runner._potential_connections is None


class TestAntaRunnerRun:
    """Test AntaRunner.run method."""

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_run_dry_run(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.run method in dry-run mode."""
        caplog.set_level(logging.INFO)

        await anta_runner.run(dry_run=True)

        # In dry-run mode, the selected inventory is the original inventory
        assert anta_runner._selected_inventory is not None
        assert len(anta_runner._selected_inventory) == len(anta_runner.inventory)

        # In dry-run mode, the inventory stats total should match the original inventory length
        assert anta_runner._inventory_stats is not None
        assert anta_runner._inventory_stats.total == len(anta_runner.inventory)

        assert "Dry-run mode, exiting before running the tests." in caplog.records[-2].message

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_run_invalid_filters(self, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.run method with invalid scope."""
        with pytest.raises(ValidationError, match="1 validation error for AntaRunnerFilter"):
            await anta_runner.run(filters=AntaRunnerFilter(devices="invalid", tests=None, tags=None), dry_run=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("anta_runner", "filters", "expected_devices", "expected_tests"),
        [
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests=None, tags=None),
                3,
                27,
                id="all-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests=None, tags={"leaf"}),
                2,
                6,
                id="1-tag",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests=None, tags={"leaf", "spine"}),
                3,
                9,
                id="2-tags",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags=None),
                3,
                5,
                id="filtered-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags={"leaf"}),
                2,
                4,
                id="1-tag-filtered-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests=None, tags={"invalid"}),
                0,
                0,
                id="invalid-tag",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerFilter(devices=None, tests=None, tags={"dc1"}),
                0,
                0,
                id="device-tag-no-tests",
            ),
        ],
        indirect=["anta_runner"],
    )
    async def test_run_filters(
        self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner, filters: AntaRunnerFilter, expected_devices: int, expected_tests: int
    ) -> None:
        """Test AntaRunner.run method with different filters."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(filters, dry_run=True)

        # Check when all tests are filtered out
        if expected_devices == 0 and expected_tests == 0:
            assert anta_runner._total_tests == 0
            assert anta_runner._selected_tests is None
            msg = f"There are no tests matching the tags {filters.tags} to run in the current test catalog and device inventory, please verify your inputs."
            assert msg in caplog.messages
            return

        assert anta_runner._selected_tests is not None
        assert len(anta_runner._selected_tests) == expected_devices
        assert sum(len(tests) for tests in anta_runner._selected_tests.values()) == expected_tests

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_multiple_runs_no_manager(self, anta_runner: AntaRunner) -> None:
        """Test multiple runs without a ResultManager instance."""
        assert anta_runner.manager is None

        first_run_manager = await anta_runner.run(dry_run=True)
        assert isinstance(first_run_manager, ResultManager)
        assert len(first_run_manager.results) == 27

        second_run_manager = await anta_runner.run(dry_run=True)
        assert isinstance(second_run_manager, ResultManager)
        assert len(second_run_manager.results) == 27

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "manager": ResultManager()}], indirect=True
    )
    async def test_multiple_runs_with_manager(self, anta_runner: AntaRunner) -> None:
        """Test multiple runs with a provided ResultManager instance."""
        assert anta_runner.manager is not None

        first_run_manager = await anta_runner.run(dry_run=True)
        assert len(first_run_manager.results) == 27
        assert first_run_manager.results == anta_runner.manager.results

        # When a manager is provided, results from subsequent runs are appended to the manager
        second_run_manager = await anta_runner.run(dry_run=True)
        assert len(second_run_manager.results) == 54
        assert first_run_manager.results == second_run_manager.results

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    @respx.mock
    async def test_run_device_by_device_strategy(self, inventory: AntaInventory) -> None:
        """Test AntaRunner with device-by-device scheduling strategy."""
        # Mock the eAPI requests
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip route vrf default").respond(
            json={"result": [{"vrfs": {"default": {"routes": {}}}}]}
        )

        # Setup the objects required for the test
        manager = ResultManager()
        catalog: AntaCatalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_routing.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        runner._settings.scheduling_strategy = AntaRunnerSchedulingStrategy.DEVICE_BY_DEVICE
        runner._settings.scheduling_tests_per_device = 2
        filters = AntaRunnerFilter()
        await runner._setup_inventory(filters)
        runner._setup_tests(filters)
        generator = runner._test_generator()

        # Run the tests
        async for result in generator:
            manager.add(await result)

        # Check that indices 0-4 all have name "device-0"
        assert all(result.name == "device-0" for result in manager.results[0:4])

        # Check that indices 5-9 all have name "device-1"
        assert all(result.name == "device-1" for result in manager.results[5:9])

        # Check that indices 10-14 all have name "device-2"
        assert all(result.name == "device-2" for result in manager.results[10:14])

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    @respx.mock
    async def test_device_by_count_strategy(self, inventory: AntaInventory) -> None:
        """Test AntaRunner with device-by-count scheduling strategy."""
        # Mock the eAPI requests
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip route vrf default").respond(
            json={"result": [{"vrfs": {"default": {"routes": {}}}}]}
        )

        # Setup the objects required for the test
        manager = ResultManager()
        catalog: AntaCatalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_routing.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        runner._settings.scheduling_strategy = AntaRunnerSchedulingStrategy.DEVICE_BY_COUNT
        runner._settings.scheduling_tests_per_device = 2
        filters = AntaRunnerFilter()
        await runner._setup_inventory(filters)
        runner._setup_tests(filters)
        generator = runner._test_generator()

        # Run the tests
        async for result in generator:
            manager.add(await result)

        # Check that indices 0-1 all have name "device-0", 2-3 all have name "device-1", and 4-5 all have name "device-2"
        device_names = ["device-0", "device-1", "device-2"]
        for index, res in enumerate(manager.results[:-3]):
            assert res.name == device_names[(index % 6) // 2]

        # The last 3 results should be "device-0", "device-1", "device-2" since there is no more tests to run
        for index, name in enumerate(device_names):
            assert manager.results[-3 + index].name == name

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    @respx.mock
    async def test_round_robin_strategy(self, inventory: AntaInventory) -> None:
        """Test AntaRunner with round-robin scheduling strategy."""
        # Mock the eAPI requests
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip route vrf default").respond(
            json={"result": [{"vrfs": {"default": {"routes": {}}}}]}
        )

        # Setup the objects required for the test
        manager = ResultManager()
        catalog: AntaCatalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_routing.yml")
        runner = AntaRunner(inventory=inventory, catalog=catalog)
        runner._settings.scheduling_strategy = AntaRunnerSchedulingStrategy.ROUND_ROBIN
        runner._settings.scheduling_tests_per_device = 2
        filters = AntaRunnerFilter()
        await runner._setup_inventory(filters)
        runner._setup_tests(filters)
        generator = runner._test_generator()

        # Run the tests
        async for result in generator:
            manager.add(await result)

        # Round-robin between devices
        device_names = ["device-0", "device-1", "device-2"]
        for index, res in enumerate(manager.results):
            assert res.name == device_names[index % 3]


class TestAntaRunnerLogging:
    """Test AntaRunner logging."""

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_log_run_information_default(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with default values."""
        caplog.set_level(logging.INFO)

        await anta_runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 10000",
            "  Total potential connections: 300",
            f"  Max file descriptors: {anta_runner._settings.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 20}], indirect=True
    )
    async def test_log_run_information_concurrency_limit(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with higher tests count than concurrency limit."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(dry_run=True)

        warning = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled."
        assert warning in caplog.text

    @pytest.mark.skipif(os.name != "posix", reason="Veriy unlikely to happen on non-POSIX systems due to sys.maxsize")
    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "nofile": 128}], indirect=True)
    async def test_log_run_information_file_descriptor_limit(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with higher connections count than file descriptor limit."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(dry_run=True)

        warning = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur."
        assert warning in caplog.text
