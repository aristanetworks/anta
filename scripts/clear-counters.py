#!/usr/bin/env python3

"""
This script clear counters on devices
"""

# standard imports
from argparse import ArgumentParser
from getpass import getpass
import ssl
from anta.inventory import AntaInventory

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context

def clear_counters(inventory, enable_pass):
    """
    clear counters
    """ 
    devices = inventory.inventory_get(established_only = True)
    for device in devices:
        switch = device.session
        response = switch.runCmds(1, ['show version'], 'json')
        if response[0]['modelName'] in ['cEOSLab', 'vEOS-lab']:
            hardware_model = False
        else:
            hardware_model = True
        if hardware_model is True:
            switch.runCmds(1,[{"cmd": "enable", "input": enable_pass},\
                'clear counters', 'clear hardware counter drop'])
            print('Cleared counters on ' + str(device.host))
        elif hardware_model is False:
            switch.runCmds(1,[{"cmd": "enable", "input": enable_pass}, 'clear counters'])
            print('Cleared counters on ' + str(device.host))
        else:
            print('Could not clear counters on device ' + str(device.host))

def report_uncleared_counters(inventory):
    """
    report unreachable devices
    """
    devices = inventory.inventory_get(established_only = False)
    for device in devices:
        if device.established is False:
            print("Could not clear counters on device " + str(device.host))

def main():
    """
    test.
    """
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

    print('Password is: %s', str(args.password))
    inventory = AntaInventory(inventory_file=args.file,username=args.username, password=args.password, auto_connect=True)
    clear_counters(inventory, args.enable_pass)
    report_uncleared_counters(inventory)

if __name__ == '__main__':
    main()