# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner function."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, Any
from warnings import warn

from anta import GITHUB_SUGGESTION
from anta.cli.console import console
from anta.logger import anta_log_exception, exc_to_str
from anta.models import AntaTest
from anta.settings import get_httpx_limits, get_max_concurrency
from anta.tools import Catchtime, cprofile

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Coroutine, Iterator

    from anta.catalog import AntaCatalog, AntaTestDefinition
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)

if os.name == "posix":
    import resource

    DEFAULT_NOFILE = 16384
    """Default number of open file descriptors for the ANTA process."""

    def adjust_rlimit_nofile() -> tuple[int, int]:
        """Adjust the maximum number of open file descriptors for the ANTA process.

        The limit is set to the lower of the current hard limit and the value of the ANTA_NOFILE environment variable.

        If the `ANTA_NOFILE` environment variable is not set or is invalid, `DEFAULT_NOFILE` is used.

        Returns
        -------
        tuple[int, int]
            The new soft and hard limits for open file descriptors.
        """
        try:
            nofile = int(os.environ.get("ANTA_NOFILE", DEFAULT_NOFILE))
        except ValueError as exception:
            logger.warning("The ANTA_NOFILE environment variable value is invalid: %s\nDefault to %s.", exc_to_str(exception), DEFAULT_NOFILE)
            nofile = DEFAULT_NOFILE

        limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        logger.debug("Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])
        nofile = min(limits[1], nofile)
        logger.debug("Setting soft limit for open file descriptors for the current ANTA process to %s", nofile)
        resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, limits[1]))
        return resource.getrlimit(resource.RLIMIT_NOFILE)


def log_run_information(
    device_count: tuple[int, int],
    test_count: int,
    max_concurrency: int,
    max_connections: int | None,
    file_descriptor_limit: int,
) -> None:
    """Log ANTA run information and potential resource limit warnings.

    Parameters
    ----------
    device_count
        Total number of devices in inventory and number of established devices.
    test_count
        Total number of tests to run.
    max_concurrency
        Maximum number of concurrent tests.
    max_connections
        Maximum connections per device. None means unlimited.
    file_descriptor_limit
        System file descriptor limit.
    """
    # TODO: 34 is a magic numbers from RichHandler formatting catering for date, level and path
    width = min(int(console.width) - 34, len("Devices: 000 total, 000 established\n"))

    devices_total, devices_established = device_count

    run_info = (
        f"{' ANTA NRFU Run Information ':-^{width}}\n"
        f"Devices: {devices_total} total, {devices_established} established\n"
        f"Tests: {test_count} total\n"
        f"Limits:\n"
        f"  Max concurrent tests: {max_concurrency}\n"
        f"  Max connections per device: {'Unlimited' if max_connections is None else max_connections}\n"
        f"  Max file descriptors: {file_descriptor_limit}\n"
        f"{'':-^{width}}"
    )

    logger.info(run_info)

    # Log warnings for potential resource limits
    if test_count > max_concurrency:
        logger.warning("Tests count (%s) exceeds concurrent limit (%s). Tests will be throttled. See Scaling ANTA documentation.", test_count, max_concurrency)

    if max_connections is None:
        logger.warning(
            "Running with unlimited HTTP connections. Connection errors may occur due to file descriptor limit (%s). See Scaling ANTA documentation.",
            file_descriptor_limit,
        )
    elif devices_established * max_connections > file_descriptor_limit:
        logger.warning(
            "Potential connections (%s) exceeds file descriptor limit (%s). Connection errors may occur. See Scaling ANTA documentation.",
            devices_established * max_connections,
            file_descriptor_limit,
        )


def log_cache_statistics(devices: list[AntaDevice]) -> None:
    """Log cache statistics for each device in the inventory.

    Parameters
    ----------
    devices
        List of devices in the inventory.
    """
    for device in devices:
        if device.cache_statistics is not None:
            msg = (
                f"Cache statistics for '{device.name}': "
                f"{device.cache_statistics['cache_hits']} hits / {device.cache_statistics['total_commands_sent']} "
                f"command(s) ({device.cache_statistics['cache_hit_ratio']})"
            )
            logger.info(msg)
        else:
            logger.info("Caching is not enabled on %s", device.name)


async def run(tests_generator: AsyncGenerator[Coroutine[Any, Any, TestResult], None], limit: int) -> AsyncGenerator[TestResult, None]:
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
    aws = tests_generator.__aiter__()  # pylint: disable=unnecessary-dunder-call
    aws_ended = False
    pending: set[Task[TestResult]] = set()

    while pending or not aws_ended:
        # Add tests to the pending set until the limit is reached or no more tests are available
        while len(pending) < limit and not aws_ended:
            try:
                # NOTE: The `anext` built-in function is not available in Python 3.9
                aw = await aws.__anext__()  # pylint: disable=unnecessary-dunder-call
            except StopAsyncIteration:  # noqa: PERF203
                aws_ended = True
                logger.debug("All tests have been added to the pending set.")
            else:
                # Ensure the coroutine is scheduled to run and add it to the pending set
                pending.add(asyncio.create_task(aw))
                logger.debug("Added a test to the pending set: %s", aw)

        if len(pending) >= limit:
            logger.debug("Concurrency limit reached: %s tests running. Waiting for tests to complete.", limit)

        if not pending:
            logger.debug("No pending tests and all tests have been processed. Exiting.")
            return

        # Wait for at least one of the pending tests to complete
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        logger.debug("Completed %s test(s). Pending count: %s", len(done), len(pending))

        # Yield results of completed tests
        while done:
            yield await done.pop()


async def setup_inventory(inventory: AntaInventory, tags: set[str] | None, devices: set[str] | None, *, established_only: bool) -> AntaInventory | None:
    """Set up the inventory for the ANTA run.

    Parameters
    ----------
    inventory
        AntaInventory object that includes the device(s).
    tags
        Tags to filter devices from the inventory.
    devices
        Devices on which to run tests. None means all devices.
    established_only
        If True use return only devices where a connection is established.

    Returns
    -------
    AntaInventory | None
        The filtered inventory or None if there are no devices to run tests on.
    """
    if len(inventory) == 0:
        logger.info("The inventory is empty, exiting")
        return None

    # Filter the inventory based on the CLI provided tags and devices if any
    selected_inventory = inventory.get_inventory(tags=tags, devices=devices) if tags or devices else inventory

    with Catchtime(logger=logger, message="Connecting to devices"):
        # Connect to the devices
        await selected_inventory.connect_inventory()

    # Remove devices that are unreachable
    selected_inventory = selected_inventory.get_inventory(established_only=established_only)

    # If there are no devices in the inventory after filtering, exit
    if not selected_inventory.devices:
        msg = f'No reachable device {f"matching the tags {tags} " if tags else ""}was found.{f" Selected devices: {devices} " if devices is not None else ""}'
        logger.warning(msg)
        return None

    return selected_inventory


def prepare_tests(
    inventory: AntaInventory, catalog: AntaCatalog, tests: set[str] | None, tags: set[str] | None
) -> defaultdict[AntaDevice, set[AntaTestDefinition]] | None:
    """Prepare the tests to run.

    Parameters
    ----------
    inventory
        AntaInventory object that includes the device(s).
    catalog
        AntaCatalog object that includes the list of tests.
    tests
        Tests to run against devices. None means all tests.
    tags
        Tags to filter devices from the inventory.

    Returns
    -------
    defaultdict[AntaDevice, set[AntaTestDefinition]] | None
        A mapping of devices to the tests to run or None if there are no tests to run.
    """
    # Build indexes for the catalog. If `tests` is set, filter the indexes based on these tests
    catalog.build_indexes(filtered_tests=tests)

    # Using a set to avoid inserting duplicate tests
    device_to_tests: defaultdict[AntaDevice, set[AntaTestDefinition]] = defaultdict(set)

    total_test_count = 0

    # Create the device to tests mapping from the tags
    for device in inventory.devices:
        if tags:
            # If there are CLI tags, execute tests with matching tags for this device
            if not (matching_tags := tags.intersection(device.tags)):
                # The device does not have any selected tag, skipping
                continue
            device_to_tests[device].update(catalog.get_tests_by_tags(matching_tags))
        else:
            # If there is no CLI tags, execute all tests that do not have any tags
            device_to_tests[device].update(catalog.tag_to_tests[None])

            # Then add the tests with matching tags from device tags
            device_to_tests[device].update(catalog.get_tests_by_tags(device.tags))

        total_test_count += len(device_to_tests[device])

    if total_test_count == 0:
        msg = (
            f"There are no tests{f' matching the tags {tags} ' if tags else ' '}to run in the current "
            "test catalog and device inventory, please verify your inputs."
        )
        logger.warning(msg)
        return None

    return device_to_tests


def _generate_test_coroutines(
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]], manager: ResultManager | None = None
) -> Iterator[Coroutine[Any, Any, TestResult]]:
    """Generate test coroutines from selected tests for the ANTA run.

    Internal function that creates the test coroutines. Used by both
    `generate_test_coroutines` and `get_coroutines` functions.

    Parameters
    ----------
    selected_tests
        A mapping of devices to the tests to run. The selected tests are generated by the `prepare_tests` function.
    manager
        An optional ResultManager object to pre-populate with the test results. Used in dry-run mode.

    Yields
    ------
        The coroutine (test) to run.
    """
    for device, test_definitions in selected_tests.items():
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


async def generate_test_coroutines(
    selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]], manager: ResultManager | None = None
) -> AsyncGenerator[Coroutine[Any, Any, TestResult], None]:
    """Generate test coroutines from selected tests for the ANTA run.

    It creates an async generator of coroutines which are created by the `test` method of the AntaTest instances. Each coroutine is a test to run.

    Parameters
    ----------
    selected_tests
        A mapping of devices to the tests to run. The selected tests are generated by the `prepare_tests` function.
    manager
        An optional ResultManager object to pre-populate with the test results. Used in dry-run mode.

    Yields
    ------
        The coroutine (test) to run.
    """
    for coroutine in _generate_test_coroutines(selected_tests, manager):
        yield coroutine


def get_coroutines(selected_tests: defaultdict[AntaDevice, set[AntaTestDefinition]], manager: ResultManager | None = None) -> list[Coroutine[Any, Any, TestResult]]:
    """Get the coroutines for the ANTA run.

    Warning
    -------
        This function is deprecated and no longer used by the runner as it now uses a generator created by the `generate_test_coroutines` function of this module.
        Will be removed in ANTA v2.0

    Parameters
    ----------
    selected_tests
        A mapping of devices to the tests to run. The selected tests are generated by the `prepare_tests` function.
    manager
        An optional ResultManager object to pre-populate with the test results. Used in dry-run mode.

    Returns
    -------
    list[Coroutine[Any, Any, TestResult]]
        The list of coroutines to run.
    """
    # TODO: Remove this function in ANTA v2.0
    warn(
        message="`get_coroutines` is deprecated and no longer used by the runner. Use `generate_test_coroutines` instead. Will be removed in ANTA v2.0.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return list(_generate_test_coroutines(selected_tests, manager))


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
    # Get the maximum number of tests to run concurrently
    max_concurrency = get_max_concurrency()

    # Get the maximum number of connections per device
    max_connections = get_httpx_limits().max_connections

    # Adjust the file descriptor limit
    if os.name == "posix":
        logger.debug("Adjusting the file descriptor limit for the ANTA process.")
        limits = adjust_rlimit_nofile()
    else:
        logger.info("Running on a non-POSIX system, cannot adjust the maximum number of file descriptors.")
        limits = (sys.maxsize, sys.maxsize)

    if not catalog.tests:
        logger.info("The list of tests is empty, exiting")
        return

    with Catchtime(logger=logger, message="Preparing ANTA NRFU Run"):
        # Setup the inventory
        selected_inventory = inventory if dry_run else await setup_inventory(inventory, tags, devices, established_only=established_only)
        if selected_inventory is None:
            return

        with Catchtime(logger=logger, message="Preparing Tests"):
            selected_tests = prepare_tests(selected_inventory, catalog, tests, tags)
            if selected_tests is None:
                return
            final_tests_count = sum(len(tests) for tests in selected_tests.values())
            del catalog  # No longer needed

        generator = generate_test_coroutines(selected_tests, manager if dry_run else None)

        log_run_information(
            device_count=(len(inventory), len(selected_inventory)),
            test_count=final_tests_count,
            max_concurrency=max_concurrency,
            max_connections=max_connections,
            file_descriptor_limit=limits[0],
        )

    if dry_run:
        logger.info("Dry-run mode, exiting before running the tests.")
        async for test in generator:
            test.close()
        return

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=final_tests_count)

    with Catchtime(logger=logger, message="Running Tests"):
        async for result in run(generator, limit=max_concurrency):
            manager.add(result)

    log_cache_statistics(selected_inventory.devices)
