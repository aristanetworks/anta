#!/usr/bin/env python3

"""
This script clear counters on devices
"""

# standard imports
from argparse import ArgumentParser
from getpass import getpass
import ssl
import sys
from socket import setdefaulttimeout
# third-party libraries
from jsonrpclib import Server,jsonrpc

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context

def main():

    parser = ArgumentParser(
        description='Clear counters on EOS devices'
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
        with open(args.file, 'r', encoding="utf8") as file:
            devices = file.readlines()
    except FileNotFoundError:
        print('Error reading ' + args.file)
        sys.exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    for device in devices:
        url=f"https://{args.username}:{args.password}@{device}/command-api"
        switch = Server(url)
        setdefaulttimeout(5)
        try:
            response = switch.runCmds(1, ['show version'], 'json')
            if response[0]['modelName'] in ['cEOSLab', 'vEOS-lab']:
                hardware_model = False
            else:
                hardware_model = True
            if hardware_model is True:
                switch.runCmds(1,[{"cmd": "enable", "input": args.enable_pass},\
                    'clear counters', 'clear hardware counter drop'])
                print('Cleared counters on ' + device)
            elif hardware_model is False:
                switch.runCmds(1,[{"cmd": "enable", "input": args.enable_pass}, 'clear counters'])
                print('Cleared counters on ' + device)
            else:
                print('Could not clear counters on device ' + device)
        except jsonrpc.TransportError:
            print('wrong credentials for ' + device)
        except OSError:
            print(device + ' is not reachable using eAPI')
        except jsonrpc.AppError:
            print("Could not clear counters on device " + device)
        except KeyError:
            print("Could not clear counters on device " + device)

if __name__ == '__main__':
    main()
