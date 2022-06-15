#!/usr/bin/env python3

import ssl
from argparse import ArgumentParser
from getpass import getpass
from sys import exit
from socket import setdefaulttimeout
from jsonrpclib import Server

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
    except:
        print('Error opening ' + args.file)
        exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    unreachable = []

    print('Testing devices reachability .... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
            switch = Server(url)
            switch.runCmds(1, ['show version'])
        except:
            unreachable.append(device)

    if unreachable == []:
        print('All devices from the file ' + args.file + ' are reachable using eAPI')
    else:
        for item in unreachable:
            print("Can not connect to device " + item + " using eAPI")

if __name__ == '__main__':
    main()
