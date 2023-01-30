#!/usr/bin/python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import logging
import traceback
from typing import List

from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

logger = logging.getLogger(__name__)


async def clear_counters_utils(anta_inventory: AntaInventory, enable_pass: str, tags: List[str]) -> None:
    """
    clear counters
    """
    async def clear(dev: InventoryDevice) -> None:
        logger.info(f'Clearing counter for {dev.name} ({dev.hw_model})')
        commands = [{"cmd": "enable", "input": enable_pass}, "clear counters"]
        if dev.hw_model not in ["cEOSLab", "vEOS-lab"]:
            commands.append("clear hardware counter drop")
        try:
            await dev.session.cli(commands=commands)
            logger.info(f"Cleared counters on {dev.name}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not clear counters on device {dev.name}")
            logger.debug(
                f"Exception raised for device {dev.name} - {type(e).__name__}: {str(e)}"
            )
            logger.debug(traceback.format_exc())

    logger.info('Reading inventory')
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags)
    logger.info('Execute command to remote devices')
    await asyncio.gather(*(clear(device) for device in devices))
