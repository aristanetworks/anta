#!/usr/bin/env python3

"""
This script clears on devices the list of MAC addresses which are blacklisted in EVPN
"""

from argparse import ArgumentParser
from getpass import getpass
import ssl
import sys
from socket import setdefaulttimeout
from jsonrpclib import Server,jsonrpc

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context

def main():
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

    try:
        with open(args.file, 'r', encoding='utf8') as file:
            devices = file.readlines()
    except FileNotFoundError:
        print('Error reading ' + args.file)
        sys.exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    print('Clearing on all the devices the list of MAC addresses which are blacklisted in EVPN ...')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url=f"https://{args.username}:{args.password}@{device}/command-api"
            switch = Server(url)
            switch.runCmds(1,[{"cmd": "enable", "input": args.enable_pass},\
                 'clear bgp evpn host-flap'])
        except jsonrpc.TransportError:
            print('wrong credentials for ' + device)
        except OSError:
            print(device + ' is not reachable using eAPI')
        except jsonrpc.AppError:
            print("Could not run this command on device " + device)

if __name__ == '__main__':
    main()
