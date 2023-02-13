#!/usr/bin/env python3

"""
This script:
- uses CVP REST API to generate a token
- uses cvprac with this token to get the device inventory
- creates a YAML file with the devices IP address under the container passed in argument
- if we dont provide the argument `c` it creates a YAML file with all the devices IP address from the CVP inventory.

usage: ./create-devices-inventory-from-cvp.py --help
requirement: pip install cvprac==1.2.0
"""

import json
import logging
import os
from argparse import ArgumentParser
from getpass import getpass
from typing import Any, Dict, List

import requests
import yaml
from cvprac.cvp_client import CvpClient
from rich.logging import RichHandler

from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


def setup_logging(level: str = "info") -> None:
    """
    Configure logging for check-devices execution

    Helpers to set logging for
    * anta.inventory
    * anta.result_manager
    * check-devices

    Args:
        level (str, optional): level name to configure. Defaults to 'critical'.
    """
    loglevel = getattr(logging, level.upper())

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=loglevel, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    logger.setLevel(loglevel)


def create_inventory(inv: List[Dict[str, Any]], directory: str, container: str) -> None:
    """
    create an inventory file
    """
    i: Dict[str, Dict[str, Any]] = {AntaInventory.INVENTORY_ROOT_KEY: {"hosts": []}}
    for dev in inv:
        i[AntaInventory.INVENTORY_ROOT_KEY]["hosts"].append({"host": dev["ipAddress"]})
    # write the devices IP address in a file
    out_file = f"{directory}/{container}.yml"
    with open(out_file, "w", encoding="utf8") as out_fd:
        out_fd.write(yaml.dump(i))


def main() -> None:
    """main"""
    parser = ArgumentParser(
        description="Create devices inventory based on CVP containers"
    )
    parser.add_argument("-cvp", help="CVP address", dest="cvp", required=True)
    parser.add_argument("-u", help="CVP username", dest="username", required=True)
    parser.add_argument("-c", help="CVP container", dest="container", required=False)
    parser.add_argument(
        "-o", help="Output directory", dest="output_directory", required=True
    )
    parser.add_argument(
        "-log",
        "--loglevel",
        default="info",
        help="Provide logging level. Example --loglevel debug, default=info",
    )
    args = parser.parse_args()
    args.password = getpass(prompt="CVP password: ")
    setup_logging(level=args.loglevel)

    # use CVP REST API to generate a token
    URL = f"https://{args.cvp}/cvpservice/login/authenticate.do"
    payload = json.dumps({"userId": args.username, "password": args.password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.request(
        "POST", URL, headers=headers, data=payload, verify=False, timeout=10
    )
    token = response.json()["sessionId"]

    # Create output directory
    cwd = os.getcwd()
    out_dir = os.path.dirname(f"{cwd}/{args.output_directory}/")
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
        container_inventory = clnt.api.get_devices_in_container(args.container)
        create_inventory(container_inventory, out_dir, args.container)


if __name__ == "__main__":
    main()
