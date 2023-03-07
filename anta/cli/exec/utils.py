#!/usr/bin/env python
# coding: utf-8 -*-

"""
Exec CLI helpers
"""

import asyncio
import logging
import os
import traceback
from typing import Dict, List, Tuple
from time import gmtime, strftime
from aioeapi import EapiCommandError

from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

from typing import Tuple

import paramiko
from aioeapi import EapiCommandError
from scp import SCPClient


ZIP_FILE = "/mnt/flash/schedule/all_files.zip"

CURRENT_DATE = strftime("%d %b %Y %H:%M:%S", gmtime())

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


def device_directories(
    device: InventoryDevice, root_dir: str
) -> Tuple[str, str, str, str]:
    """
    Create device directories
    """
    cwd = os.getcwd()
    output_directory = os.path.dirname(f"{cwd}/{root_dir}/")
    device_directory = f"{output_directory}/{device.name}"
    json_directory = f"{device_directory}/json"
    text_directory = f"{device_directory}/text"
    for directory in [
        output_directory,
        device_directory,
        json_directory,
        text_directory,
    ]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    return output_directory, device_directory, json_directory, text_directory


async def collect_commands(inv: AntaInventory,  enable_pass: str, commands: Dict[str, str], root_dir: str, tags: List[str]) -> None:
    """
    Collect EOS commands
    """
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags)
    for device in devices:  # TODO: should use asyncio.gather instead of a loop.
        logger.info("----")
        logger.info(f"Collecting show commands output to device {device.name}")
        output_dir = device_directories(device, root_dir)
        try:
            if "json_format" in commands:
                for command in commands["json_format"]:
                    result = await device.session.cli(
                        commands=[
                            {"cmd": "enable", "input": enable_pass}, command],
                        ofmt='json'
                    )
                    outfile = f"{output_dir[2]}/{command}"
                    with open(outfile, "w", encoding="UTF-8") as out_fd:
                        out_fd.write(str(result[1]))
                    logger.info(
                        f"  * Collected command '{command}' on {device.name}")
            if "text_format" in commands:
                for command in commands["text_format"]:
                    result = await device.session.cli(
                        commands=[
                            {"cmd": "enable", "input": enable_pass}, command],
                        ofmt='text'
                    )
                    outfile = f"{output_dir[3]}/{command}"
                    with open(outfile, "w", encoding="UTF-8") as out_fd:
                        out_fd.write(f'{device.name}# {command}\n\r')
                        out_fd.write(result[1])
                    logger.info(
                        f"  * Collected command '{command}' on {device.name}")
        except EapiCommandError as e:
            logger.error(f"Command failed on {device.name}: {e.errmsg}")
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not collect commands on device {device.name}")
            logger.debug(
                f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}"
            )
            logger.debug(traceback.format_exc())


def device_directories(dev: str, root_dir: str) -> Tuple[str, str]:
    """
    return a tuple containing the show_tech_directory and the device_directory
    """
    cwd = os.getcwd()
    show_tech_directory = f"{cwd}/{root_dir}"
    device_directory = f"{show_tech_directory}/{dev}"
    for directory in [show_tech_directory, device_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    return show_tech_directory, device_directory


def create_ssh_client(
    dev: str, port: int, username: str, password: str, banner_timeout: int = 60
) -> paramiko.SSHClient:
    """
    return a connected ssh client
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=dev,
        port=port,
        username=username,
        password=password,
        banner_timeout=banner_timeout
    )
    return client


async def collect_scheduled_show_tech(inv: AntaInventory, root_dir: str, tags: List[str], ssh_port: int = 22) -> None:
    """
    Collect scheduled show-tech on devices
    """
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True, tags=tags)
    if len(devices) > 0:
        # Collect all the tech-support files stored on Arista switches flash and copy them locally
        for device in devices:  # TODO: should use asyncio.gather instead of a loop.
            try:
                # Create one zip file named all_files.zip on the device with the all the show tech-support files in it
                await device.session.cli(
                    command=f"bash timeout 30 zip {ZIP_FILE} /mnt/flash/schedule/tech-support/*"
                )
                logger.info(f"Created {ZIP_FILE} on device {device.name}")
                # Create directories
                output_dir = device_directories(device.name, root_dir)
                # Connect to the dpreevice using SSH
                ssh = create_ssh_client(
                    device.host, ssh_port, device.username, device.password
                )
                # Get the zipped file all_files.zip using SCP and save it locally
                my_path = f"{output_dir[1]}/{CURRENT_DATE}_{device.name}.zip"
                scp = SCPClient(ssh.get_transport())
                scp.get(ZIP_FILE, local_path=my_path)
                scp.close()
                # Delete the created zip file on the device
                await device.session.cli(command=f"bash timeout 30 rm {ZIP_FILE}")
                logger.info(f"Deleted {ZIP_FILE} on {device.name}")
            except EapiCommandError as e:
                logger.error(f"Command failed on {device.name}: {e.errmsg}")
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    f"Could not collect show tech files on device {device.name}"
                )
                logger.debug(
                    f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}"
                )
                logger.debug(traceback.format_exc())
        logger.info("Done collecting scheduled show-tech")
