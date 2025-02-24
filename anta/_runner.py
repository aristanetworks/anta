# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner classes."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

from anta import GITHUB_SUGGESTION
from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.cli.console import console
from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.logger import anta_log_exception
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.settings import AntaRunnerSettings
from anta.tools import Catchtime, limit_concurrency

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Coroutine

    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AntaRunnerInventoryStats:
    """Store inventory filtering statistics of an ANTA run.

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

    total: int
    filtered_by_tags: int
    connection_failed: int
    established: int


class AntaRunnerFilter(BaseModel):
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


class AntaRunner(BaseModel):
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
    _inventory_stats : AntaRunnerInventoryStats | None
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

    from anta._runner import AntaRunner, AntaRunnerFilter
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
    second_run_results = asyncio.run(runner.run(scope=AntaRunnerFilter(tags={"leaf"})))
    ```
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    inventory: AntaInventory
    catalog: AntaCatalog
    manager: ResultManager | None = None

    # Internal attributes set during setup phases before each run
    _selected_inventory: AntaInventory | None = PrivateAttr(default=None)
    _selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] | None = PrivateAttr(default=None)
    _inventory_stats: AntaRunnerInventoryStats | None = PrivateAttr(default=None)
    _total_tests: int = PrivateAttr(default=0)
    _potential_connections: float | None = PrivateAttr(default=None)

    # Internal settings loaded from environment variables
    _settings: AntaRunnerSettings = PrivateAttr(default_factory=AntaRunnerSettings)

    def reset(self) -> None:
        """Reset the internal attributes of the ANTA runner."""
        self._selected_inventory: AntaInventory | None = None
        self._selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] | None = None
        self._inventory_stats: AntaRunnerInventoryStats | None = None
        self._total_tests: int = 0
        self._potential_connections: float | None = None

    async def run(self, filters: AntaRunnerFilter | None = None, *, dry_run: bool = False) -> ResultManager:
        """Run ANTA.

        Parameters
        ----------
        filters
            Filters for the ANTA run. If None, runs all tests on all devices.
        dry_run
            Dry-run mode flag. If True, runs all setup steps but does not execute tests.
        """
        filters = filters or AntaRunnerFilter()

        # Cleanup the instance before each run
        self.reset()
        self.catalog.clear_indexes()
        manager = ResultManager() if self.manager is None else self.manager

        if not self.catalog.tests:
            logger.info("The list of tests is empty, exiting")
            return manager

        with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
            # Set up inventory
            if not await self._setup_inventory(filters, dry_run=dry_run):
                return manager

            # Set up tests
            with Catchtime(logger=logger, message="Preparing Tests"):
                if not self._setup_tests(filters):
                    return manager

            # Build the test generator
            test_generator = self._test_generator(manager if dry_run else None)

            # Log run information
            self._log_run_information(dry_run=dry_run)

        if dry_run:
            logger.info("Dry-run mode, exiting before running the tests.")
            async for test in test_generator:
                test.close()
            return manager

        if AntaTest.progress is not None:
            AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=self._total_tests)

        with Catchtime(logger=logger, message="Running Tests"):
            async for result in limit_concurrency(test_generator, limit=self._settings.max_concurrency):
                manager.add(await result)

        self._log_cache_statistics()
        return manager

    async def _setup_inventory(self, filters: AntaRunnerFilter, *, dry_run: bool = False) -> bool:
        """Set up the inventory for the ANTA run."""
        total_devices = len(self.inventory)

        # In dry-run mode, set the selected inventory to the full inventory
        if dry_run:
            self._selected_inventory = self.inventory
            self._inventory_stats = AntaRunnerInventoryStats(total=total_devices, filtered_by_tags=0, connection_failed=0, established=0)
            return True

        # If the inventory is empty, exit
        if total_devices == 0:
            logger.info("The inventory is empty, exiting")
            return False

        # Filter the inventory based on the provided filters any
        filtered_inventory = self.inventory.get_inventory(tags=filters.tags, devices=filters.devices) if filters.tags or filters.devices else self.inventory
        filtered_by_tags = total_devices - len(filtered_inventory)

        # Connect to devices
        with Catchtime(logger=logger, message="Connecting to devices"):
            await filtered_inventory.connect_inventory()

        # Remove devices that are unreachable
        self._selected_inventory = filtered_inventory.get_inventory(established_only=filters.established_only)
        connection_failed = len(filtered_inventory) - len(self._selected_inventory)

        # If there are no devices in the inventory after filtering, exit
        if not self._selected_inventory.devices:
            # Build message parts
            tag_msg = f"matching the tags {filters.tags} " if filters.tags else ""
            device_msg = f" Selected devices: {filters.devices} " if filters.devices is not None else ""
            logger.warning("No reachable device %swas found.%s", tag_msg, device_msg)
            return False

        self._inventory_stats = AntaRunnerInventoryStats(
            total=total_devices, filtered_by_tags=filtered_by_tags, connection_failed=connection_failed, established=len(self._selected_inventory)
        )
        return True

    def _setup_tests(self, filters: AntaRunnerFilter) -> bool:
        """Set up tests for the ANTA run."""
        if self._selected_inventory is None:
            msg = "The selected inventory is not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        # Build indexes for the catalog. If `filters.tests` is set, filter the indexes based on these tests
        self.catalog.build_indexes(filtered_tests=filters.tests)

        # Using a set to avoid inserting duplicate tests
        device_to_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = defaultdict(set)
        total_tests = 0
        total_connections = 0
        all_have_connections = True

        # Create the device to tests mapping from the tags and calculate connection stats
        for device in self._selected_inventory.devices:
            if filters.tags:
                # If there are CLI tags, execute tests with matching tags for this device
                if not (matching_tags := filters.tags.intersection(device.tags)):
                    # The device does not have any selected tag, skipping
                    continue
                device_to_tests[device].update(self.catalog.get_tests_by_tags(matching_tags))
            else:
                # If there is no CLI tags, execute all tests that do not have any tags
                device_to_tests[device].update(self.catalog.tag_to_tests[None])

                # Then add the tests with matching tags from device tags
                device_to_tests[device].update(self.catalog.get_tests_by_tags(device.tags))

            total_tests += len(device_to_tests[device])

            # Check device connections
            if not hasattr(device, "max_connections") or device.max_connections is None:
                all_have_connections = False
            else:
                total_connections += device.max_connections

        if total_tests == 0:
            tag_msg = f" matching the tags {filters.tags} " if filters.tags else " "
            logger.warning(
                "There are no tests%sto run in the current test catalog and device inventory, please verify your inputs.",
                tag_msg,
            )
            return False

        self._selected_tests = device_to_tests
        self._total_tests = total_tests
        self._potential_connections = None if not all_have_connections else total_connections
        return True

    async def _test_generator(self, manager: ResultManager | None = None) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
        """Generate test coroutines for the ANTA run."""
        if self._selected_tests is None:
            msg = "The selected tests are not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        logger.debug("ANTA run scheduling strategy: %s", self._settings.scheduling_strategy)

        device_to_tests: dict[AntaDevice, list[AntaTestDefinition]] = {
            device: sorted(tests, key=lambda td: td.test.__name__) for device, tests in self._selected_tests.items()
        }

        if self._settings.scheduling_strategy == "device-by-device":
            async for coro in self._generate_device_by_device(device_to_tests, manager):
                yield coro
        elif self._settings.scheduling_strategy == "device-by-count":
            async for coro in self._generate_device_by_count(device_to_tests, self._settings.scheduling_tests_per_device, manager):
                yield coro
        else:
            # Default to round-robin
            async for coro in self._generate_round_robin(device_to_tests, manager):
                yield coro

    async def _generate_round_robin(
        self, device_to_tests: dict[AntaDevice, list[AntaTestDefinition]], manager: ResultManager | None = None
    ) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
        """Yield one test per device in each round."""
        while any(device_to_tests.values()):
            for device, tests in device_to_tests.items():
                if tests:
                    test_def = tests.pop(0)
                    coro = self._create_test_coroutine(test_def, device, manager)
                    if coro is not None:
                        yield coro

    async def _generate_device_by_device(
        self, device_to_tests: dict[AntaDevice, list[AntaTestDefinition]], manager: ResultManager | None = None
    ) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
        """Yield all tests for one device before moving to the next."""
        for device, tests in device_to_tests.items():
            while tests:
                test_def = tests.pop(0)
                coro = self._create_test_coroutine(test_def, device, manager)
                if coro is not None:
                    yield coro

    async def _generate_device_by_count(
        self,
        device_to_tests: dict[AntaDevice, list[AntaTestDefinition]],
        tests_per_device: int,
        manager: ResultManager | None = None,
    ) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
        """In each round, yield up to `tests_per_device` tests for each device."""
        while any(device_to_tests.values()):
            for device, tests in device_to_tests.items():
                count = min(tests_per_device, len(tests))
                for _ in range(count):
                    test_def = tests.pop(0)
                    coro = self._create_test_coroutine(test_def, device, manager)
                    if coro is not None:
                        yield coro

    def _create_test_coroutine(
        self, test_def: AntaTestDefinition, device: AntaDevice, manager: ResultManager | None = None
    ) -> Coroutine[Any, Any, TestResult] | None:
        """Create a test coroutine from a test definition."""
        try:
            test_instance = test_def.test(device=device, inputs=test_def.inputs)
            if manager is not None:
                manager.add(test_instance.result)
            coroutine = test_instance.test()
        except Exception as e:  # noqa: BLE001
            # An AntaTest instance is potentially user-defined code.
            # We need to catch everything and exit gracefully with an error message.
            message = "\n".join(
                [
                    f"There is an error when creating test {test_def.test.__module__}.{test_def.test.__name__}.",
                    f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                ],
            )
            anta_log_exception(e, message, logger)
            return None
        return coroutine

    def _log_run_information(self, *, dry_run: bool = False) -> None:
        """Log ANTA run information and potential resource limit warnings."""
        if self._inventory_stats is None:
            msg = "The inventory stats are not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        width = min(int(console.width) - 34, len("  Total potential connections: 100000000\n"))

        # Build device information
        device_lines = [
            "Devices:",
            f"  Total: {self._inventory_stats.total}",
        ]
        if self._inventory_stats.filtered_by_tags > 0:
            device_lines.append(f"  Excluded by tags: {self._inventory_stats.filtered_by_tags}")
        if self._inventory_stats.connection_failed > 0:
            device_lines.append(f"  Failed to connect: {self._inventory_stats.connection_failed}")
        device_lines.append(f"  Selected: {self._inventory_stats.established}{' (dry-run mode)' if dry_run else ''}")

        # Build connection information
        connections_line = "" if self._potential_connections is None else f"  Total potential connections: {self._potential_connections}\n"

        run_info = (
            f"{' ANTA NRFU Run Information ':-^{width}}\n"
            f"{chr(10).join(device_lines)}\n"
            f"Tests: {self._total_tests} total\n"
            f"Limits:\n"
            f"  Max concurrent tests: {self._settings.max_concurrency}\n"
            f"{connections_line}"
            f"  Max file descriptors: {self._settings.file_descriptor_limit}\n"
            f"{'':-^{width}}"
        )
        logger.info(run_info)

        # Log warnings for potential resource limits
        if self._total_tests > self._settings.max_concurrency:
            logger.warning(
                "Tests count (%s) exceeds concurrent limit (%s). Tests will be throttled. Please consult the ANTA FAQ.",
                self._total_tests,
                self._settings.max_concurrency,
            )
        if self._potential_connections is not None and self._potential_connections > self._settings.file_descriptor_limit:
            logger.warning(
                "Potential connections (%s) exceeds file descriptor limit (%s). Connection errors may occur. Please consult the ANTA FAQ.",
                self._potential_connections,
                self._settings.file_descriptor_limit,
            )

    def _log_cache_statistics(self) -> None:
        """Log cache statistics for each device in the inventory."""
        if self._selected_inventory is None:
            msg = "The selected inventory is not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        for device in self._selected_inventory.devices:
            if device.cache_statistics is not None:
                msg = (
                    f"Cache statistics for '{device.name}': "
                    f"{device.cache_statistics['cache_hits']} hits / {device.cache_statistics['total_commands_sent']} "
                    f"command(s) ({device.cache_statistics['cache_hit_ratio']})"
                )
                logger.info(msg)
            else:
                logger.info("Caching is not enabled on %s", device.name)
