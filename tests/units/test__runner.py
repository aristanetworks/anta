# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta._runner.py."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import ClassVar

import pytest
import respx
from pydantic import ValidationError

from anta._runner import AntaRunFilters, AntaRunner
from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.inventory import AntaInventory
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult as AntaTestResult
from anta.settings import DEFAULT_MAX_CONCURRENCY, DEFAULT_NOFILE, AntaRunnerSettings
from anta.tests.routing.generic import VerifyRoutingTableEntry

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"


class TestAntaRunner:
    """Test AntaRunner class."""

    def test_init_with_default_settings(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test initialization with default settings."""
        caplog.set_level(logging.DEBUG)
        default_settings = {"nofile": DEFAULT_NOFILE, "max_concurrency": DEFAULT_MAX_CONCURRENCY}

        runner = AntaRunner()

        assert f"AntaRunner initialized with settings: {default_settings}" in caplog.messages
        assert runner._settings

    def test_init_with_custom_env_settings(self, caplog: pytest.LogCaptureFixture, setenvvar: pytest.MonkeyPatch) -> None:
        """Test initialization with custom env settings."""
        caplog.set_level(logging.DEBUG)
        desired_settings = {"nofile": 1048576, "max_concurrency": 10000}
        setenvvar.setenv("ANTA_NOFILE", str(desired_settings["nofile"]))
        setenvvar.setenv("ANTA_MAX_CONCURRENCY", str(desired_settings["max_concurrency"]))

        runner = AntaRunner()

        assert f"AntaRunner initialized with settings: {desired_settings}" in caplog.messages
        assert runner._settings

    def test_init_with_provided_settings(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test initialization with provided settings."""
        caplog.set_level(logging.DEBUG)
        desired_settings = AntaRunnerSettings(nofile=1048576, max_concurrency=10000)

        runner = AntaRunner(settings=desired_settings)

        assert f"AntaRunner initialized with settings: {desired_settings.model_dump()}" in caplog.messages
        assert runner._settings

    async def test_dry_run(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run() in dry-run."""
        caplog.set_level(logging.INFO)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner()
        ctx = await runner.run(inventory, catalog, dry_run=True)

        # Validate the final context attributes
        assert ctx.selected_inventory == ctx.inventory == inventory
        assert len(ctx.manager) > 0
        assert ctx.manager.status == "unset"
        assert ctx.total_tests_scheduled > 0
        assert ctx.total_devices_filtered_by_tags == 0
        assert ctx.total_devices_unreachable == 0
        assert ctx.total_devices_selected_for_testing == ctx.total_devices_in_inventory == len(inventory)
        assert ctx.duration is not None

        assert "Dry-run mode, exiting before running the tests." in caplog.messages

    @pytest.mark.parametrize(
        ("filters", "expected_devices", "expected_tests"),
        [
            pytest.param(
                AntaRunFilters(devices=None, tests=None, tags=None),
                3,
                27,
                id="all-tests",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests=None, tags={"leaf"}),
                2,
                6,
                id="1-tag",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests=None, tags={"leaf", "spine"}),
                3,
                9,
                id="2-tags",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags=None),
                3,
                5,
                id="filtered-tests",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags={"leaf"}),
                2,
                4,
                id="1-tag-filtered-tests",
            ),
            pytest.param(
                AntaRunFilters(devices={"leaf1"}, tests=None, tags=None),
                1,
                9,
                id="filtered-devices",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests=None, tags={"invalid"}),
                0,
                0,
                id="invalid-tag",
            ),
            pytest.param(
                AntaRunFilters(devices={"invalid"}, tests=None, tags=None),
                0,
                0,
                id="invalid-device",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests={"invalid"}, tags=None),
                3,
                0,
                id="invalid-test",
            ),
            pytest.param(
                AntaRunFilters(devices=None, tests=None, tags={"dc1"}),
                1,
                0,
                id="device-tag-no-tests",
            ),
        ],
    )
    async def test_run_filters(self, caplog: pytest.LogCaptureFixture, filters: AntaRunFilters, expected_devices: int, expected_tests: int) -> None:
        """Test AntaRunner.run() with different filters."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner()
        ctx = await runner.run(inventory, catalog, filters=filters, dry_run=True)

        # Gather the warning message
        warning_msg = None
        if expected_devices == 0:
            msg = "The inventory is empty after filtering by tags/devices. "
            if filters.devices:
                msg += f"Devices filter: {', '.join(sorted(filters.devices))}. "
            if filters.tags:
                msg += f"Tags filter: {', '.join(sorted(filters.tags))}. "
            msg += "Exiting ..."
        elif expected_tests == 0:
            msg = "No tests scheduled to run after filtering by tags/tests. "
            if filters.tests:
                msg += f"Tests filter: {', '.join(sorted(filters.tests))}. "
            if filters.tags:
                msg += f"Tags filter: {', '.join(sorted(filters.tags))}. "
            msg += "Exiting ..."

        if warning_msg is not None:
            assert msg in ctx.warnings_at_setup
            assert msg in caplog.messages

        assert ctx.total_tests_scheduled == expected_tests
        assert ctx.total_devices_selected_for_testing == expected_devices

    async def test_run_invalid_filters(self) -> None:
        """Test AntaRunner.run() with invalid filters."""
        inventory = AntaInventory()
        catalog = AntaCatalog()
        runner = AntaRunner()

        with pytest.raises(ValidationError, match="1 validation error for AntaRunFilters"):
            await runner.run(inventory, catalog, filters=AntaRunFilters(devices="invalid"), dry_run=True)  # type: ignore[arg-type]

    async def test_run_provided_manager(self) -> None:
        """Test AntaRunner.run() with a provided ResultManager instance."""
        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        manager = ResultManager()
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog, manager, dry_run=True)
        assert isinstance(ctx.manager, ResultManager)
        assert ctx.manager is manager
        assert len(manager) == 27

    async def test_run_provided_manager_not_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run() with a provided non-empty ResultManager instance."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        manager = ResultManager()
        test = AntaTestResult(name="DC1-LEAF1A", test="VerifyNTP", categories=["system"], description="NTP Test")
        runner = AntaRunner()
        manager.add(test)

        ctx = await runner.run(inventory, catalog, manager, dry_run=True)
        assert isinstance(ctx.manager, ResultManager)
        assert ctx.manager is manager
        assert len(manager) == 28
        assert len(manager.device_stats) == ctx.total_devices_selected_for_testing + 1

        warning_msg = (
            "Appending new results to the provided ResultManager which already holds 1 results. Statistics in this run context are for the current execution only."
        )
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    async def test_run_empty_catalog(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run() with an empty AntaCatalog."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog()
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog)

        warning_msg = "The list of tests is empty. Exiting ..."
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    async def test_run_empty_inventory(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run() with an empty AntaInventory."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory()
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog)

        warning_msg = "The initial inventory is empty. Exiting ..."
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    @pytest.mark.parametrize("inventory", [{"reachable": False}], indirect=True)
    async def test_run_no_reachable_devices(self, caplog: pytest.LogCaptureFixture, inventory: AntaInventory) -> None:
        """Test AntaRunner.run() with an empty AntaInventory."""
        caplog.set_level(logging.WARNING)

        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog)
        assert ctx.total_devices_unreachable == ctx.total_devices_in_inventory
        assert "device-0" in ctx.devices_unreachable_at_setup

        warning_msg = "No reachable devices found for testing after connectivity checks. Exiting ..."
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    async def test_run_invalid_anta_test(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run() with a provided non-empty ResultManager instance."""
        caplog.set_level(logging.CRITICAL)

        class InvalidTest(AntaTest):
            """ANTA test that raises an exception when test is called."""

            categories: ClassVar[list[str]] = []
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

            def test(self) -> None:  # type: ignore[override]
                """Test function."""
                msg = "Test not implemented"
                raise NotImplementedError(msg)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        test_definition = AntaTestDefinition(test=InvalidTest, inputs=None)
        catalog = AntaCatalog(tests=[test_definition])
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog, dry_run=True)
        assert len(ctx.manager) == 0

        error_msg = (
            f"There is an error when creating test {__name__}.InvalidTest.\n"
            "If this is not a custom test implementation: "
            "Please reach out to the maintainer team or open an issue on Github: https://github.com/aristanetworks/anta.\n"
            "NotImplementedError: Test not implemented"
        )
        assert error_msg in caplog.messages

    async def test_log_run_information_default(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner._log_run_information with default settings."""
        caplog.set_level(logging.INFO)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner = AntaRunner()
        await runner.run(inventory, catalog, dry_run=True)

        expected_output = [
            "ANTA NRFU Dry Run Information",
            "Devices:",
            "  Total in initial inventory: 3",
            "  Selected for testing: 3",
            "Tests: 27 total scheduled",
            "Limits:",
            "  Max concurrent tests: 50000",
            "  Potential connections needed: 300",
            f"  File descriptors limit: {runner._settings.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    async def test_log_run_information_concurrency_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner._log_run_information with higher tests count than concurrency limit."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner_settings = AntaRunnerSettings(max_concurrency=20)
        runner = AntaRunner(settings=runner_settings)

        ctx = await runner.run(inventory, catalog, dry_run=True)

        warning_msg = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled. Please consult the ANTA FAQ."
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    @pytest.mark.skipif(os.name != "posix", reason="Very unlikely to happen on non-POSIX systems due to sys.maxsize")
    async def test_log_run_information_file_descriptor_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner._log_run_information with higher connections count than file descriptor limit."""
        caplog.set_level(logging.WARNING)

        inventory = AntaInventory.parse(filename=DATA_DIR / "test_inventory_with_tags.yml", username="anta", password="anta")
        catalog = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
        runner_settings = AntaRunnerSettings(nofile=128)
        runner = AntaRunner(settings=runner_settings)

        ctx = await runner.run(inventory, catalog, dry_run=True)

        warning_msg = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur. Please consult the ANTA FAQ."
        assert warning_msg in ctx.warnings_at_setup
        assert warning_msg in caplog.messages

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    @respx.mock
    async def test_run(self, inventory: AntaInventory) -> None:
        """Test AntaRunner.run()."""
        # Mock the eAPI requests
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip route vrf default").respond(
            json={"result": [{"vrfs": {"default": {"routes": {}}}}]}
        )
        tests = [AntaTestDefinition(test=VerifyRoutingTableEntry, inputs={"routes": [f"10.1.0.{i}"], "collect": "all"}) for i in range(5)]
        catalog = AntaCatalog(tests=tests)
        runner = AntaRunner()

        ctx = await runner.run(inventory, catalog)

        assert ctx.total_devices_selected_for_testing == 3
        assert ctx.total_tests_scheduled == 15
        assert len(ctx.warnings_at_setup) == 0
        assert len(ctx.manager) == 15
        for result in ctx.manager.results:
            assert result.result == "failure"
