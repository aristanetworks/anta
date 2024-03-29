# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=too-many-branches
"""ANTA runner function."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from anta import GITHUB_SUGGESTION
from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.device import AntaDevice
from anta.logger import anta_log_exception
from anta.models import AntaTest

if TYPE_CHECKING:
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)

AntaTestRunner = tuple[AntaTestDefinition, AntaDevice]


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


async def main(  # noqa: PLR0913
    manager: ResultManager,
    inventory: AntaInventory,
    catalog: AntaCatalog,
    devices: list[str] | None = None,
    tests: list[str] | None = None,
    tags: list[str] | None = None,
    *,
    established_only: bool = True,
) -> None:
    # pylint: disable=too-many-arguments
    # sourcery skip: merge-duplicate-blocks, remove-redundant-if, split-or-ifs
    """Run ANTA.

    Use this as an entrypoint to the test framwork in your script.
    ResultManager object gets updated with the test results.

    Args:
    ----
        manager: ResultManager object to populate with the test results.
        inventory: AntaInventory object that includes the device(s).
        catalog: AntaCatalog object that includes the list of tests.
        devices: devices on which to run tests. None means all devices.
        tests: tests to run against devices. None means all tests.
        tags: List of tags to filter devices from the inventory. Defaults to None.
        established_only: Include only established device(s). Defaults to True.
    """
    if not catalog.tests:
        logger.info("The list of tests is empty, exiting")
        return
    if len(inventory) == 0:
        logger.info("The inventory is empty, exiting")
        return

    # Filter the inventory based on tags and devices parameters
    inventory = inventory.get_inventory(
        tags=tags,
        devices=devices,
    )
    await inventory.connect_inventory()

    # Remove devices that are unreachable
    inventory = inventory.get_inventory(established_only=established_only)

    if not inventory.devices:
        msg = f"No reachable device {f'matching the tags {tags} ' if tags else ''}was found."
        logger.warning(msg)
        return
    coros = []

    # Select the tests from the catalog
    if tests:
        catalog = AntaCatalog(catalog.get_tests_by_names(tests))

    # Using a set to avoid inserting duplicate tests
    selected_tests: set[AntaTestRunner] = set()

    # Create AntaTestRunner tuples from the tags
    for device in inventory.devices:
        if tags:
            # If there are CLI tags, only execute tests with matching tags
            selected_tests.update((test, device) for test in catalog.get_tests_by_tags(tags))
        else:
            # If there is no CLI tags, execute all tests that do not have any filters
            selected_tests.update((t, device) for t in catalog.tests if t.inputs.filters is None or t.inputs.filters.tags is None)

            # Then add the tests with matching tags from device tags
            selected_tests.update((t, device) for t in catalog.get_tests_by_tags(device.tags))

    if not selected_tests:
        msg = f"There is no tests{f' matching the tags {tags} ' if tags else ' '}to run in the current test catalog, please verify your inputs."
        logger.warning(msg)
        return

    for test_definition, device in selected_tests:
        try:
            test_instance = test_definition.test(device=device, inputs=test_definition.inputs)

            coros.append(test_instance.test())
        except Exception as e:  # pylint: disable=broad-exception-caught
            # An AntaTest instance is potentially user-defined code.
            # We need to catch everything and exit gracefully with an
            # error message
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
