# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner classes."""

from __future__ import annotations

import logging
from asyncio import Semaphore, gather
from collections import defaultdict
from dataclasses import dataclass, field
from inspect import getcoroutinelocals
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from anta import GITHUB_SUGGESTION
from anta.cli.console import console
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


# TODO: Update docstring
@dataclass
class AntaRunStatistics:
    """Store various statistics of an ANTA run.

    This class maintains counters for tracking how the device inventory is filtered
    during test setup.

    Attributes
    ----------
    total : int
        Total number of devices in the original inventory before filtering.
    filtered_by_tags : int
        Number of devices excluded due to tag filtering.
    connection_failed : int
        Number of devices that failed to establish a connection.
    established : int
        Number of devices with successfully established connections that are
        included in the final test run.
    """

    total_tests: int = 0
    total_devices: int = 0
    filtered_by_tags_devices: int = 0
    connection_failed_devices: int = 0
    established_devices: int = 0


# TODO: Update docstring
class AntaRunFilters(BaseModel):
    """Define a filter for an ANTA run.

    The filter determines which devices and tests to include in a run, and how to
    filter them with tags. This class is used with the `AntaRunner.run()` method.

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


# TODO: Update docstring
@dataclass
class AntaRunnerContext:
    """Store an AntaRunner run context."""

    inventory: AntaInventory
    catalog: AntaCatalog
    filters: AntaRunFilters
    dry_run: bool = False

    # Attributes set during setup phases in each run
    selected_inventory: AntaInventory = field(default_factory=AntaInventory)
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = field(default_factory=lambda: defaultdict(set))
    run_statistics: AntaRunStatistics = field(default_factory=AntaRunStatistics)


# TODO: Update docstring
# pylint: disable=too-few-public-methods
class AntaRunner:
    """Run and manage ANTA test execution.

    This class orchestrates the execution of ANTA tests across network devices. It handles
    inventory filtering, test selection, concurrent test execution, and result collection.

    Attributes
    ----------
    inventory : AntaInventory
        Inventory of network devices to test.
    catalog : AntaCatalog
        Catalog of available tests to run.
    manager : ResultManager | None, optional
        Manager for collecting and storing test results. If `None`, a new manager
        is returned for each run, otherwise the provided manager is used
        and results from subsequent runs are appended to it.
    _selected_inventory : AntaInventory | None
        Internal state of filtered inventory for current run.
    _selected_tests : defaultdict[AntaDevice, set[AntaTestDefinition]] | None
        Mapping of devices to their selected tests for current run.
    _run_statistics : AntaRunStatistics | None
        Statistics about inventory filtering for current run.
    _total_tests : int
        Total number of tests to run in current execution.
    _potential_connections : float | None
        Total potential concurrent connections needed for current run.
        `None` if unknown.
    _settings : AntaRunnerSettings
        Internal settings loaded from environment variables. See the class definition
        in the `anta.settings` module for details.

    Notes
    -----
    After initializing an `AntaRunner` instance, tests should only be executed through
    the `run()` method. This method manages the complete test lifecycle including setup,
    execution, and cleanup.

    All internal methods and state (prefixed with `_`) are managed by the `run()` method
    and should not be called directly. The internal state is reset between runs to
    ensure clean execution.


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
    runner = AntaRunner(inventory=inventory, catalog=catalog)

    # Run all tests
    first_run_results = asyncio.run(runner.run())

    # Run with filters
    second_run_results = asyncio.run(runner.run(scope=AntaRunFilters(tags={"leaf"})))
    ```
    """

    def __init__(self, settings: AntaRunnerSettings | None = None) -> None:
        """Initialize AntaRunner."""
        self._settings = settings if settings is not None else AntaRunnerSettings()
        logger.debug("AntaRunner initialized with settings: %s", self._settings.model_dump())

    # TODO: Add knob to clear the manager
    # TODO: Update docstring
    async def run(  # noqa: D417
        self,
        inventory: AntaInventory,
        catalog: AntaCatalog,
        result_manager: ResultManager | None = None,
        filters: AntaRunFilters | None = None,
        *,
        dry_run: bool = False,
    ) -> ResultManager:
        """Run ANTA.

        Parameters
        ----------
        filters
            Filters for the ANTA run. If None, runs all tests on all devices.
        dry_run
            Dry-run mode flag. If True, runs all setup steps but does not execute tests.
        """
        ctx = AntaRunnerContext(
            inventory=inventory,
            catalog=catalog,
            filters=filters if filters is not None else AntaRunFilters(),
            dry_run=dry_run,
        )
        result_manager = result_manager if result_manager is not None else ResultManager()

        if not ctx.catalog.tests:
            logger.warning("The list of tests is empty, exiting")
            return result_manager

        with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
            # Set up inventory
            if not await self._setup_inventory(ctx):
                return result_manager

            # Set up tests
            with Catchtime(logger=logger, message="Preparing Tests"):
                if not self._setup_tests(ctx):
                    return result_manager

            # Log run information
            self._log_run_information(ctx)

            # Build test coroutines
            test_coroutines = self._get_test_coroutines(ctx)

        if ctx.dry_run:
            logger.info("Dry-run mode, exiting before running the tests.")
            for coro in test_coroutines:
                # Get the AntaTest instance from the coroutine locals, can be in `args` when decorated
                coro_locals = getcoroutinelocals(coro)
                test = coro_locals.get("self") or coro_locals.get("args", (None))[0]
                if isinstance(test, AntaTest):
                    result_manager.add(test.result)
                else:
                    logger.error("Coroutine %s does not have an AntaTest instance.", coro)
                coro.close()
            return result_manager

        if AntaTest.progress is not None:
            AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=ctx.run_statistics.total_tests)

        with Catchtime(logger=logger, message="Running Tests"):
            sem = Semaphore(self._settings.max_concurrency)

            async def run_with_sem(test_coro: Coroutine[Any, Any, TestResult]) -> TestResult:
                """Wrap the test coroutine with semaphore control."""
                async with sem:
                    return await test_coro

            results = await gather(*[run_with_sem(coro) for coro in test_coroutines])
            for res in results:
                result_manager.add(res)

        self._log_cache_statistics(ctx)
        return result_manager

    async def _setup_inventory(self, ctx: AntaRunnerContext) -> bool:
        """Set up the inventory for the ANTA run."""
        total_devices = len(ctx.inventory)

        # In dry-run mode, set the selected inventory to the full inventory
        if ctx.dry_run:
            ctx.selected_inventory = ctx.inventory
            ctx.run_statistics.total_devices = total_devices
            return True

        # If the inventory is empty, exit
        if total_devices == 0:
            logger.warning("The inventory is empty, exiting")
            return False

        # Filter the inventory based on the provided filters if any
        filtered_inventory = (
            ctx.inventory.get_inventory(tags=ctx.filters.tags, devices=ctx.filters.devices) if ctx.filters.tags or ctx.filters.devices else ctx.inventory
        )

        # Connect to devices
        with Catchtime(logger=logger, message="Connecting to devices"):
            await filtered_inventory.connect_inventory()

        # Remove devices that are unreachable if required
        ctx.selected_inventory = filtered_inventory.get_inventory(established_only=True) if ctx.filters.established_only else filtered_inventory

        # If there are no devices in the inventory after filtering, exit
        if not ctx.selected_inventory.devices:
            # Build message parts
            tag_msg = f"matching the tags {ctx.filters.tags} " if ctx.filters.tags else ""
            device_msg = f" Selected devices: {ctx.filters.devices} " if ctx.filters.devices else ""
            logger.warning("No reachable device %swas found.%s", tag_msg, device_msg)
            return False

        # TODO: Add unreachable devices to the result manager

        # Update the run statistics
        ctx.run_statistics.total_devices = total_devices
        ctx.run_statistics.filtered_by_tags_devices = total_devices - len(filtered_inventory)
        ctx.run_statistics.connection_failed_devices = len(filtered_inventory) - len(ctx.selected_inventory)
        ctx.run_statistics.established_devices = len(ctx.selected_inventory)

        return True

    def _setup_tests(self, ctx: AntaRunnerContext) -> bool:
        """Set up tests for the ANTA run."""
        # Build indexes for the catalog. If `ctx.filters.tests` is set, filter the indexes based on these tests
        ctx.catalog.build_indexes(filtered_tests=ctx.filters.tests)

        total_tests = 0

        # Create the device to tests mapping from the tags
        for device in ctx.selected_inventory.devices:
            if ctx.filters.tags:
                # If there are CLI tags, execute tests with matching tags for this device
                if not (matching_tags := ctx.filters.tags.intersection(device.tags)):
                    # The device does not have any selected tag, skipping
                    continue
                ctx.selected_tests[device].update(ctx.catalog.get_tests_by_tags(matching_tags))
            else:
                # If there is no CLI tags, execute all tests that do not have any tags
                ctx.selected_tests[device].update(ctx.catalog.tag_to_tests[None])

                # Then add the tests with matching tags from device tags
                ctx.selected_tests[device].update(ctx.catalog.get_tests_by_tags(device.tags))

            total_tests += len(ctx.selected_tests[device])

        if total_tests == 0:
            tag_msg = f" matching the tags {ctx.filters.tags} " if ctx.filters.tags else " "
            logger.warning(
                "There are no tests%sto run in the current test catalog and device inventory, please verify your inputs.",
                tag_msg,
            )
            return False

        # Update the run statistics
        ctx.run_statistics.total_tests = total_tests

        return True

    def _get_test_coroutines(self, ctx: AntaRunnerContext) -> list[Coroutine[Any, Any, TestResult]]:
        """Get the test coroutines for the ANTA run with semaphore control."""
        coros = []
        for device, test_definitions in ctx.selected_tests.items():
            for test_def in test_definitions:
                try:
                    coros.append(test_def.test(device=device, inputs=test_def.inputs).test())
                except Exception as exc:  # noqa: BLE001, PERF203
                    # An AntaTest instance is potentially user-defined code.
                    # We need to catch everything and exit gracefully with an error message.
                    message = "\n".join(
                        [
                            f"There is an error when creating test {test_def.test.__module__}.{test_def.test.__name__}.",
                            f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                        ],
                    )
                    anta_log_exception(exc, message, logger)
        return coros

    def _log_run_information(self, ctx: AntaRunnerContext) -> None:
        """Log ANTA run information and potential resource limit warnings."""
        width = min(int(console.width) - 34, len("  Total potential connections: 100000000\n"))

        # Build device information
        device_lines = [
            "Devices:",
            f"  Total: {ctx.run_statistics.total_devices}",
        ]
        if ctx.run_statistics.filtered_by_tags_devices > 0:
            device_lines.append(f"  Excluded by tags: {ctx.run_statistics.filtered_by_tags_devices}")
        if ctx.run_statistics.connection_failed_devices > 0:
            device_lines.append(f"  Failed to connect: {ctx.run_statistics.connection_failed_devices}")
        device_lines.append(f"  Selected: {ctx.run_statistics.established_devices}{' (dry-run mode)' if ctx.dry_run else ''}")

        # Build connection information
        potential_connections = ctx.selected_inventory.get_potential_connections()
        connections_line = "" if potential_connections is None else f"  Total potential connections: {potential_connections}\n"

        run_info = (
            f"{{' ANTA NRFU Run Information ':-^{width}}}\n"
            f"{chr(10).join(device_lines)}\n"
            f"Tests: {ctx.run_statistics.total_tests} total\n"
            f"Limits:\n"
            f"  Max concurrent tests: {self._settings.max_concurrency}\n"
            f"{connections_line}"
            f"  Max file descriptors: {self._settings.file_descriptor_limit}\n"
            f"{{'':-^{width}}}"
        )
        logger.info(run_info)

        # Log warnings for potential resource limits
        if ctx.run_statistics.total_tests > self._settings.max_concurrency:
            logger.warning(
                "Tests count (%s) exceeds concurrent limit (%s). Tests will be throttled. Please consult the ANTA FAQ.",
                ctx.run_statistics.total_tests,
                self._settings.max_concurrency,
            )
        if potential_connections is not None and potential_connections > self._settings.file_descriptor_limit:
            logger.warning(
                "Potential connections (%s) exceeds file descriptor limit (%s). Connection errors may occur. Please consult the ANTA FAQ.",
                potential_connections,
                self._settings.file_descriptor_limit,
            )

    def _log_cache_statistics(self, ctx: AntaRunnerContext) -> None:
        """Log cache statistics for each device in the inventory."""
        for device in ctx.selected_inventory.devices:
            if device.cache_statistics is not None:
                msg = (
                    f"Cache statistics for '{device.name}': "
                    f"{device.cache_statistics['cache_hits']} hits / {device.cache_statistics['total_commands_sent']} "
                    f"command(s) ({device.cache_statistics['cache_hit_ratio']})"
                )
                logger.info(msg)
            else:
                logger.info("Caching is not enabled on %s", device.name)
