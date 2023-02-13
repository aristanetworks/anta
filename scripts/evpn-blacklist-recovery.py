#!/usr/bin/env python3

# disabling duplicate-code for scripts as this is expected between scripts
# pylint: disable=R0801

"""
This script clears on devices the list of MAC addresses which are blacklisted in EVPN
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

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logger.setLevel(loglevel)


async def clear_evpn_blacklisted_mac_addresses(
    inv: AntaInventory, enable_pass: str
) -> None:
    """
    clear EVPN blacklisted mac addresses
    """
    logger.info("Connecting to devices...")
    await inv.connect_inventory()
    devices = inv.get_inventory(established_only=True)
    for device in devices:  # TODO: should use asyncio.gather instead of a loop.
        try:
            await device.session.cli(
                commands=[
                    {"cmd": "enable", "input": enable_pass},
                    "clear bgp evpn host-flap",
                ],
                ofmt="json",
            )
            logger.info(
                f"Cleared the EVPN blacklisted mac addresses on device {device.name}"
            )
        # In this case we want to catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                f"Could not clear the EVPN blacklisted mac addresses on device {device.name}"
            )
            logger.debug(
                f"Exception raised for device {device.name} - {type(e).__name__}: {str(e)}"
            )
            logger.debug(traceback.format_exc())


def main() -> None:
    """main"""
    parser = ArgumentParser(
        description="Clear the list of MAC addresses which are blacklisted in EVPN"
    )
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
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

    logger.info(
        "Clearing on all the devices the list of MAC addresses which are blacklisted in EVPN ... please be patient ..."
    )
    inventory = AntaInventory(
        inventory_file=args.file, username=args.username, password=args.password
    )

    asyncio.run(clear_evpn_blacklisted_mac_addresses(inventory, args.enable_pass))


if __name__ == "__main__":
    main()
