#!/usr/bin/env python3

"""
This script clears on devices the list of MAC addresses which are blacklisted in EVPN
"""

from argparse import ArgumentParser
from getpass import getpass
import ssl
import logging
from jsonrpclib import jsonrpc
from anta.inventory import AntaInventory

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context
logging.disable(level=logging.WARNING)

def clear_evpn_blacklisted_mac_addresses(inventory, enable_pass):
    """
    clear EVPN blacklisted mac addresses
    """
    devices = inventory.inventory_get(established_only = True)
    for device in devices:
        switch = device.session
        try:
            switch.runCmds(1,[{"cmd": "enable", "input": enable_pass},\
                 'clear bgp evpn host-flap'])
        except jsonrpc.AppError:
            print("Could not clear the EVPN blacklisted mac addresses on device " + str(device.host))

def report_unreachable_devices(inventory):
    """
    report unreachable devices
    """
    devices = inventory.inventory_get(established_only = False)
    for device in devices:
        if device.established is False:
            print("Could not connect on device " + str(device.host))

def main():
    """
    clear EVPN blacklisted mac addresses
    """
    parser = ArgumentParser(
        description='Clear the list of MAC addresses which are blacklisted in EVPN'
        )
    parser.add_argument(
        '-i',
        help='Text file containing a list of switches',
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

    print('Clearing on all the devices the list of MAC addresses which are blacklisted in EVPN ... please be patient ...')
    inventory = AntaInventory(inventory_file=args.file,username=args.username, password=args.password, auto_connect=True)
    clear_evpn_blacklisted_mac_addresses(inventory, args.enable_pass)
    report_unreachable_devices(inventory)

if __name__ == '__main__':
    main()
