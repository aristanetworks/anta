# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Utils functions to use with anta.cli.get.commands module.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests
import urllib3
import yaml

from anta.inventory import AntaInventory
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def get_cv_token(cvp_ip: str, cvp_username: str, cvp_password: str) -> str:
    """Generate AUTH token from CVP using password"""
    # TODO, need to handle requests eror

    # use CVP REST API to generate a token
    URL = f"https://{cvp_ip}/cvpservice/login/authenticate.do"
    payload = json.dumps({"userId": cvp_username, "password": cvp_password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.request("POST", URL, headers=headers, data=payload, verify=False, timeout=10)
    return response.json()["sessionId"]


def create_inventory_from_cvp(inv: list[dict[str, Any]], directory: str, container: str | None = None) -> None:
    """
    create an inventory file from Arista CloudVision
    """
    i: dict[str, dict[str, Any]] = {AntaInventory.INVENTORY_ROOT_KEY: {"hosts": []}}
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


def create_inventory_from_ansible(inventory: Path, output_file: Path, ansible_group: str = "all") -> None:
    """
    Create an ANTA inventory from an Ansible inventory YAML file

    Args:
        inventory: Ansible Inventory file to read
        output_file: ANTA inventory file to generate.
        ansible_root: Ansible group from where to extract data.
    """

    def find_ansible_group(data: dict[str, Any], group: str) -> dict[str, Any] | None:
        for k, v in data.items():
            if isinstance(v, dict):
                if k == group and ("children" in v.keys() or "hosts" in v.keys()):
                    return v
                d = find_ansible_group(v, group)
                if d is not None:
                    return d
        return None

    def deep_yaml_parsing(data: dict[str, Any], hosts: list[AntaInventoryHost] | None = None) -> list[AntaInventoryHost]:
        """Deep parsing of YAML file to extract hosts and associated IPs"""
        if hosts is None:
            hosts = []
        for key, value in data.items():
            if isinstance(value, dict) and "ansible_host" in value.keys():
                logger.info(f"   * adding entry for {key}")
                hosts.append(AntaInventoryHost(name=key, host=value["ansible_host"]))
            elif isinstance(value, dict):
                deep_yaml_parsing(value, hosts)
            else:
                return hosts
        return hosts

    try:
        with open(inventory, encoding="utf-8") as inv:
            ansible_inventory = yaml.safe_load(inv)
    except OSError as exc:
        raise ValueError(f"Could not parse {inventory}.") from exc

    if not ansible_inventory:
        raise ValueError(f"Ansible inventory {inventory} is empty")

    ansible_inventory = find_ansible_group(ansible_inventory, ansible_group)

    if ansible_inventory is None:
        raise ValueError(f"Group {ansible_group} not found in Ansible inventory")
    ansible_hosts = deep_yaml_parsing(ansible_inventory)
    i = AntaInventoryInput(hosts=ansible_hosts)
    # TODO, catch issue
    with open(output_file, "w", encoding="UTF-8") as out_fd:
        out_fd.write(yaml.dump({AntaInventory.INVENTORY_ROOT_KEY: i.model_dump(exclude_unset=True)}))
    logger.info(f"ANTA device inventory file has been created in {output_file}")
