#!/usr/bin/env python3

from argparse import ArgumentParser
from getpass import getpass
from jsonrpclib import Server
import ssl
from sys import exit
from yaml import safe_load
from socket import setdefaulttimeout


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
        with open(args.file, 'r') as file:
            devices = file.readlines()
    except:
        print('Error opening ' + args.file)
        exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    for device in devices:
        url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
        switch = Server(url)
        setdefaulttimeout(5)
        try:
            result=switch.runCmds(1,[{"cmd": "enable", "input": args.enable_pass}, 'clear counters', 'clear hardware counter drop'])
            print('Cleared counters on ' + device)
        except:
            print("Can not connect to " + device)

if __name__ == '__main__':
    main()
