#!/usr/bin/env python3

"""
This script clear counters on devices
"""

import asyncio
import logging
import traceback
from argparse import ArgumentParser
from getpass import getpass

from rich.logging import RichHandler

from anta.inventory import AntaInventory

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

    # FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logging.getLogger("anta.inventory").setLevel(loglevel)
    logger.setLevel(loglevel)


async def clear_counters(inventory: AntaInventory, enable_pass: str) -> None:
    """
    clear counters
    """
    await inventory.connect_inventory()
    devices = inventory.get_inventory(established_only=True)
    for device in devices:
        try:
            if device.hw_model in ["cEOSLab", "vEOS-lab"]:
                await device.session.cli(
                    commands=[{"cmd": "enable", "input": enable_pass}, "clear counters"]
                )
                logger.info(f"Cleared counters on {device.name}")
            else:
                await device.session.cli(
                    commands=[
                        {"cmd": "enable", "input": enable_pass},
                        "clear counters",
                        "clear hardware counter drop",
                    ],
                )
                logger.info(f"Cleared counters on {device.name}")
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Could not clear counters on device {device.name}")
            logger.debug(
                f"Exception raised for device {device.name}) - {type(e).__name__}: {str(e)}"
            )
            logger.debug(traceback.format_exc())


def report_unreachable_devices(inventory: AntaInventory) -> None:
    """
    report unreachable devices
    """
    devices = inventory.get_inventory(established_only=False)
    for device in devices:
        if device.established is False:
            logger.info(f"Could not connect to device {device.name}")


def main() -> None:
    """
    Main.
    """

    parser = ArgumentParser(description="Clear counters on EOS devices")
    parser.add_argument(
        "-i", help="Text file containing switches inventory", dest="file", required=True
    )
    parser.add_argument(
        "-log",
        "--loglevel",
        default="info",
        help="Provide logging level. Example --loglevel debug, default=info",
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)

    args = parser.parse_args()
    args.password = getpass(prompt="Device password: ")
    args.enable_pass = getpass(prompt="Enable password (if any): ")
    setup_logging(level=args.loglevel)
    logger.info("Clearing counters on devices .... please be patient ... ")
    inventory = AntaInventory(
        inventory_file=args.file,
        username=args.username,
        password=args.password,
        timeout=10
    )
    asyncio.run(clear_counters(inventory, args.enable_pass))
    report_unreachable_devices(inventory)


if __name__ == "__main__":
    main()
