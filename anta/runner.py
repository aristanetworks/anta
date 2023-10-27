# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=too-many-branches
"""
ANTA runner function
"""
from __future__ import annotations

import asyncio
import itertools
import logging
from typing import Union

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.tools.misc import anta_log_exception

logger = logging.getLogger(__name__)


def filter_tags(tags_cli: Union[list[str], None], tags_device: list[str], tags_test: list[str]) -> bool:
    """Implement filtering logic for tags"""
    return (tags_cli is None or any(t for t in tags_cli if t in tags_device)) and any(t for t in tags_device if t in tags_test)


async def main(
    manager: ResultManager,
    inventory: AntaInventory,
    catalog: AntaCatalog,
    tags: list[str] | None = None,
    established_only: bool = True,
) -> None:
    """
    Main coroutine to run ANTA.
    Use this as an entrypoint to the test framwork in your script.

    Args:
        manager: ResultManager object to populate with the test results.
        inventory: AntaInventory object that includes the device(s).
        catalog: AntaCatalog object that includes the list of tests.
        tags: List of tags to filter devices from the inventory. Defaults to None.
        established_only: Include only established device(s). Defaults to True.

    Returns:
        any: ResultManager object gets updated with the test results.
    """

    catalog.check()
    if not catalog.tests:
        logger.info("The list of tests is empty, exiting")
        return

    if len(inventory) == 0:
        logger.info("The inventory is empty, exiting")
        return

    await inventory.connect_inventory()

    # asyncio.gather takes an iterator of the function to run concurrently.
    # we get the cross product of the devices and tests to build that iterator.
    devices = inventory.get_inventory(established_only=established_only, tags=tags).values()

    if len(devices) == 0:
        logger.info(
            f"No device in the established state '{established_only}' "
            f"{f'matching the tags {tags} ' if tags else ''}was found. There is no device to run tests against, exiting"
        )
        return

    coros = []

    for device, test_definition in itertools.product(devices, catalog.tests):
        if len(test_definition.inputs.filters.tags) == 0 or filter_tags(tags_cli=tags, tags_device=device.tags, tags_test=test_definition.inputs.filters.tags):
            try:
                # Instantiate AntaTest object
                test_instance = test_definition.test(device=device, inputs=test_definition.inputs)
                coros.append(test_instance.test(eos_data=None))
            except Exception as e:  # pylint: disable=broad-exception-caught
                message = "Error when creating ANTA tests"
                anta_log_exception(e, message, logger)

    if AntaTest.progress is not None:
        AntaTest.nrfu_task = AntaTest.progress.add_task("Running NRFU Tests...", total=len(coros))

    logger.info("Running ANTA tests...")
    res = await asyncio.gather(*coros, return_exceptions=True)
    logger.debug(res)
    for r in res:
        if isinstance(r, Exception):
            message = "Error in main ANTA Runner"
            anta_log_exception(r, message, logger)
        else:
            manager.add_test_result(r)

    # Get each device statistics
    for device in devices:
        if device.cache_statistics is not None:
            logger.info(f"Cache statistics for {device.name}: {device.cache_statistics}")
        else:
            logger.info(f"Caching is not enabled on {device.name}")
