#!/usr/bin/env python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import logging
import os
import traceback
import itertools
from pathlib import Path
from time import gmtime, strftime
from typing import Dict, List, Literal

from aioeapi import EapiCommandError
from scp import SCPClient

from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

EOS_TECH_SUPPORT_ARCHIVE_ZIP = "/mnt/flash/schedule/all_files.zip"


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

    logger.info("Connecting to devices...")
    await anta_inventory.connect_inventory()
    devices = anta_inventory.get_inventory(established_only=True, tags=tags)
    logger.info('Execute command to remote devices')
    await asyncio.gather(*(clear(device) for device in devices))


async def collect_commands(inv: AntaInventory,  enable_pass: str, commands: Dict[str, str], root_dir: str, tags: List[str]) -> None:
    """
    Collect EOS commands
    """
    async def collect(dev: InventoryDevice, command: str, outformat: Literal['json', 'text']) -> None:
        try:
            outdir = Path() / root_dir / dev.name / outformat
            outdir.mkdir(parents=True, exist_ok=True)
            outfile = outdir / command
            result = await dev.session.cli(
                            commands=[
                                {"cmd": "enable", "input": enable_pass}, command],
                            ofmt=outformat
                        )
            with outfile.open(mode="w", encoding="UTF-8") as f:
                f.write(str(result[1]))
            logger.info(f"Collected command '{command}' from device {dev.name} ({dev.hw_model})")
        except EapiCommandError as e:
            logger.error(f"Command failed on {dev.name}: {e.errmsg}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not collect commands on device {dev.name}")
            logger.debug(
                f"Exception raised for device {dev.name} - {type(e).__name__}: {str(e)}"
            )
            logger.debug(traceback.format_exc())

    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags)
    logger.info('Collecting commands from remote devices')
    coros = [collect(device, command, 'json') for device, command in itertools.product(devices, commands["json_format"])]
    coros += [collect(device, command, 'text') for device, command in itertools.product(devices, commands["text_format"])]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for r in res:
        if isinstance(r, Exception):
            logger.error(f"Error when running tests: {r.__class__.__name__}: {r}")


def device_directories_show_tech_support(dev: str, root_dir: str) -> str:
    """
    return a tuple containing the show_tech_directory and the device_directory
    """
    device_directory = f"{os.getcwd()}/{root_dir}/{dev}"
    os.makedirs(device_directory, exist_ok=True)
    return device_directory


async def collect_scheduled_show_tech(inv: AntaInventory, root_dir: str, tags: List[str], ssh_port: int = 22) -> None:
    """
    Collect scheduled show-tech on devices
    """
    # Set date here so we have same timestamp for all devices.
    date_current = strftime("%d %b %Y %H:%M:%S", gmtime())
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags)
    if len(devices) > 0:
        # Collect all the tech-support files stored on Arista switches flash and copy them locally
        for device in devices:  # TODO: should use asyncio.gather instead of a loop.
            try:
                # Create one zip file named all_files.zip on the device with the all the show tech-support files in it
                await device.session.cli(
                    command=f"bash timeout 30 zip {EOS_TECH_SUPPORT_ARCHIVE_ZIP} /mnt/flash/schedule/tech-support/*"
                )
                logger.info(f"Created {EOS_TECH_SUPPORT_ARCHIVE_ZIP} on device {device.name}")

            except EapiCommandError as e:
                logger.error(f"Unable to create tech-support archove on {device.name}: {e.errmsg}")

            # Create directories
            tech_support_root_local_path = device_directories_show_tech_support(
                device.name, root_dir)

            # Connect to the device using SSH
            ssh = device.create_ssh_socket(ssh_port=ssh_port)

            try:
                # Get the zipped file all_files.zip using SCP and save it locally
                tech_support_device_local_path = f"{tech_support_root_local_path}/{date_current}_{device.name.lower()}.zip"
                with SCPClient(ssh.get_transport()) as scp:
                    scp.get(EOS_TECH_SUPPORT_ARCHIVE_ZIP, local_path=tech_support_device_local_path)

            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    f"Could not collect show tech files on device {device.name}"
                )
                logger.debug(
                    f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}"
                )
                logger.debug(traceback.format_exc())

            try:
                # Delete the created zip file on the device
                await device.session.cli(command=f"bash timeout 30 rm {EOS_TECH_SUPPORT_ARCHIVE_ZIP}")
                logger.info(f"Deleted {EOS_TECH_SUPPORT_ARCHIVE_ZIP} on {device.name}")
            except EapiCommandError as e:
                logger.error(f"Unable to delete tech-support archive on {device.name}: {e.errmsg}")

        logger.info("Done collecting scheduled show-tech")
