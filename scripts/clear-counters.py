#!/usr/bin/env python3

"""
This script clear counters on devices
"""

import logging
import ssl
from argparse import ArgumentParser
from getpass import getpass

from jsonrpclib import jsonrpc
from anta.inventory import AntaInventory

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context


def clear_counters(inventory, enable_pass):
    """
    clear counters
    """
    devices = inventory.get_inventory(established_only=True)
    for device in devices:
        switch = device.session
        try:
            if device.hw_model in ['cEOSLab', 'vEOS-lab']:
                switch.runCmds(1, [{"cmd": "enable", "input": enable_pass}, 'clear counters'])
                print(f'Cleared counters on {str(device.host)}')
            else:
                switch.runCmds(1, [{"cmd": "enable", "input": enable_pass},
                                   'clear counters', 'clear hardware counter drop'])
                print(f'Cleared counters on {str(device.host)}')
        except jsonrpc.AppError:
            print(f'Could not clear counters on device {str(device.host)}')
        except KeyError:
            print(f'Could not clear counters on device {str(device.host)}')


def report_unreachable_devices(inventory):
    """
    report unreachable devices
    """
    devices = inventory.get_inventory(established_only=False)
    for device in devices:
        if device.established is False:
            print(f'Could not connect to device {str(device.host)}')


def main():
    """
    Main.
    """
    logging.disable(level=logging.WARNING)

    parser = ArgumentParser(
        description='Clear counters on EOS devices'
        )
    parser.add_argument(
        '-i',
        help='Text file containing switches inventory',
        dest='file',
        required=True
        )
    parser.add_argument(
        '-u',
        help='Devices username',
        dest='username',
        required=True
        )

    args = parser.parse_args()
    args.password = getpass(prompt='Device password: ')
    args.enable_pass = getpass(prompt='Enable password (if any): ')
    print('Clearing counters on devices .... please be patient ... ')
    inventory = AntaInventory(
        inventory_file=args.file,
        username=args.username,
        password=args.password,
        auto_connect=True,
        timeout=2
    )
    clear_counters(inventory, args.enable_pass)
    report_unreachable_devices(inventory)


if __name__ == '__main__':
    main()
