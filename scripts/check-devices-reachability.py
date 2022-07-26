#!/usr/bin/env python3

"""
This script checks devices reachability
"""

# disabling duplicate-code for scripts as this is expected between scripts
# pylint: disable=R0801

import ssl
from argparse import ArgumentParser
from getpass import getpass
import logging
from anta.inventory import AntaInventory

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context
logging.disable(level=logging.WARNING)


def report_unreachable_devices(inventory: AntaInventory) -> None:
    """
    report unreachable devices
    """
    devices = inventory.get_inventory(established_only=False)
    all_devices_reachable = True
    for device in devices:
        if device.established is False:  # type: ignore
            print(f"Could not connect to device {str(device.host)}")  # type: ignore
            all_devices_reachable = False
    if all_devices_reachable is True:
        print("All devices from the file are reachable using eAPI")


def main() -> None:
    """
    check devices rechability
    """
    parser = ArgumentParser(description="Verify devices eAPI connectivity")
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)
    args = parser.parse_args()
    args.password = getpass(prompt="Device password: ")
    print("Testing devices reachability .... please be patient ... ")
    inventory = AntaInventory(
        inventory_file=args.file,
        username=args.username,
        password=args.password,
        auto_connect=True,
        timeout=1,
    )
    report_unreachable_devices(inventory)


if __name__ == "__main__":
    main()
