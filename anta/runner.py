# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner function."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from anta import GITHUB_SUGGESTION
from anta.cli.console import console
from anta.logger import anta_log_exception
from anta.models import AntaTest
from anta.settings import get_file_descriptor_limit, get_max_concurrency
from anta.tools import Catchtime, cprofile

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Coroutine

    from anta.catalog import AntaCatalog, AntaTestDefinition
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InventoryStats:
    """Statistics about inventory filtering."""

    total: int = 0
    filtered_by_tags: int = 0
    connection_failed: int = 0
    established: int = 0


@dataclass
class RunnerContext:
    """Context for ANTA runner execution."""

    # Parameters from main
    manager: ResultManager
    inventory: AntaInventory
    catalog: AntaCatalog
    devices: set[str] | None
    tests: set[str] | None
    tags: set[str] | None
    established_only: bool
    dry_run: bool

    # These attributes are set during preparation phase
    selected_inventory: AntaInventory | None = None
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] | None = None
    inventory_stats: InventoryStats | None = None
    total_tests: int = 0
    potential_connections: float | None = None

    # Resource limits
    max_concurrency: int = field(default_factory=get_max_concurrency)
    file_descriptor_limit: int = field(default_factory=get_file_descriptor_limit)


def _log_run_information(ctx: RunnerContext) -> None:
    """Log ANTA run information and potential resource limit warnings.

    Parameters
    ----------
    ctx
        RunnerContext object that includes the ANTA run parameters and context.
    """
    if ctx.inventory_stats is None:
        msg = "The inventory stats are not set in the ANTA run context. Make sure to run ANTA from the main function."
        raise RuntimeError(msg)

    width = min(int(console.width) - 34, len("  Total potential connections: Unlimited\n"))

    # Build device information
    device_lines = [
        "Devices:",
        f"  Total: {ctx.inventory_stats.total}",
    ]
    if ctx.inventory_stats.filtered_by_tags > 0:
        device_lines.append(f"  Excluded by tags: {ctx.inventory_stats.filtered_by_tags}")
    if ctx.inventory_stats.connection_failed > 0:
        device_lines.append(f"  Failed to connect: {ctx.inventory_stats.connection_failed}")
    device_lines.append(f"  Selected: {ctx.inventory_stats.established}{' (dry-run mode)' if ctx.dry_run else ''}")

    # Build connection information
    connections_line = (
        ""
        if ctx.potential_connections is None
        else f"  Total potential connections: {'Unlimited' if ctx.potential_connections == float('inf') else ctx.potential_connections}\n"
    )

    run_info = (
        f"{' ANTA NRFU Run Information ':-^{width}}\n"
        f"{chr(10).join(device_lines)}\n"
        f"Tests: {ctx.total_tests} total\n"
        f"Limits:\n"
        f"  Max concurrent tests: {ctx.max_concurrency}\n"
        f"{connections_line}"
        f"  Max file descriptors: {ctx.file_descriptor_limit}\n"
        f"{'':-^{width}}"
    )
    logger.info(run_info)

    # Log warnings for potential resource limits
    if ctx.total_tests > ctx.max_concurrency:
        logger.warning(
            "Tests count (%s) exceeds concurrent limit (%s). Tests will be throttled. See Scaling ANTA documentation.", ctx.total_tests, ctx.max_concurrency
        )
    if ctx.potential_connections == float("inf"):
        logger.warning(
            "Running with unlimited connections. Connection errors may occur due to file descriptor limit (%s). See Scaling ANTA documentation.",
            ctx.file_descriptor_limit,
        )
    elif ctx.potential_connections is not None and ctx.potential_connections > ctx.file_descriptor_limit:
        logger.warning(
            "Potential connections (%s) exceeds file descriptor limit (%s). Connection errors may occur. See Scaling ANTA documentation.",
            ctx.potential_connections,
            ctx.file_descriptor_limit,
        )


def _log_cache_statistics(ctx: RunnerContext) -> None:
    """Log cache statistics for each device in the inventory.

    Parameters
    ----------
    ctx
        RunnerContext object that includes the ANTA run parameters and context.
    """
    if ctx.selected_inventory is None:
        msg = "The selected inventory is not set in the ANTA run context. Make sure to run ANTA from the main function."
        raise RuntimeError(msg)

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


async def _run(tests_generator: AsyncGenerator[Coroutine[Any, Any, TestResult], None], limit: int) -> AsyncGenerator[TestResult, None]:
    """Run tests with a concurrency limit.

    This function takes an asynchronous generator of test coroutines and runs them
    with a limit on the number of concurrent tests. It yields test results as each
    test completes.

    Inspired by: https://death.andgravity.com/limit-concurrency

    Parameters
    ----------
    tests_generator
        An asynchronous generator that yields test coroutines.
    limit
        The maximum number of concurrent tests to run.

    Yields
    ------
        The result of each completed test.
    """
    if limit <= 0:
        msg = "Concurrency limit must be greater than 0."
        raise RuntimeError(msg)

    # NOTE: The `aiter` built-in function is not available in Python 3.9
    tests = tests_generator.__aiter__()  # pylint: disable=unnecessary-dunder-call
    tests_ended = False
    tests_pending: set[Task[TestResult]] = set()

    while tests_pending or not tests_ended:
        # Add tests to the pending set until the limit is reached or no more tests are available
        while len(tests_pending) < limit and not tests_ended:
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

        if len(tests_pending) >= limit:
            logger.debug("Concurrency limit reached: %s tests running. Waiting for tests to complete.", limit)

        if not tests_pending:
            logger.debug("No pending tests and all tests have been processed. Exiting.")
            return

        # Wait for at least one of the pending tests to complete
        tests_done, tests_pending = await asyncio.wait(tests_pending, return_when=asyncio.FIRST_COMPLETED)
        logger.debug("Completed %s test(s). Pending count: %s", len(tests_done), len(tests_pending))

        # Yield results of completed tests
        while tests_done:
            yield await tests_done.pop()


async def _setup_inventory(ctx: RunnerContext) -> bool:
    """Set up the inventory for the ANTA run.

    Parameters
    ----------
    ctx
        RunnerContext object that includes the ANTA run parameters and context.

    Returns
    -------
    bool
        True if the inventory is set up successfully, False otherwise.
    """
    total_devices = len(ctx.inventory)

    # In dry-run mode, set the selected inventory to the full inventory
    if ctx.dry_run:
        ctx.selected_inventory = ctx.inventory
        ctx.inventory_stats = InventoryStats(total=total_devices)
        return True

    # If the inventory is empty, exit
    if total_devices == 0:
        logger.info("The inventory is empty, exiting")
        return False

    # Filter the inventory based on the CLI provided tags and devices if any
    filtered_inventory = ctx.inventory.get_inventory(tags=ctx.tags, devices=ctx.devices) if ctx.tags or ctx.devices else ctx.inventory
    filtered_by_tags = total_devices - len(filtered_inventory)

    # Connect to devices
    with Catchtime(logger=logger, message="Connecting to devices"):
        await filtered_inventory.connect_inventory()

    # Remove devices that are unreachable
    ctx.selected_inventory = filtered_inventory.get_inventory(established_only=ctx.established_only)
    connection_failed = len(filtered_inventory) - len(ctx.selected_inventory)

    # If there are no devices in the inventory after filtering, exit
    if not ctx.selected_inventory.devices:
        # Build message parts
        tag_msg = f"matching the tags {ctx.tags} " if ctx.tags else ""
        device_msg = f" Selected devices: {ctx.devices} " if ctx.devices is not None else ""
        logger.warning("No reachable device %swas found.%s", tag_msg, device_msg)
        return False

    ctx.inventory_stats = InventoryStats(
        total=total_devices, filtered_by_tags=filtered_by_tags, connection_failed=connection_failed, established=len(ctx.selected_inventory)
    )
    return True


def _setup_tests(ctx: RunnerContext) -> bool:
    """Set up tests for the ANTA run.

    Parameters
    ----------
    ctx
        RunnerContext object that includes the ANTA run parameters and context.

    Returns
    -------
    bool
        True if tests are set up successfully, False otherwise.
    """
    if not ctx.selected_inventory:
        msg = "The inventory is not set in the ANTA run context. Make sure to run ANTA from the main function."
        raise RuntimeError(msg)

    # Build indexes for the catalog. If `tests` is set, filter the indexes based on these tests
    ctx.catalog.build_indexes(filtered_tests=ctx.tests)

    # Using a set to avoid inserting duplicate tests
    device_to_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = defaultdict(set)
    total_tests = 0
    total_connections = 0
    unlimited_connections = False
    all_have_connections = True

    # Create the device to tests mapping from the tags and calculate connection stats
    for device in ctx.selected_inventory.devices:
        if ctx.tags:
            # If there are CLI tags, execute tests with matching tags for this device
            if not (matching_tags := ctx.tags.intersection(device.tags)):
                # The device does not have any selected tag, skipping
                continue
            device_to_tests[device].update(ctx.catalog.get_tests_by_tags(matching_tags))
        else:
            # If there is no CLI tags, execute all tests that do not have any tags
            device_to_tests[device].update(ctx.catalog.tag_to_tests[None])

            # Then add the tests with matching tags from device tags
            device_to_tests[device].update(ctx.catalog.get_tests_by_tags(device.tags))

        total_tests += len(device_to_tests[device])

        # Check device connections
        if not hasattr(device, "max_connections"):
            all_have_connections = False
        elif device.max_connections is None:
            unlimited_connections = True
        else:
            total_connections += device.max_connections

    if total_tests == 0:
        tag_msg = f" matching the tags {ctx.tags} " if ctx.tags else " "
        logger.warning(
            "There are no tests%sto run in the current test catalog and device inventory, please verify your inputs.",
            tag_msg,
        )
        return False

    ctx.selected_tests = device_to_tests
    ctx.total_tests = total_tests
    ctx.potential_connections = None if not all_have_connections else float("inf") if unlimited_connections else total_connections
    return True


async def _generate_test_coroutines(ctx: RunnerContext) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
    """Generate test coroutines from selected tests for the ANTA run.

    It creates an async generator of coroutines which are created by the `test` method of the AntaTest instances.
    Each coroutine is a test to run.

    Parameters
    ----------
    ctx
        RunnerContext object that includes the ANTA run parameters and context.

    Yields
    ------
        The coroutine (test) to run.
    """
    if ctx.selected_tests is None:
        msg = "The selected tests are not set in the ANTA run context. Make sure to run ANTA from the main function."
        raise RuntimeError(msg)

    for device, test_definitions in ctx.selected_tests.items():
        for test in test_definitions:
            try:
                test_instance = test.test(device=device, inputs=test.inputs)
                if ctx.dry_run:
                    ctx.manager.add(test_instance.result)
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


@cprofile()
async def main(
    manager: ResultManager,
    inventory: AntaInventory,
    catalog: AntaCatalog,
    devices: set[str] | None = None,
    tests: set[str] | None = None,
    tags: set[str] | None = None,
    *,
    established_only: bool = True,
    dry_run: bool = False,
) -> None:
    """Run ANTA.

    Use this as an entrypoint to the test framework in your script.
    ResultManager object gets updated with the test results.

    Parameters
    ----------
    manager
        ResultManager object to populate with the test results.
    inventory
        AntaInventory object that includes the device(s).
    catalog
        AntaCatalog object that includes the list of tests.
    devices
        Devices on which to run tests. None means all devices. These may come from the `--device / -d` CLI option in NRFU.
    tests
        Tests to run against devices. None means all tests. These may come from the `--test / -t` CLI option in NRFU.
    tags
        Tags to filter devices from the inventory. These may come from the `--tags` CLI option in NRFU.
    established_only
        Include only established device(s).
    dry_run
        Build the list of coroutine to run and stop before test execution.
    """
    # Initialize the ANTA run context
    ctx = RunnerContext(
        manager=manager,
        inventory=inventory,
        catalog=catalog,
        devices=devices,
        tests=tests,
        tags=tags,
        established_only=established_only,
        dry_run=dry_run,
    )

    if not ctx.catalog.tests:
        logger.info("The list of tests is empty, exiting")
        return

    with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
        # Setup inventory
        if not await _setup_inventory(ctx):
            return

        # Prepare tests
        with Catchtime(logger=logger, message="Preparing Tests"):
            if not _setup_tests(ctx):
                return

        # Generate test coroutines
        generator = _generate_test_coroutines(ctx)
        _log_run_information(ctx)

    if ctx.dry_run:
        logger.info("Dry-run mode, exiting before running the tests.")
        async for test in generator:
            test.close()
        return

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=ctx.total_tests)

    with Catchtime(logger=logger, message="Running Tests"):
        async for result in _run(generator, limit=ctx.max_concurrency):
            ctx.manager.add(result)

    _log_cache_statistics(ctx)
