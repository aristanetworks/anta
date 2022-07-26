#!/usr/bin/env python3

"""
This script collects show commands output from devices
"""

# disabling duplicate-code for scripts as this is expected between scripts
# pylint: disable=R0801

import logging
import os
import ssl
import sys
from argparse import ArgumentParser
from getpass import getpass
from socket import setdefaulttimeout
from typing import Tuple
from jsonrpclib import jsonrpc
from yaml import safe_load
from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice

# pylint: disable=protected-access
ssl._create_default_https_context = ssl._create_unverified_context


def device_directories(
    device: InventoryDevice, root_dir: str
) -> Tuple[str, str, str, str]:
    """
    Create device directories
    """
    cwd = os.getcwd()
    output_directory = os.path.dirname(f"{cwd}/{root_dir}/")
    device_directory = f"{output_directory}/{device.host}"
    json_directory = f"{device_directory}/json"
    text_directory = f"{device_directory}/text"
    for directory in [
        output_directory,
        device_directory,
        json_directory,
        text_directory,
    ]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    result = output_directory, device_directory, json_directory, text_directory
    return result


def report_unreachable_devices(inventory: AntaInventory) -> None:
    """
    report unreachable devices
    """
    devices = inventory.get_inventory(established_only=False)
    for device in devices:
        if device.established is False:  # type: ignore
            print(f"Could not connect to device {device.host}")  # type: ignore


def main() -> None:
    """
    Main
    """
    logging.disable(level=logging.WARNING)
    parser = ArgumentParser(description="Collect output of EOS commands")
    parser.add_argument(
        "-i", help="Text file containing a list of switches", dest="file", required=True
    )
    parser.add_argument("-u", help="Devices username", dest="username", required=True)
    parser.add_argument(
        "-c",
        help="YAML file containing the list of EOS commands to collect",
        dest="eos_commands_file",
        required=True,
    )
    parser.add_argument(
        "-o", help="Output directory", dest="output_directory", required=True
    )
    args = parser.parse_args()
    args.password = getpass(prompt="Device password: ")
    args.enable_pass = getpass(prompt="Enable password (if any): ")

    try:
        with open(args.eos_commands_file, "r", encoding="utf8") as file:
            file_content = file.read()
            eos_commands = safe_load(file_content)
    except FileNotFoundError:
        print(f"Error reading {args.eos_commands}")
        sys.exit(1)

    print("Connecting to devices .... please be patient ... ")

    inventory = AntaInventory(
        inventory_file=args.file,
        username=args.username,
        password=args.password,
        auto_connect=True,
        timeout=2,
    )

    devices = inventory.get_inventory(established_only=True)
    for device in devices:
        switch = device.session  # type: ignore
        host = str(device.host)  # type: ignore
        print("\n")
        print(f"Collecting show commands output to device {host}")
        output_dir = device_directories(device, args.output_directory)  # type: ignore
        if "json_format" in eos_commands:
            for eos_command in eos_commands["json_format"]:
                setdefaulttimeout(10)
                try:
                    result = switch.runCmds(
                        1,
                        [{"cmd": "enable", "input": args.enable_pass}, eos_command],
                        "json",
                    )
                    outfile = output_dir[2] + "/" + eos_command
                    with open(outfile, "w", encoding="utf8") as out_fd:
                        out_fd.write(str(result[1]))
                except jsonrpc.AppError:
                    print(f"Unable to collect and save the json command {eos_command}")
        if "text_format" in eos_commands:
            for eos_command in eos_commands["text_format"]:
                setdefaulttimeout(10)
                try:
                    result = switch.runCmds(
                        1,
                        [{"cmd": "enable", "input": args.enable_pass}, eos_command],
                        "text",
                    )
                    outfile = output_dir[3] + "/" + eos_command
                    with open(outfile, "w", encoding="utf8") as out_fd:
                        out_fd.write(result[1]["output"])
                except jsonrpc.AppError:
                    print(f"Unable to collect and save the text command {eos_command}")

    report_unreachable_devices(inventory)


if __name__ == "__main__":
    main()
