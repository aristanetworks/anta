#!/usr/bin/env python3

# This script collects all the tech-support files stored on Arista switches flash and copies them locally

# Imports

import ssl
import paramiko
from jsonrpclib import Server
from scp import SCPClient
from time import strftime, gmtime
from argparse import ArgumentParser
from getpass import getpass
import os
from sys import exit
from socket import setdefaulttimeout

port = 22

ssl._create_default_https_context = ssl._create_unverified_context
date = strftime("%d %b %Y %H:%M:%S", gmtime())

def device_directories (device, root_dir):
    cwd = os.getcwd()
    show_tech_directory = cwd + '/' + root_dir
    device_directory = show_tech_directory + '/' + device
    for directory in [show_tech_directory, device_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    result = show_tech_directory, device_directory
    return result

def createSSHClient (device, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(device, port, username, password)
    return client

def main():
    parser = ArgumentParser(
        description='Collect all the tech-support files'
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
        '-o',
        help='Output directory',
        dest='output_directory',
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

    # Remove unreachable devices from devices list

    unreachable = []

    print('Connecting to devices .... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url = 'https://%s:%s@%s/command-api' %(args.username, args.password, device)
            switch = Server(url)
            response = switch.runCmds(1, ['enable'])
        except:
            unreachable.append(device)

    for item in unreachable:
        devices.remove(item)
        print("Can not connect to device " + item)

    # Collect all the tech-support files stored on Arista switches flash and copy them locally

    for device in devices:
        url = "https://" + args.username + ":" + args.password + "@" + device + "/command-api"
        try:
            # Create one zip file named all_files.zip on the device with the all the show tech-support files in it
            switch = Server(url)
            cmds=['bash timeout 30 zip /mnt/flash/schedule/all_files.zip /mnt/flash/schedule/tech-support/*']
            switch.runCmds(1,cmds, 'text')
            # Get device hostname
            cmds=['show hostname']
            result = switch.runCmds(1,cmds, 'json')
            hostname = result[0]['hostname']
            # Create directories
            output_dir = device_directories (hostname, args.output_directory)
            # Connect to the device using SSH
            ssh = createSSHClient(device, port, args.username, args.password)
            # Get the zipped file all_files.zip using SCP and save it locally
            my_path = output_dir[1] + '/' + date + '_' + hostname + '.zip'
            scp = SCPClient(ssh.get_transport())
            scp.get("/mnt/flash/schedule/all_files.zip",local_path = my_path)
            scp.close()
            # Delete the created zip file on the device
            cmds=[bash timeout 30 rm /mnt/flash/schedule/all_files.zip']
            switch.runCmds(1,cmds, 'text')
        except:
            print('You are unlucky today! ' + device + ' does not like this script')

if __name__ == '__main__':
    main()
