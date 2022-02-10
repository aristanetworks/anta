#!/usr/bin/env python3

from argparse import ArgumentParser
from getpass import getpass
from jsonrpclib import Server
import ssl
from sys import exit
from socket import setdefaulttimeout

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
        with open(args.file, 'r') as file:
            devices = file.readlines()
    except:
        print('Error opening ' + args.file)
        exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    print('Clearing on all the devices the list of MAC addresses which are blacklisted in EVPN ... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
            switch = Server(url)
            response = switch.runCmds(1, ['clear bgp evpn host-flap'])
        except:
            print("Can not do it on device " + device)

if __name__ == '__main__':
    main()
