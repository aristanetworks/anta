#!/usr/bin/env python3

"""
This script collects show commands output from devices
"""

import asyncio
import logging
import os
import sys
import traceback
from argparse import ArgumentParser
from getpass import getpass
from typing import Dict, Tuple

from aioeapi import EapiCommandError
from rich.logging import RichHandler
from yaml import safe_load

from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

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


def device_directories(
    device: InventoryDevice, root_dir: str
) -> Tuple[str, str, str, str]:
    """
    Create device directories
    """
    cwd = os.getcwd()
    output_directory = os.path.dirname(f"{cwd}/{root_dir}/")
    device_directory = f"{output_directory}/{device.host}"
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
    result = output_directory, device_directory, json_directory, text_directory
    return result


async def collect_commands(
    inv: AntaInventory, enable_pass: str, commands: Dict[str, str], root_dir: str
) -> None:
    """
    Collect EOS commands
    """
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True)
    for device in devices:  # TODO: should use asyncio.gather instead of a loop.
        logger.info(f"Collecting show commands output to device {device.name}")
        output_dir = device_directories(device, root_dir)
        try:
            if "json_format" in commands:
                for command in commands["json_format"]:
                    result = await device.session.cli(
                        commands=[{"cmd": "enable", "input": enable_pass}, command],
                        ofmt="json",
                    )
                    outfile = f"{output_dir[2]}/{command}"
                    with open(outfile, "w", encoding="utf8") as out_fd:
                        out_fd.write(str(result[1]))
                    logger.info(f"Collected command '{command}' on {device.name}")
            if "text_format" in commands:
                for command in commands["text_format"]:
                    result = await device.session.cli(
                        commands=[{"cmd": "enable", "input": enable_pass}, command],
                        ofmt="text",
                    )
                    outfile = f"{output_dir[3]}/{command}"
                    with open(outfile, "w", encoding="utf8") as out_fd:
                        out_fd.write(result[1])
                    logger.info(f"Collected command '{command}' on {device.name}")
        except EapiCommandError as e:
            logger.error(f"Command failed on {device.name}: {e.errmsg}")
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not collect commands on device {device.name}")
            logger.debug(
                f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}"
            )

            logger.debug(traceback.format_exc())

            logger.debug(traceback.format_exc())


def main() -> None:
    """main"""
    parser = ArgumentParser(description="Collect output of EOS commands")
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)
    parser.add_argument(
        "-c",
        help="YAML file containing the list of EOS commands to collect",
        dest="eos_commands_file",
        required=True,
    )
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
    args.enable_pass = getpass(prompt="Enable password (if any): ")
    setup_logging(level=args.loglevel)

    try:
        with open(args.eos_commands_file, "r", encoding="utf8") as file:
            file_content = file.read()
            eos_commands = safe_load(file_content)
    except FileNotFoundError:
        logger.error(f"Error reading {args.eos_commands}")
        sys.exit(1)

    inventory = AntaInventory(
        inventory_file=args.file, username=args.username, password=args.password
    )

    asyncio.run(
        collect_commands(
            inventory, args.enable_pass, eos_commands, args.output_directory
        )
    )


if __name__ == "__main__":
    main()
