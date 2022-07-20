#!/usr/bin/env python3

"""
This script run tests on devices
"""

from argparse import ArgumentParser
from getpass import getpass
import sys
from datetime import datetime
import ssl
from math import ceil
from socket import setdefaulttimeout
from json import dumps
from jsonrpclib import Server, jsonrpc
from prettytable import PrettyTable
from yaml import safe_load
from colorama import Fore
import anta.tests

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context


def create_connections_dict(text_file, device_username, device_password, output_file):
    connections = {}
    try:
        with open(text_file, 'r', encoding='utf8') as file:
            for device in file:
                device = device.strip()
                connections[device] = Server(
                    f"https://{device_username}:{device_password}@{device}/command-api"
                )
    except FileNotFoundError:
        print('Error opening ' + text_file)
        sys.exit(1)
    # Delete unreachable devices from connections dict
    unreachable = []

    print('Testing devices .... please be patient ... ')

    for device, connection in connections.items():
        try:
            setdefaulttimeout(5)
            connection.runCmds(1, ['show version'])
        except jsonrpc.TransportError:
            print('wrong credentials for ' + device)
            unreachable.append(device)
        except OSError:
            print(device + ' is not reachable using eAPI')
            unreachable.append(device)

    for key in unreachable:
        connections.pop(key)

    with open(output_file, 'w', encoding="utf8") as outfile:
        now = datetime.now()
        outfile.write(now.strftime("%c"))
        outfile.write('\n')
        outfile.write('devices inventory file was ' + text_file)
        outfile.write('\n')
        outfile.write('devices username was ' + device_username)
        outfile.write('\n')
        outfile.write('list of unreachable devices is \n')
        for element in unreachable:
            outfile.write(element + "\n")

    return connections


def main():
    parser = ArgumentParser(
        description='EOS devices health checks'
        )
    parser.add_argument(
        '-i',
        help='Text file containing a list of switches, one per line',
        dest='inventory_file',
        required=True
        )
    parser.add_argument(
        '-u',
        help='Devices username',
        dest='username',
        required=True
        )
    parser.add_argument(
        '-t',
        help='Text file containing the tests',
        dest='test_catalog',
        required=True
        )
    parser.add_argument(
        '-o',
        help='Output file',
        dest='output_file',
        required=True
        )
    args = parser.parse_args()
    args.password = getpass(prompt='Device password: ')
    args.enable_pass = getpass(prompt='Enable password (if any): ')

    # Create connections dict
    connections = create_connections_dict(
        args.inventory_file, args.username, args.password, args.output_file)

    try:
        with open(args.test_catalog, 'r', encoding='utf8') as file:
            test_catalog = safe_load(file)
    except FileNotFoundError:
        print('Error opening ' + args.test_catalog)
        sys.exit(1)

    # Create the dictionnary test_summary for test results and run the tests
    test_summary = {}
    for device, connection in connections.items():
        print('Running tests on device ' + device + ' ...')
        test_summary[device] = {}
        for test, test_def in test_catalog.items():
            # Run test cases
            test_kwargs = {}
            if 'name' in test_def:
                func_name = test_def['name']
                test_kwargs = {k: v for k, v in test_def.items() if k != 'name'}
            else:
                func_name = test_def
            test_summary[device][test] = (getattr(anta.tests, func_name)
                                          (connection, args.enable_pass, **test_kwargs))

    # Replace True/False/None with Pass/Fail/Skip in the test_summary dictionnary
    for device in sorted(test_summary):
        for test in sorted(test_catalog):
            if test_summary[device][test] is True:
                test_summary[device][test] = Fore.GREEN + 'Pass' + Fore.RESET
            elif test_summary[device][test] is False:
                test_summary[device][test] = Fore.RED + 'Fail' + Fore.RESET
            elif test_summary[device][test] is None:
                test_summary[device][test] = Fore.BLUE + 'Skip' + Fore.RESET

    # Use prettytable so we will display data in a visually appealing format
    x = PrettyTable(padding_width=2)
    fields = ['devices']
    for test in sorted(test_catalog):
        fields.append(test)
    x.field_names = fields
    for device in sorted(test_summary):
        row = [device]
        for test in sorted(test_catalog):
            row.append(test_summary[device][test])
        x.add_row(row)

    # Split the table into t tables of c columns each
    c = 12
    lenx = len(fields)
    t = ceil(lenx/c)

    print("Test results are saved on " + args.output_file)

    # Write tests result to an external file
    with open(args.output_file, 'a', encoding="utf8") as outfile:
        outfile.write('tests file was ' + args.test_catalog)
        outfile.write('\n\n')
        outfile.write('***** Results *****\n')
        outfile.write('\n')
        for i in range(t):
            start = (i * (c - 1) + 1)
            stop = ((c - 1) * (i + 1)) + 1
            y = ["devices"] + fields[start:stop]
            outfile.write(x.get_string(fields=y))
            outfile.write('\n')

        outfile.write('\n')
        outfile.write('***** Tests *****\n')
        outfile.write('\n')
        for test in sorted(test_catalog):
            outfile.write(test + '\t ' + dumps(test_catalog[test]))
            outfile.write('\n')
        outfile.write('\n')


if __name__ == '__main__':
    main()
