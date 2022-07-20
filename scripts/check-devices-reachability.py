#!/usr/bin/env python3

"""
This script checks devices reachability
"""

import ssl
from argparse import ArgumentParser
from getpass import getpass
import sys
from socket import setdefaulttimeout
from jsonrpclib import Server, jsonrpc

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context


def main():
    parser = ArgumentParser(
        description='Verify devices eAPI connectivity'
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

    try:
        with open(args.file, 'r', encoding='utf8') as file:
            devices = file.readlines()
    except FileNotFoundError:
        print('Error reading ' + args.file)
        sys.exit(1)

    for i, device in enumerate(devices):
        devices[i] = device.strip()

    unreachable = []

    print('Testing devices reachability .... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url = f"https://{args.username}:{args.password}@{device}/command-api"
            switch = Server(url)
            switch.runCmds(1, ['show version'])
        except jsonrpc.TransportError:
            print('wrong credentials for ' + device)
            unreachable.append(device)
        except OSError:
            print(device + ' is not reachable using eAPI')
            unreachable.append(device)

    if not unreachable:
        print('All devices from the file ' + args.file + ' are reachable using eAPI')


if __name__ == '__main__':
    main()
