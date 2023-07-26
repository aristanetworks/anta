#!/usr/bin/env python
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.get.commands module.
"""

import json
import logging
from typing import Any, Dict, List, Union

import requests
import urllib3
import yaml

from ...inventory import AntaInventory

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def get_cv_token(cvp_ip: str, cvp_username: str, cvp_password: str) -> str:
    """Generate AUTH token from CVP using password"""

    # use CVP REST API to generate a token
    URL = f"https://{cvp_ip}/cvpservice/login/authenticate.do"
    payload = json.dumps({"userId": cvp_username, "password": cvp_password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.request("POST", URL, headers=headers, data=payload, verify=False, timeout=10)
    return response.json()["sessionId"]


def create_inventory_from_cvp(inv: List[Dict[str, Any]], directory: str, container: str) -> None:
    """
    create an inventory file from Arista CloudVision
    """
    i: Dict[str, Dict[str, Any]] = {AntaInventory.INVENTORY_ROOT_KEY: {"hosts": []}}
    logger.debug(f"Received {len(inv)} device(s) from CVP")
    for dev in inv:
        logger.info(f'   * adding entry for {dev["hostname"]}')
        i[AntaInventory.INVENTORY_ROOT_KEY]["hosts"].append({"host": dev["ipAddress"], "name": dev["hostname"], "tags": [dev["containerName"].lower()]})
    # write the devices IP address in a file
    inv_file = "inventory" if container is None else f"inventory-{container}"
    out_file = f"{directory}/{inv_file}.yml"
    with open(out_file, "w", encoding="UTF-8") as out_fd:
        out_fd.write(yaml.dump(i))
    logger.info(f"Inventory file has been created in {out_file}")


def create_inventory_from_ansible(inventory: str, directory: str, ansible_root: str = None, output_file: str = 'inventory.yml') -> None:
    def deep_yaml_parsing(data: Dict[str, Any], hosts: Union[None, List[Dict[str, str]]] = None) -> Union[None, List[Dict[str, str]]]:
        """Deep parsing of YAML file to extract hosts and associated IPs"""
        if hosts is None:
            hosts = []
        for key, value in data.items():
            if isinstance(value, dict) and "ansible_host" in value.keys():
                hosts.append({"name": key, "host": value["ansible_host"]})
            elif isinstance(value, dict):
                deep_yaml_parsing(value, hosts)
            else:
                # print(f"Key: {key}\n  Value: {value}")
                return hosts
        return hosts

    i: Dict[str, Dict[str, Any]] = {AntaInventory.INVENTORY_ROOT_KEY: {"hosts": []}}
    ansible_inventory = yaml.safe_load(open(inventory))
    if ansible_root not in ansible_inventory.keys():
        logger.error(f"Group {ansible_root} not in ansible inventory {inventory}")
        raise (f"Group {ansible_root} not in ansible inventory {inventory}")
    if ansible_root is None:
        ansible_hosts = deep_yaml_parsing(ansible_inventory, hosts=[])
    else:
        ansible_hosts = deep_yaml_parsing(ansible_inventory[ansible_root], hosts=[])
    for dev in ansible_hosts:
        logger.info(f'   * adding entry for {dev["name"]}')
        print(f"   * adding entry for {dev}")
        i[AntaInventory.INVENTORY_ROOT_KEY]["hosts"].append({"host": dev["host"], "name": dev["name"]})
    out_file = f"{directory}/{output_file}.yml"
    with open(out_file, "w", encoding="UTF-8") as out_fd:
        out_fd.write(yaml.dump(i))
    logger.info(f"Inventory file has been created in {out_file}")
