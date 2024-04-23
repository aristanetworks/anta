# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA runner function."""

from __future__ import annotations

import asyncio
import logging
import os
import resource
from typing import TYPE_CHECKING

from anta import GITHUB_SUGGESTION
from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.device import AntaDevice
from anta.logger import anta_log_exception, exc_to_str
from anta.models import AntaTest

if TYPE_CHECKING:
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)

AntaTestRunner = tuple[AntaTestDefinition, AntaDevice]

# Environment variable to set ANTA's maximum number of open file descriptors.
# Maximum number of file descriptor the ANTA process will be able to open.
# This limit is independent from the system's hard limit, the lower will be used.
DEFAULT_NOFILE = 16384
try:
    __NOFILE__ = int(os.environ.get("ANTA_NOFILE", DEFAULT_NOFILE))
except ValueError as exception:
    logger.warning("The ANTA_NOFILE environment variable value is invalid: %s\nDefault to %s.", exc_to_str(exception), DEFAULT_NOFILE)
    __NOFILE__ = DEFAULT_NOFILE


def adjust_rlimit_nofile() -> tuple[int, int]:
    """Adjust the maximum number of open file descriptors for the ANTA process.

    Returns
    -------
        tuple[int, int]: The new soft and hard limits for open file descriptors.
    """
    limits = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.debug("Initial limit numbers for open file descriptors for the current ANTA process: Soft Limit: %s | Hard Limit: %s", limits[0], limits[1])
    nofile = __NOFILE__ if limits[1] > __NOFILE__ else limits[1]
    logger.debug("Setting soft limit for open file descriptors for the current ANTA process to %s", nofile)
    resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, limits[1]))
    return resource.getrlimit(resource.RLIMIT_NOFILE)


def log_cache_statistics(devices: list[AntaDevice]) -> None:
    """Log cache statistics for each device in the inventory.

    Args:
    ----
        devices: List of devices in the inventory.
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


async def setup_inventory(inventory: AntaInventory, tags: set[str] | None, devices: set[str] | None, *, established_only: bool) -> AntaInventory | None:
    """Set up the inventory for the ANTA run.

    Args:
    ----
        inventory: AntaInventory object that includes the device(s).
        tags: Tags to filter devices from the inventory.
        devices: Devices on which to run tests. None means all devices.

    Returns
    -------
        AntaInventory | None: The filtered inventory or None if there are no devices to run tests on.
    """
    if len(inventory) == 0:
        logger.info("The inventory is empty, exiting")
        return None

    # Filter the inventory based on the CLI provided tags and devices if any
    selected_inventory = inventory.get_inventory(tags=tags, devices=devices) if tags or devices else inventory

    # Connect to the devices
    await selected_inventory.connect_inventory()

    # Remove devices that are unreachable
    inventory = selected_inventory.get_inventory(established_only=established_only)

    # If there are no devices in the inventory after filtering, exit
    if not inventory.devices:
        msg = f'No reachable device {f"matching the tags {tags} " if tags else ""}was found.{f" Selected devices: {devices} " if devices is not None else ""}'
        logger.warning(msg)
        return None

    return selected_inventory


async def prepare_tests(inventory: AntaInventory, catalog: AntaCatalog, tests: set[str] | None, tags: set[str] | None) -> set[AntaTestRunner] | None:
    """Prepare the tests to run.

    Args:
    ----
        inventory: AntaInventory object that includes the device(s).
        catalog: AntaCatalog object that includes the list of tests.
        tests: Tests to run against devices. None means all tests.
        tags: Tags to filter devices from the inventory.

    Returns
    -------
        set[AntaTestRunner] | None: The selected tests to run or None if there are no tests to run.
    """
    # Build indexes for the catalog. If there are CLI provided tests, filter the indexes based on these tests
    catalog.build_indexes(filtered_tests=tests)

    # Using a set to avoid inserting duplicate tests
    selected_tests: set[AntaTestRunner] = set()

    # Create AntaTestRunner tuples from the tags
    for device in inventory.devices:
        if tags:
            # If there are CLI tags, only execute tests with matching tags
            selected_tests.update((test, device) for test in catalog.get_tests_by_tags(tags))
        else:
            # If there is no CLI tags, execute all tests that do not have any tags
            selected_tests.update((test, device) for test in catalog.tag_to_tests[None])

            # Then add the tests with matching tags from device tags
            selected_tests.update((test, device) for test in catalog.get_tests_by_tags(device.tags))

    if not selected_tests:
        msg = (
            f"There are no tests{f' matching the tags {tags} ' if tags else ' '}to run in the current test catalog and device inventory, please verify your inputs."
        )
        logger.warning(msg)
        return None

    return selected_tests


async def main(  # noqa: PLR0913
    manager: ResultManager,
    inventory: AntaInventory,
    catalog: AntaCatalog,
    devices: set[str] | None = None,
    tests: set[str] | None = None,
    tags: set[str] | None = None,
    *,
    established_only: bool = True,
) -> None:
    # pylint: disable=too-many-arguments
    """Run ANTA.

    Use this as an entrypoint to the test framework in your script.
    ResultManager object gets updated with the test results.

    Args:
    ----
        manager: ResultManager object to populate with the test results.
        inventory: AntaInventory object that includes the device(s).
        catalog: AntaCatalog object that includes the list of tests.
        devices: Devices on which to run tests. None means all devices. These may come from the `--device / -d` CLI option in NRFU.
        tests: Tests to run against devices. None means all tests. These may come from the `--test / -t` CLI option in NRFU.
        tags: Tags to filter devices from the inventory. These may come from the `--tags` CLI option in NRFU.
        established_only: Include only established device(s).
    """
    # Adjust the maximum number of open file descriptors for the ANTA process
    limits = adjust_rlimit_nofile()

    if not catalog.tests:
        logger.info("The list of tests is empty, exiting")
        return

    # Setup the inventory
    selected_inventory = await setup_inventory(inventory, tags, devices, established_only=established_only)
    if selected_inventory is None:
        return

    # Prepare the tests
    selected_tests = await prepare_tests(selected_inventory, catalog, tests, tags)
    if selected_tests is None:
        return

    run_info = (
        "--- ANTA NRFU Run Information ---\n"
        f"Number of devices: {len(selected_inventory)} ({len(inventory)} established)\n"
        f"Total number of selected tests: {len(selected_tests)}\n"
        f"Maximum number of open file descriptors for the current ANTA process: {limits[0]}\n"
        "---------------------------------"
    )

    logger.info(run_info)

    if len(selected_tests) > limits[0]:
        logger.warning(
            "The number of concurrent tests is higher than the open file descriptors limit for this ANTA process.\n"
            "Errors may occur while running the tests.\n"
            "Please consult the ANTA FAQ."
        )

    coros = []
    for test_definition, device in selected_tests:
        try:
            test_instance = test_definition.test(device=device, inputs=test_definition.inputs)
            coros.append(test_instance.test())
        except Exception as e:  # noqa: PERF203, pylint: disable=broad-exception-caught
            # An AntaTest instance is potentially user-defined code.
            # We need to catch everything and exit gracefully with an error message.
            message = "\n".join(
                [
                    f"There is an error when creating test {test_definition.test.__module__}.{test_definition.test.__name__}.",
                    f"If this is not a custom test implementation: {GITHUB_SUGGESTION}",
                ],
            )
            anta_log_exception(e, message, logger)

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=len(coros))

    logger.info("Running ANTA tests...")
    test_results = await asyncio.gather(*coros)
    for r in test_results:
        manager.add(r)

    log_cache_statistics(inventory.devices)
