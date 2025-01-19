# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner classes."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from anta import GITHUB_SUGGESTION
from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.cli.console import console
from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.logger import anta_log_exception
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.settings import get_file_descriptor_limit, get_max_concurrency
from anta.tools import Catchtime

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Coroutine

    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AntaRunnerInventoryStats:
    """Track inventory filtering statistics during an ANTA run.

    This class maintains counters for tracking how the device inventory is filtered
    during test setup and.

    When initialized, the counters are set to zero.

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

    total: int = 0
    filtered_by_tags: int = 0
    connection_failed: int = 0
    established: int = 0


class AntaRunnerScope(BaseModel):
    """Define the scope of an ANTA test run.

    The scope determines which devices and tests to include in a run, and how to
    filter them. This class is used with the AntaRunner.run() method.

    Attributes
    ----------
    devices : set[str] | None, optional
        Set of device names to run tests on. If None, includes all devices in
        the inventory. Commonly set via the NRFU CLI `--device/-d` option.
    tests : set[str] | None, optional
        Set of test names to run. If None, runs all available tests in the
        catalog. Commonly set via the NRFU CLI `--test/-t` option.
    tags : set[str] | None, optional
        Set of tags used to filter both devices and tests. A device or test
        must match any of the provided tags to be included. Commonly set via
        the NRFU CLI `--tags` option.
    established_only : bool, default=True
        When True, only includes devices with established connections in the
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
        Manager for collecting and storing test results. If None, a new manager
        is returned for each run, otherwise the provided manager is used
        and results from subsequent runs are appended to it.
    max_concurrency : int
        Maximum number of tests that can run concurrently. Defaults from `get_max_concurrency()`.
        See the `anta.settings` module for details on how this value is determined from
        environment variables and system defaults.
    file_descriptor_limit : int
        System file descriptor limit for connections. Defaults from `get_file_descriptor_limit()`.
        See the `anta.settings` module for details on how this value is determined from
        environment variables and system defaults.
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
        None if unknown, float('inf') if unlimited.

    Notes
    -----
    After initializing an `AntaRunner` instance, tests should only be executed through
    the `run()` method. This method manages the complete test lifecycle including setup,
    execution, and cleanup.

    All internal methods and state (prefixed with _) are managed by the `run()` method
    and should not be called directly. The internal state is reset between runs to
    ensure clean execution.


    Examples
    --------
    ```python
    import asyncio

    from anta._runner import AntaRunner, AntaRunnerScope
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
    second_run_results = asyncio.run(runner.run(scope=AntaRunnerScope(tags={"leaf"})))
    ```
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    inventory: AntaInventory
    catalog: AntaCatalog
    manager: ResultManager | None = None
    max_concurrency: int = Field(default_factory=get_max_concurrency)
    file_descriptor_limit: int = Field(default_factory=get_file_descriptor_limit)

    # Internal attributes set during setup phases before each run
    _selected_inventory: AntaInventory | None = None
    _selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] | None = None
    _inventory_stats: AntaRunnerInventoryStats | None = None
    _total_tests: int = 0
    _potential_connections: float | None = None

    def reset(self) -> None:
        """Reset the internal attributes of the ANTA runner."""
        self._selected_inventory: AntaInventory | None = None
        self._selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] | None = None
        self._inventory_stats: AntaRunnerInventoryStats | None = None
        self._total_tests: int = 0
        self._potential_connections: float | None = None

    async def run(self, scope: AntaRunnerScope | None = None, *, dry_run: bool = False) -> ResultManager:
        """Run ANTA.

        Parameters
        ----------
        scope
            Scope of the ANTA run. If None, runs all tests on all devices.
        dry_run
            Dry-run mode flag. If True, runs all setup steps but does not execute tests.
        """
        scope = scope or AntaRunnerScope()

        # Cleanup the instance before each run
        self.reset()
        self.catalog.clear_indexes()
        manager = ResultManager() if self.manager is None else self.manager

        if not self.catalog.tests:
            logger.info("The list of tests is empty, exiting")
            return manager

        with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
            # Set up inventory
            if not await self._setup_inventory(scope, dry_run=dry_run):
                return manager

            # Set up tests
            with Catchtime(logger=logger, message="Preparing Tests"):
                if not self._setup_tests(scope):
                    return manager

            # Set up test coroutines
            generator = self._setup_coroutines(manager=manager if dry_run else None)

            # Log run information
            self._log_run_information(dry_run=dry_run)

        if dry_run:
            logger.info("Dry-run mode, exiting before running the tests.")
            async for test in generator:
                test.close()
            return manager

        if AntaTest.progress is not None:
            AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=self._total_tests)

        with Catchtime(logger=logger, message="Running Tests"):
            async for result in self._run(generator):
                manager.add(result)

        self._log_cache_statistics()
        return manager

    async def _setup_inventory(self, scope: AntaRunnerScope, *, dry_run: bool = False) -> bool:
        """Set up the inventory for the ANTA run."""
        total_devices = len(self.inventory)

        # In dry-run mode, set the selected inventory to the full inventory
        if dry_run:
            self._selected_inventory = self.inventory
            self._inventory_stats = AntaRunnerInventoryStats(total=total_devices)
            return True

        # If the inventory is empty, exit
        if total_devices == 0:
            logger.info("The inventory is empty, exiting")
            return False

        # Filter the inventory based on the CLI provided tags and devices if any
        filtered_inventory = self.inventory.get_inventory(tags=scope.tags, devices=scope.devices) if scope.tags or scope.devices else self.inventory
        filtered_by_tags = total_devices - len(filtered_inventory)

        # Connect to devices
        with Catchtime(logger=logger, message="Connecting to devices"):
            await filtered_inventory.connect_inventory()

        # Remove devices that are unreachable
        self._selected_inventory = filtered_inventory.get_inventory(established_only=scope.established_only)
        connection_failed = len(filtered_inventory) - len(self._selected_inventory)

        # If there are no devices in the inventory after filtering, exit
        if not self._selected_inventory.devices:
            # Build message parts
            tag_msg = f"matching the tags {scope.tags} " if scope.tags else ""
            device_msg = f" Selected devices: {scope.devices} " if scope.devices is not None else ""
            logger.warning("No reachable device %swas found.%s", tag_msg, device_msg)
            return False

        self._inventory_stats = AntaRunnerInventoryStats(
            total=total_devices, filtered_by_tags=filtered_by_tags, connection_failed=connection_failed, established=len(self._selected_inventory)
        )
        return True

    def _setup_tests(self, scope: AntaRunnerScope) -> bool:
        """Set up tests for the ANTA run."""
        if self._selected_inventory is None:
            msg = "The selected inventory is not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        # Build indexes for the catalog. If `tests` is set, filter the indexes based on these tests
        self.catalog.build_indexes(filtered_tests=scope.tests)

        # Using a set to avoid inserting duplicate tests
        device_to_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = defaultdict(set)
        total_tests = 0
        total_connections = 0
        unlimited_connections = False
        all_have_connections = True

        # Create the device to tests mapping from the tags and calculate connection stats
        for device in self._selected_inventory.devices:
            if scope.tags:
                # If there are CLI tags, execute tests with matching tags for this device
                if not (matching_tags := scope.tags.intersection(device.tags)):
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
            if not hasattr(device, "max_connections"):
                all_have_connections = False
            elif device.max_connections is None:
                unlimited_connections = True
            else:
                total_connections += device.max_connections

        if total_tests == 0:
            tag_msg = f" matching the tags {scope.tags} " if scope.tags else " "
            logger.warning(
                "There are no tests%sto run in the current test catalog and device inventory, please verify your inputs.",
                tag_msg,
            )
            return False

        self._selected_tests = device_to_tests
        self._total_tests = total_tests
        self._potential_connections = None if not all_have_connections else float("inf") if unlimited_connections else total_connections
        return True

    async def _setup_coroutines(self, *, manager: ResultManager | None = None) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
        """Set up test coroutines from selected tests for the ANTA run.

        It creates an async generator of coroutines which are created by the `test` method of the AntaTest instances.
        Each coroutine is a test to run.

        Parameters
        ----------
        manager
            An optional ResultManager instance to pre-populate with the test results. Used in `dry_run` mode.

        Yields
        ------
            The coroutine (test) to run.
        """
        if self._selected_tests is None:
            msg = "The selected tests are not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        for device, test_definitions in self._selected_tests.items():
            for test in test_definitions:
                try:
                    test_instance = test.test(device=device, inputs=test.inputs)
                    if manager is not None:
                        manager.add(test_instance.result)
                    coroutine = test_instance.test()
                except Exception as e:  # noqa: PERF203, BLE001
                    # An AntaTest instance is potentially user-defined code.
                    # We need to catch everything and exit gracefully with an error message.
                    message = "\n".join(
                        [
                            f"There is an error when creating test {test.test.__module__}.{test.test.__name__}.",
                            f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                        ],
                    )
                    anta_log_exception(e, message, logger)
                else:
                    yield coroutine

    def _log_run_information(self, *, dry_run: bool = False) -> None:
        """Log ANTA run information and potential resource limit warnings.

        Parameters
        ----------
        dry_run
            Dry-run mode flag.
        """
        if self._inventory_stats is None:
            msg = "The inventory stats are not available. ANTA must be executed through AntaRunner.run()"
            raise RuntimeError(msg)

        width = min(int(console.width) - 34, len("  Total potential connections: Unlimited\n"))

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
        connections_line = (
            ""
            if self._potential_connections is None
            else f"  Total potential connections: {'Unlimited' if self._potential_connections == float('inf') else self._potential_connections}\n"
        )

        run_info = (
            f"{' ANTA NRFU Run Information ':-^{width}}\n"
            f"{chr(10).join(device_lines)}\n"
            f"Tests: {self._total_tests} total\n"
            f"Limits:\n"
            f"  Max concurrent tests: {self.max_concurrency}\n"
            f"{connections_line}"
            f"  Max file descriptors: {self.file_descriptor_limit}\n"
            f"{'':-^{width}}"
        )
        logger.info(run_info)

        # Log warnings for potential resource limits
        if self._total_tests > self.max_concurrency:
            logger.warning(
                "Tests count (%s) exceeds concurrent limit (%s). Tests will be throttled. See Scaling ANTA documentation.", self._total_tests, self.max_concurrency
            )
        if self._potential_connections == float("inf"):
            logger.warning(
                "Running with unlimited connections. Connection errors may occur due to file descriptor limit (%s). See Scaling ANTA documentation.",
                self.file_descriptor_limit,
            )
        elif self._potential_connections is not None and self._potential_connections > self.file_descriptor_limit:
            logger.warning(
                "Potential connections (%s) exceeds file descriptor limit (%s). Connection errors may occur. See Scaling ANTA documentation.",
                self._potential_connections,
                self.file_descriptor_limit,
            )

    async def _run(self, generator: AsyncGenerator[Coroutine[Any, Any, TestResult], None]) -> AsyncGenerator[TestResult, None]:
        """Run tests with a concurrency limit.

        This function takes an asynchronous generator of test coroutines and runs them
        with a limit on the number of concurrent tests. It yields test results as each
        test completes.

        Inspired by: https://death.andgravity.com/limit-concurrency

        Parameters
        ----------
        generator
            An asynchronous generator that yields test coroutines.

        Yields
        ------
            The result of each completed test.
        """
        if self.max_concurrency <= 0:
            msg = "Concurrency limit must be greater than 0."
            raise RuntimeError(msg)

        # NOTE: The `aiter` built-in function is not available in Python 3.9
        tests = generator.__aiter__()  # pylint: disable=unnecessary-dunder-call
        tests_ended = False
        tests_pending: set[Task[TestResult]] = set()

        while tests_pending or not tests_ended:
            # Add tests to the pending set until the limit is reached or no more tests are available
            while len(tests_pending) < self.max_concurrency and not tests_ended:
                try:
                    # NOTE: The `anext` built-in function is not available in Python 3.9
                    test = await tests.__anext__()  # pylint: disable=unnecessary-dunder-call
                except StopAsyncIteration:  # noqa: PERF203
                    tests_ended = True
                    logger.debug("All tests have been added to the pending set.")
                else:
                    # Ensure the coroutine is scheduled to run and add it to the pending set
                    tests_pending.add(asyncio.create_task(test))
                    logger.debug("Added a test to the pending set: %s", test)

            if len(tests_pending) >= self.max_concurrency:
                logger.debug("Concurrency limit reached: %s tests running. Waiting for tests to complete.", self.max_concurrency)

            if not tests_pending:
                logger.debug("No pending tests and all tests have been processed. Exiting.")
                return

            # Wait for at least one of the pending tests to complete
            tests_done, tests_pending = await asyncio.wait(tests_pending, return_when=asyncio.FIRST_COMPLETED)
            logger.debug("Completed %s test(s). Pending count: %s", len(tests_done), len(tests_pending))

            # Yield results of completed tests
            while tests_done:
                yield await tests_done.pop()

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
