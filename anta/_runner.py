# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner classes."""

from __future__ import annotations

import logging
from asyncio import Semaphore, gather
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from inspect import getcoroutinelocals
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from anta import GITHUB_SUGGESTION
from anta.inventory import AntaInventory
from anta.logger import anta_log_exception
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.settings import AntaRunnerSettings
from anta.tools import Catchtime

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from anta.catalog import AntaCatalog, AntaTestDefinition
    from anta.device import AntaDevice
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


class AntaRunFilters(BaseModel):
    """Define filters for an ANTA run.

    Filters determine which devices and tests to include in a run, and how to
    filter them with tags. This class is used by the `AntaRunner.run()` method.

    Attributes
    ----------
    devices : set[str] | None, optional
        Set of device names to run tests on. If `None`, includes all devices in
        the inventory. Commonly set via the NRFU CLI `--device/-d` option.
    tests : set[str] | None, optional
        Set of test names to run. If `None`, runs all available tests in the
        catalog. Commonly set via the NRFU CLI `--test/-t` option.
    tags : set[str] | None, optional
        Set of tags used to filter both devices and tests. A device or test
        must match any of the provided tags to be included. Commonly set via
        the NRFU CLI `--tags` option.
    established_only : bool, default=True
        When `True`, only includes devices with established connections in the
        test run.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    devices: set[str] | None = None
    tests: set[str] | None = None
    tags: set[str] | None = None
    established_only: bool = True


@dataclass
class AntaRunContext:
    """Store the complete context and results of an ANTA run.

    A unique context is created and returned per ANTA run.

    Attributes
    ----------
    inventory: AntaInventory
        Initial inventory of devices provided to the run.
    catalog: AntaCatalog
        Initial catalog of tests provided to the run.
    manager: ResultManager
        Manager with the final test results.
    filters: AntaRunFilters
        Provided filters to the run.
    selected_inventory: AntaInventory
        The final inventory of devices selected for testing.
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]]
        A mapping containing the final tests to be run per device.
    devices_filtered_at_setup: list[str]
        List of device names that were filtered during the inventory setup phase.
    devices_unreachable_at_setup: list[str]
        List of device names that were found unreachable during the inventory setup phase.
    warnings_at_setup: list[str]
        List of warnings caught during the setup phase.
    start_time: datetime | None
        Start time of the run. None if not set yet.
    end_time: datetime | None
        End time of the run. None if not set yet.
    """

    inventory: AntaInventory
    catalog: AntaCatalog
    manager: ResultManager
    filters: AntaRunFilters
    dry_run: bool = False

    # State populated during the run
    selected_inventory: AntaInventory = field(default_factory=AntaInventory)
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = field(default_factory=lambda: defaultdict(set))
    devices_filtered_at_setup: list[str] = field(default_factory=list)
    devices_unreachable_at_setup: list[str] = field(default_factory=list)
    warnings_at_setup: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def total_devices_in_inventory(self) -> int:
        """Total devices in the initial inventory provided to the run."""
        return len(self.inventory)

    @property
    def total_devices_filtered_by_tags(self) -> int:
        """Total devices filtered by tags at inventory setup."""
        return len(self.devices_filtered_at_setup)

    @property
    def total_devices_unreachable(self) -> int:
        """Total devices unreachable at inventory setup."""
        return len(self.devices_unreachable_at_setup)

    @property
    def total_devices_selected_for_testing(self) -> int:
        """Total devices selected for testing."""
        return len(self.selected_inventory)

    @property
    def total_tests_scheduled(self) -> int:
        """Total tests scheduled to run across all selected devices."""
        return sum(len(tests) for tests in self.selected_tests.values())

    @property
    def duration(self) -> timedelta | None:
        """Calculate the duration of the run. Returns None if start or end time is not set."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


# pylint: disable=too-few-public-methods
class AntaRunner:
    """Run and manage ANTA test execution.

    This class orchestrates the execution of ANTA tests across network devices. It handles
    inventory filtering, test selection, concurrent test execution, and result collection.
    An `AntaRunner` instance is stateless between runs. All necessary inputs like inventory
    and catalog are provided to the `run()` method.

    Attributes
    ----------
    _settings : AntaRunnerSettings
        Settings container for the runner. This can be provided during initialization;
        otherwise, it is loaded from environment variables by default. See the
        `AntaRunnerSettings` class definition in the `anta.settings` module for details.

    Notes
    -----
    After initializing an `AntaRunner` instance, tests should only be executed through
    the `run()` method. This method manages the complete test lifecycle including setup,
    execution, and cleanup.

    Examples
    --------
    ```python
    import asyncio

    from anta._runner import AntaRunner, AntaRunFilters
    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory

    inventory = AntaInventory.parse(
        filename="anta_inventory.yml",
        username="arista",
        password="arista",
    )
    catalog = AntaCatalog.parse(filename="anta_catalog.yml")

    # Create an ANTA runner
    runner = AntaRunner()

    # Run all tests
    first_run_results = asyncio.run(runner.run(inventory, catalog))

    # Run with filters
    second_run_results = asyncio.run(runner.run(inventory, catalog, filters=AntaRunFilters(tags={"leaf"})))
    ```
    """

    def __init__(self, settings: AntaRunnerSettings | None = None) -> None:
        """Initialize AntaRunner."""
        self._settings = settings if settings is not None else AntaRunnerSettings()
        logger.debug("AntaRunner initialized with settings: %s", self._settings.model_dump())

    async def run(
        self,
        inventory: AntaInventory,
        catalog: AntaCatalog,
        result_manager: ResultManager | None = None,
        filters: AntaRunFilters | None = None,
        *,
        dry_run: bool = False,
    ) -> AntaRunContext:
        """Run ANTA.

        Run workflow:

        1. Build the context object for the run.
        2. Set up the selected inventory, removing filtered/unreachable devices.
        3. Set up the selected tests, removing filtered tests.
        4. Prepare the `AntaTest` coroutines from the selected inventory and tests.
        5. Run the test coroutines if it is not a dry run.

        Parameters
        ----------
        inventory
            Inventory of network devices to test.
        catalog
            Catalog of tests to run.
        result_manager
            Manager for collecting and storing test results. If `None`, a new manager
            is returned for each run, otherwise the provided manager is used
            and results from subsequent runs are appended to it.
        filters
            Filters for the ANTA run. If `None`, run all tests on all devices.
        dry_run
            Dry-run mode flag. If `True`, run all setup steps but do not execute tests.

        Returns
        -------
        AntaRunContext
            The complete context and results of this ANTA run.
        """
        start_time = datetime.now(tz=timezone.utc)
        logger.info("ANTA run starting ...")

        ctx = AntaRunContext(
            inventory=inventory,
            catalog=catalog,
            manager=result_manager if result_manager is not None else ResultManager(),
            filters=filters if filters is not None else AntaRunFilters(),
            dry_run=dry_run,
            start_time=start_time,
        )

        if len(ctx.manager) > 0:
            msg = (
                f"Appending new results to the provided ResultManager which already holds {len(ctx.manager)} results. "
                "Statistics in this run context are for the current execution only."
            )
            self._log_warning_msg(msg=msg, ctx=ctx)

        if not ctx.catalog.tests:
            self._log_warning_msg(msg="The list of tests is empty. Exiting ...", ctx=ctx)
            ctx.end_time = datetime.now(tz=timezone.utc)
            return ctx

        with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
            # Set up inventory
            setup_inventory_ok = await self._setup_inventory(ctx)
            if not setup_inventory_ok:
                ctx.end_time = datetime.now(tz=timezone.utc)
                return ctx

            # Set up tests
            with Catchtime(logger=logger, message="Preparing Tests"):
                setup_tests_ok = self._setup_tests(ctx)
                if not setup_tests_ok:
                    ctx.end_time = datetime.now(tz=timezone.utc)
                    return ctx

            # Get test coroutines
            test_coroutines = self._get_test_coroutines(ctx)

        self._log_run_information(ctx)

        if ctx.dry_run:
            logger.info("Dry-run mode, exiting before running the tests.")
            self._close_test_coroutines(test_coroutines, ctx)
            ctx.end_time = datetime.now(tz=timezone.utc)
            return ctx

        if AntaTest.progress is not None:
            AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests ...", total=ctx.total_tests_scheduled)

        with Catchtime(logger=logger, message="Running Tests"):
            sem = Semaphore(self._settings.max_concurrency)

            async def run_with_sem(test_coro: Coroutine[Any, Any, TestResult]) -> TestResult:
                """Wrap the test coroutine with semaphore control."""
                async with sem:
                    return await test_coro

            results = await gather(*[run_with_sem(coro) for coro in test_coroutines])
            for res in results:
                ctx.manager.add(res)

        self._log_cache_statistics(ctx)

        ctx.end_time = datetime.now(tz=timezone.utc)
        return ctx

    async def _setup_inventory(self, ctx: AntaRunContext) -> bool:
        """Set up the inventory for the ANTA run.

        Returns True if the inventory setup was successful, otherwise False.
        """
        initial_device_names = set(ctx.inventory.keys())

        if not initial_device_names:
            self._log_warning_msg(msg="The initial inventory is empty. Exiting ...", ctx=ctx)
            return False

        # Filter the inventory based on the provided filters if any
        filtered_inventory = (
            ctx.inventory.get_inventory(tags=ctx.filters.tags, devices=ctx.filters.devices) if ctx.filters.tags or ctx.filters.devices else ctx.inventory
        )
        filtered_device_names = set(filtered_inventory.keys())
        ctx.devices_filtered_at_setup = sorted(initial_device_names - filtered_device_names)

        if not filtered_device_names:
            msg_parts = ["The inventory is empty after filtering by tags/devices."]
            if ctx.filters.devices:
                msg_parts.append(f"Devices filter: {', '.join(sorted(ctx.filters.devices))}.")
            if ctx.filters.tags:
                msg_parts.append(f"Tags filter: {', '.join(sorted(ctx.filters.tags))}.")
            msg_parts.append("Exiting ...")
            self._log_warning_msg(msg=" ".join(msg_parts), ctx=ctx)
            return False

        # In dry-run mode, set the selected inventory to the filtered inventory
        if ctx.dry_run:
            ctx.selected_inventory = filtered_inventory
            return True

        # Attempt to connect to devices that passed filters
        with Catchtime(logger=logger, message="Connecting to devices"):
            await filtered_inventory.connect_inventory()

        # Remove devices that are unreachable if required
        ctx.selected_inventory = filtered_inventory.get_inventory(established_only=True) if ctx.filters.established_only else filtered_inventory
        selected_device_names = set(ctx.selected_inventory.keys())
        ctx.devices_unreachable_at_setup = sorted(filtered_device_names - selected_device_names)

        if not selected_device_names:
            msg = "No reachable devices found for testing after connectivity checks. Exiting ..."
            self._log_warning_msg(msg=msg, ctx=ctx)
            return False

        return True

    def _setup_tests(self, ctx: AntaRunContext) -> bool:
        """Set up tests for the ANTA run.

        Returns True if the test setup was successful, otherwise False.
        """
        # Build indexes for the catalog. If `ctx.filters.tests` is set, filter the indexes based on these tests
        ctx.catalog.build_indexes(filtered_tests=ctx.filters.tests)

        # Create the device to tests mapping from the tags
        for device in ctx.selected_inventory.devices:
            if ctx.filters.tags:
                # If there are CLI tags, execute tests with matching tags for this device
                if not (matching_tags := ctx.filters.tags.intersection(device.tags)):
                    # The device does not have any selected tag, skipping
                    # This should not never happen because the device will already be filtered by `_setup_inventory`
                    continue
                ctx.selected_tests[device].update(ctx.catalog.get_tests_by_tags(matching_tags))
            else:
                # If there is no CLI tags, execute all tests that do not have any tags
                ctx.selected_tests[device].update(ctx.catalog.tag_to_tests[None])

                # Then add the tests with matching tags from device tags
                ctx.selected_tests[device].update(ctx.catalog.get_tests_by_tags(device.tags))

        if ctx.total_tests_scheduled == 0:
            msg_parts = ["No tests scheduled to run after filtering by tags/tests."]
            if ctx.filters.tests:
                msg_parts.append(f"Tests filter: {', '.join(sorted(ctx.filters.tests))}.")
            if ctx.filters.tags:
                msg_parts.append(f"Tags filter: {', '.join(sorted(ctx.filters.tags))}.")
            msg_parts.append("Exiting ...")
            self._log_warning_msg(msg=" ".join(msg_parts), ctx=ctx)
            return False

        return True

    def _get_test_coroutines(self, ctx: AntaRunContext) -> list[Coroutine[Any, Any, TestResult]]:
        """Get the test coroutines for the ANTA run."""
        coros = []
        for device, test_definitions in ctx.selected_tests.items():
            for test_def in test_definitions:
                try:
                    coros.append(test_def.test(device=device, inputs=test_def.inputs).test())
                except Exception as exc:  # noqa: BLE001, PERF203
                    # An AntaTest instance is potentially user-defined code.
                    # We need to catch everything and exit gracefully with an error message.
                    msg = "\n".join(
                        [
                            f"There is an error when creating test {test_def.test.__module__}.{test_def.test.__name__}.",
                            f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                        ],
                    )
                    anta_log_exception(exc, msg, logger)
        return coros

    def _close_test_coroutines(self, coros: list[Coroutine[Any, Any, TestResult]], ctx: AntaRunContext) -> None:
        """Close the test coroutines. Used in dry-run."""
        for coro in coros:
            # Get the AntaTest instance from the coroutine locals, can be in `args` when decorated
            coro_locals = getcoroutinelocals(coro)
            test = coro_locals.get("self") or coro_locals.get("args")
            if isinstance(test, AntaTest):
                ctx.manager.add(test.result)
            elif test and isinstance(test, tuple) and isinstance(test[0], AntaTest):
                ctx.manager.add(test[0].result)
            else:
                logger.error("Coroutine %s does not have an AntaTest instance.", coro)
            coro.close()

    def _log_run_information(self, ctx: AntaRunContext) -> None:
        """Log ANTA run information and potential resource limit warnings."""
        logger.info("Initial inventory contains %s devices", ctx.total_devices_in_inventory)

        if ctx.total_devices_filtered_by_tags > 0:
            device_list_str = ", ".join(sorted(ctx.devices_filtered_at_setup))
            logger.info("%d devices excluded by name/tag filters: %s", ctx.total_devices_filtered_by_tags, device_list_str)

        if ctx.total_devices_unreachable > 0:
            device_list_str = ", ".join(sorted(ctx.devices_unreachable_at_setup))
            logger.info("%d devices found unreachable after connection attempts: %s", ctx.total_devices_unreachable, device_list_str)

        logger.info("%d devices selected for testing", ctx.total_devices_selected_for_testing)
        logger.info("%d total tests scheduled across all selected devices", ctx.total_tests_scheduled)

        # Log debugs for runner settings
        logger.debug("Max concurrent tests configured: %d", self._settings.max_concurrency)
        if (potential_connections := ctx.selected_inventory.max_potential_connections) is not None:
            logger.debug("Potential device connections estimated for this run: %d", potential_connections)
        logger.debug("System file descriptor limit configured: %d", self._settings.file_descriptor_limit)

        # Log warnings for potential resource limits
        if ctx.total_tests_scheduled > self._settings.max_concurrency:
            msg = (
                f"Tests count ({ctx.total_tests_scheduled}) exceeds concurrent limit ({self._settings.max_concurrency}). "
                "Tests will be throttled. Please consult the ANTA FAQ."
            )
            self._log_warning_msg(msg=msg, ctx=ctx)
        if potential_connections is not None and potential_connections > self._settings.file_descriptor_limit:
            msg = (
                f"Potential connections ({potential_connections}) exceeds file descriptor limit ({self._settings.file_descriptor_limit}). "
                "Connection errors may occur. Please consult the ANTA FAQ."
            )
            self._log_warning_msg(msg=msg, ctx=ctx)

    def _log_cache_statistics(self, ctx: AntaRunContext) -> None:
        """Log cache statistics for each device in the inventory."""
        for device in ctx.selected_inventory.devices:
            if device.cache_statistics is not None:
                msg = (
                    f"Cache statistics for '{device.name}': "
                    f"{device.cache_statistics['cache_hits']} hits / {device.cache_statistics['total_commands_sent']} "
                    f"command(s) ({device.cache_statistics['cache_hit_ratio']})"
                )
                logger.debug(msg)
            else:
                logger.debug("Caching is not enabled on %s", device.name)

    def _log_warning_msg(self, msg: str, ctx: AntaRunContext) -> None:
        """Log the provided message at WARNING level and add it to the context warnings_at_setup list."""
        logger.warning(msg)
        ctx.warnings_at_setup.append(msg)
