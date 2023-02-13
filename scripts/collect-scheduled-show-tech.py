#!/usr/bin/env python3

"""
This script collects all the tech-support files stored on Arista switches flash
"""

import asyncio
import logging
import os
import traceback
from argparse import ArgumentParser
from getpass import getpass
from time import gmtime, strftime
from typing import Tuple

import paramiko
from aioeapi import EapiCommandError
from rich.logging import RichHandler
from scp import SCPClient

from anta.inventory import AntaInventory

ZIP_FILE = "/mnt/flash/schedule/all_files.zip"

date = strftime("%d %b %Y %H:%M:%S", gmtime())
logger = logging.getLogger(__name__)


def setup_logging(level: str = "info") -> None:
    """
    Configure logging for check-devices execution

    Helpers to set logging for
    * anta.inventory
    * anta.result_manager
    * check-devices

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.
    """
    loglevel = getattr(logging, level.upper())

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logger.setLevel(loglevel)


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
    dev: str, port: int, username: str, password: str
) -> paramiko.SSHClient:
    """
    return a connected ssh client
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(dev, port, username, password)
    return client


async def collect_scheduled_show_tech(inv: AntaInventory, root_dir: str) -> None:
    """
    Collect scheduled show-tech on devices
    """
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True)
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
                    device.host, device.port, device.username, device.password
                )
                # Get the zipped file all_files.zip using SCP and save it locally
                my_path = f"{output_dir[1]}/{date}_{device.name}.zip"
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


def main() -> None:
    """main"""
    parser = ArgumentParser(description="Collect all the tech-support files")
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)
    parser.add_argument(
        "-o", help="Output directory", dest="output_directory", required=True
    )
    parser.add_argument(
        "-log",
        "--loglevel",
        default="info",
        help="Provide logging level. Example --loglevel debug, default=info",
    )
    args = parser.parse_args()
    args.password = getpass(prompt="Device password: ")
    setup_logging(level=args.loglevel)

    inventory = AntaInventory(
        inventory_file=args.file, username=args.username, password=args.password
    )

    asyncio.run(collect_scheduled_show_tech(inventory, args.output_directory))


if __name__ == "__main__":
    main()
