#!/usr/bin/env python3

"""
This script collects all the tech-support files stored on Arista switches flash
"""

# Imports
import ssl
from socket import setdefaulttimeout
from getpass import getpass
import sys
from time import strftime, gmtime
from argparse import ArgumentParser
import os
import paramiko
from jsonrpclib import Server
from scp import SCPClient
from tqdm import tqdm

PORT = 22

# pylint: disable=protected-access
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

def create_ssh_client (device, port, username, password):
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
        with open(args.file, 'r', encoding='utf8') as file:
            devices = file.readlines()
    except:
        print('Error opening ' + args.file)
        sys.exit(1)

    for i,device in enumerate(devices):
        devices[i] = device.strip()
    
    # Remove unreachable devices from devices list

    unreachable = []

    print('Checking connectivity to devices .... please be patient ... ')

    for device in devices:
        try:
            setdefaulttimeout(5)
            url=f"https://{args.username}:{args.password}@{device}/command-api"
            switch = Server(url)
            switch.runCmds(1, ['enable'])
        except:
            unreachable.append(device)

    for item in unreachable:
        devices.remove(item)
        print("Can not connect to device " + item)

    # Progress bar 
    
    number_of_unreachable_devices = len(unreachable)
    number_of_reachable_devices = len(devices)
    pbar = tqdm(total = number_of_unreachable_devices + number_of_reachable_devices,\
         desc = 'Collecting files from devices')
    pbar.update(number_of_unreachable_devices)

    # Collect all the tech-support files stored on Arista switches flash and copy them locally

    for device in devices:
        url = "https://" + args.username + ":" + args.password + "@" + device + "/command-api"
        try:
            # Create one zip file named all_files.zip on the device 
            # with the all the show tech-support files in it
            switch = Server(url)
            to_zip = '/mnt/flash/schedule/tech-support/*'
            zip_file = '/mnt/flash/schedule/all_files.zip'
            zip_command = 'bash timeout 30 zip ' + zip_file + ' ' + to_zip
            cmds=[zip_command]
            switch.runCmds(1,cmds, 'text')
            # Get device hostname
            cmds=['show hostname']
            result = switch.runCmds(1,cmds, 'json')
            hostname = result[0]['hostname']
            # Create directories
            output_dir = device_directories (hostname, args.output_directory)
            # Connect to the device using SSH
            ssh = create_ssh_client(device, PORT, args.username, args.password)
            # Get the zipped file all_files.zip using SCP and save it locally
            my_path = output_dir[1] + '/' + date + '_' + hostname + '.zip'
            scp = SCPClient(ssh.get_transport())
            scp.get("/mnt/flash/schedule/all_files.zip",local_path = my_path)
            scp.close()
            # Delete the created zip file on the device
            cmds=['bash timeout 30 rm /mnt/flash/schedule/all_files.zip']
            switch.runCmds(1,cmds, 'text')
            pbar.update(1)
        except:
            print('You are unlucky today! ' + device + ' does not like this script')
            pbar.update(1)
    
    pbar.close()
    print('Done. Files are in the directory ' + output_dir[0])

if __name__ == '__main__':
    main()
