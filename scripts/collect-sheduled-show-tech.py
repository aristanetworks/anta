#!/usr/bin/env python3
"""
This script collects all the tech-support files stored on Arista switches flash
"""

# disabling duplicate-code for scripts as this is expected between scripts
# pylint: disable=R0801

import logging
import ssl
from getpass import getpass
from time import strftime, gmtime
from argparse import ArgumentParser
import os
from typing import Tuple
import paramiko
from jsonrpclib import jsonrpc
from scp import SCPClient
from tqdm import tqdm
from anta.inventory import AntaInventory

PORT = 22

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context
date = strftime("%d %b %Y %H:%M:%S", gmtime())


def device_directories(device: str, root_dir: str) -> Tuple[str, str]:
    """
    return a tuple containing the show_tech_directory and the device_directory
    """
    cwd = os.getcwd()
    show_tech_directory = cwd + "/" + root_dir
    device_directory = show_tech_directory + "/" + device
    for directory in [show_tech_directory, device_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    result = show_tech_directory, device_directory
    return result


def create_ssh_client(
    device: str, port: int, username: str, password: str
) -> paramiko.SSHClient:
    """
    return a connected ssh client
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(device, port, username, password)
    return client


def report_unreachable_devices(inventory: AntaInventory) -> None:
    """
    report unreachable devices
    """
    devices = inventory.get_inventory(established_only=False)
    for device in devices:
        if device.established is False:  # type: ignore
            print(f"Could not connect to device {str(device.host)}")  # type: ignore


def main() -> None:
    """
    Main script routine
    """
    logging.disable(level=logging.WARNING)
    parser = ArgumentParser(description="Collect all the tech-support files")
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)
    parser.add_argument(
        "-o", help="Output directory", dest="output_directory", required=True
    )
    args = parser.parse_args()
    args.password = getpass(prompt="Device password: ")

    print("Checking connectivity to devices .... please be patient ... ")

    inventory = AntaInventory(
        inventory_file=args.file,
        username=args.username,
        password=args.password,
        auto_connect=True,
        timeout=2,
    )

    inv_size = inventory.get_inventory(established_only=False)
    devices = inventory.get_inventory(established_only=True)
    number_of_reachable_devices = len(devices)
    number_of_unreachable_devices = len(inv_size) - number_of_reachable_devices
    if len(devices) > 0:
        # Progress bar
        pbar = tqdm(total=len(inv_size), desc="Collecting files from devices")
        pbar.update(number_of_unreachable_devices)
        # Collect all the tech-support files stored on Arista switches flash and copy them locally
        for device in devices:
            try:
                switch = device.session  # type: ignore
                host = str(device.host)  # type: ignore
                # Create one zip file named all_files.zip on the device with the all the show tech-support files in it
                zip_command = "bash timeout 30 zip /mnt/flash/schedule/all_files.zip /mnt/flash/schedule/tech-support/*"
                cmds = [zip_command]
                switch.runCmds(1, cmds, "text")
                # Get device hostname
                cmds = ["show hostname"]
                result = switch.runCmds(1, cmds, "json")
                hostname = result[0]["hostname"]
                # Create directories
                output_dir = device_directories(hostname, args.output_directory)
                # Connect to the device using SSH
                ssh = create_ssh_client(host, PORT, args.username, args.password)
                # Get the zipped file all_files.zip using SCP and save it locally
                my_path = output_dir[1] + "/" + date + "_" + hostname + ".zip"
                scp = SCPClient(ssh.get_transport())
                scp.get("/mnt/flash/schedule/all_files.zip", local_path=my_path)
                scp.close()
                # Delete the created zip file on the device
                cmds = ["bash timeout 30 rm /mnt/flash/schedule/all_files.zip"]
                switch.runCmds(1, cmds, "text")
                pbar.update(1)
            except jsonrpc.AppError:
                print(f"Could not collect show tech files on device {host}")
                pbar.update(1)
        pbar.close()
        print(f"Done. Files are in the directory {output_dir[0]}")
    else:
        print("can not connect to any device")

    report_unreachable_devices(inventory)


if __name__ == "__main__":
    main()
