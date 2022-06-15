#!/usr/bin/env python3

import os
import ssl
from sys import exit
from argparse import ArgumentParser
from getpass import getpass
from socket import setdefaulttimeout
from jsonrpclib import Server
from yaml import safe_load

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context

def device_directories (device, root_dir):
    cwd = os.getcwd()
    output_directory = os.path.dirname(cwd + "/" + root_dir + "/")
    device_directory = output_directory + '/' + device
    json_directory = device_directory + '/json'
    text_directory = device_directory + '/text'
    for directory in [output_directory, device_directory, json_directory, text_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    result = output_directory, device_directory, json_directory, text_directory
    return result

def main():
    parser = ArgumentParser(
        description='Collect output of EOS commands'
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
    parser.add_argument(
        '-c',
        help='YAML file containing the list of EOS commands to collect',
        dest='eos_commands',
        required=True
        )
    parser.add_argument(
        '-o',
        help='Output directory',
        dest='output_directory',
        required=True
        )
    args = parser.parse_args()
    args.password = getpass(prompt='Device password: ')
    args.enable_pass = getpass(prompt='Enable password (if any): ')

    try:
        with open(args.eos_commands, 'r', encoding='utf8') as file:
            eos_commands = file.read()
            eos_commands = safe_load(eos_commands)
    except:
        print('Error opening ' + args.eos_commands)
        exit(1)

    try:
        with open(args.file, 'r', encoding='utf8') as file:
            devices = file.readlines()
    except:
        print('Error opening ' + args.file)
        exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()

    # Delete unreachable devices from devices list
    unreachable = []

    print('Connecting to devices .... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
            switch = Server(url)
            response = switch.runCmds(1, ['show version'])
        except:
            unreachable.append(device)

    for item in unreachable:
        devices.remove(item)
        print("Can not connect to device " + item)

    for device in devices:
        url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
        switch = Server(url)
        print('\n')
        print('Collecting show commands output on device ' + device)
        output_dir = device_directories (device, args.output_directory)
        if 'json_format' in eos_commands:
            for eos_command in eos_commands['json_format']:
                try:
                    setdefaulttimeout(10)
                    result=switch.runCmds\
                        (1, [{"cmd": "enable", "input": args.enable_pass}, eos_command], 'json')
                    outfile = output_dir[2] + '/' + eos_command
                    outfile = open(outfile, 'w', encoding='utf8')
                    outfile.write(str(result[1]))
                    outfile.close()
                except:
                    print('Unable to collect and save the json command ' + eos_command)
        if 'text_format' in eos_commands:
            for eos_command in eos_commands['text_format']:
                try:
                    setdefaulttimeout(10)
                    result=switch.runCmds\
                        (1, [{"cmd": "enable", "input": args.enable_pass}, eos_command], 'text')
                    outfile = output_dir[3] + '/' + eos_command
                    outfile = open(outfile, 'w', encoding='utf8')
                    outfile.write(result[1]['output'])
                    outfile.close()
                except:
                    print('Unable to collect and save the text command ' + eos_command)

if __name__ == '__main__':
    main()
