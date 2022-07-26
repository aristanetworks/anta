#!/usr/bin/env python3

"""
This script:
- uses CVP REST API to generate a token
- uses cvprac with this token to get the device inventory
- creates a text file with the devices IP address under the container passed in argument
- if we dont provide the argument `c` it creates a text file with all the devices IP address from the CVP inventory.

usage: ./create-devices-inventory-from-cvp.py --help
requirement: pip install cvprac==1.2.0
"""

# disabling duplicate-code for scripts as this is expected between scripts
# pylint: disable=R0801

import json
import os
from argparse import ArgumentParser
from getpass import getpass
from typing import Dict, Any, List
import yaml
import requests
import urllib3
from cvprac.cvp_client import CvpClient
from anta.inventory import AntaInventory

# Ignore certificate warnings
# https://github.com/python/typeshed/issues/6893#issuecomment-1012511758
urllib3.disable_warnings()


def create_inventory(
    cvp_inventory: List[Dict[str, Any]], out_dir: str, container: str
) -> None:
    """
    create an inventory file
    """
    inv: Dict[str, Dict[str, Any]] = {AntaInventory.INVENTORY_ROOT_KEY: {"hosts": []}}
    for dev in cvp_inventory:
        inv[AntaInventory.INVENTORY_ROOT_KEY]["hosts"].append(
            {"host": dev["ipAddress"]}
        )
    # write the devices IP address in a file
    out_file = f"{out_dir}/{container}.yml"
    with open(out_file, "w", encoding="utf8") as out_fd:
        out_fd.write(yaml.dump(inv))


def main() -> None:
    """
    Main script routine
    """
    parser = ArgumentParser(
        description="Create devices inventory based on CVP containers"
    )
    parser.add_argument("-cvp", help="CVP address", dest="cvp", required=True)
    parser.add_argument("-u", help="CVP username", dest="username", required=True)
    parser.add_argument("-c", help="CVP container", dest="container", required=False)
    parser.add_argument(
        "-o", help="Output directory", dest="output_directory", required=True
    )
    args = parser.parse_args()
    args.password = getpass(prompt="CVP password: ")

    # use CVP REST API to generate a token
    URL = f"https://{args.cvp}/cvpservice/login/authenticate.do"
    payload = json.dumps({"userId": args.username, "password": args.password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.request(
        "POST", URL, headers=headers, data=payload, verify=False
    )
    token = response.json()["sessionId"]

    # Create output directory
    cwd = os.getcwd()
    out_dir = os.path.dirname(cwd + "/" + args.output_directory + "/")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # CvpClient is a class in the module cvprac.cvp_client
    # clnt is an object, instance of the class CvpClient
    clnt = CvpClient()

    # help(clnt.connect)
    clnt.connect(nodes=[args.cvp], username="", password="", api_token=token)

    if args.container is None:
        # Get a list of all devices
        cvp_inventory = clnt.api.get_inventory()
        create_inventory(cvp_inventory, out_dir, "all")

    else:
        # Get devices under a container
        container = args.container
        container_inventory = clnt.api.get_devices_in_container(container)
        create_inventory(container_inventory, out_dir, container)


if __name__ == "__main__":
    main()
