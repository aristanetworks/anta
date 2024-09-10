# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.get.commands module."""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from sys import stdin
from typing import Any, Callable

import click
import requests
import urllib3
import yaml

from anta.cli.utils import ExitCode
from anta.inventory import AntaInventory
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def inventory_output_options(f: Callable[..., Any]) -> Callable[..., Any]:
    """Click common options required when an inventory is being generated."""

    @click.option(
        "--output",
        "-o",
        required=True,
        envvar="ANTA_INVENTORY",
        show_envvar=True,
        help="Path to save inventory file",
        type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=Path),
    )
    @click.option(
        "--overwrite",
        help="Do not prompt when overriding current inventory",
        default=False,
        is_flag=True,
        show_default=True,
        required=False,
        show_envvar=True,
    )
    @click.pass_context
    @functools.wraps(f)
    def wrapper(
        ctx: click.Context,
        *args: tuple[Any],
        output: Path,
        overwrite: bool,
        **kwargs: dict[str, Any],
    ) -> Any:
        # Boolean to check if the file is empty
        output_is_not_empty = output.exists() and output.stat().st_size != 0
        # Check overwrite when file is not empty
        if not overwrite and output_is_not_empty:
            is_tty = stdin.isatty()
            if is_tty:
                # File has content and it is in an interactive TTY --> Prompt user
                click.confirm(
                    f"Your destination file '{output}' is not empty, continue?",
                    abort=True,
                )
            else:
                # File has content and it is not interactive TTY nor overwrite set to True --> execution stop
                logger.critical("Conversion aborted since destination file is not empty (not running in interactive TTY)")
                ctx.exit(ExitCode.USAGE_ERROR)
        output.parent.mkdir(parents=True, exist_ok=True)
        return f(*args, output=output, **kwargs)

    return wrapper


def get_cv_token(cvp_ip: str, cvp_username: str, cvp_password: str, *, verify_cert: bool) -> str:
    """Generate the authentication token from CloudVision using username and password.

    TODO: need to handle requests error

    Parameters
    ----------
    cvp_ip
        IP address of CloudVision.
    cvp_username
        Username to connect to CloudVision.
    cvp_password
        Password to connect to CloudVision.
    verify_cert
        Enable or disable certificate verification when connecting to CloudVision.

    Returns
    -------
    str
        The token to use in further API calls to CloudVision.

    Raises
    ------
    requests.ssl.SSLError
        If the certificate verification fails.

    """
    # use CVP REST API to generate a token
    url = f"https://{cvp_ip}/cvpservice/login/authenticate.do"
    payload = json.dumps({"userId": cvp_username, "password": cvp_password})
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload, verify=verify_cert, timeout=10)
    return response.json()["sessionId"]


def write_inventory_to_file(hosts: list[AntaInventoryHost], output: Path) -> None:
    """Write a file inventory from pydantic models."""
    i = AntaInventoryInput(hosts=hosts)
    with output.open(mode="w", encoding="UTF-8") as out_fd:
        out_fd.write(yaml.dump({AntaInventory.INVENTORY_ROOT_KEY: yaml.safe_load(i.yaml())}))
    logger.info("ANTA inventory file has been created: '%s'", output)


def create_inventory_from_cvp(inv: list[dict[str, Any]], output: Path) -> None:
    """Create an inventory file from Arista CloudVision inventory."""
    logger.debug("Received %s device(s) from CloudVision", len(inv))
    hosts = []
    for dev in inv:
        logger.info("   * adding entry for %s", dev["hostname"])
        hosts.append(
            AntaInventoryHost(
                name=dev["hostname"],
                host=dev["ipAddress"],
                tags={dev["containerName"].lower()},
            )
        )
    write_inventory_to_file(hosts, output)


def find_ansible_group(data: dict[str, Any], group: str) -> dict[str, Any] | None:
    """Retrieve Ansible group from an input data dict."""
    for k, v in data.items():
        if isinstance(v, dict):
            if k == group and ("children" in v or "hosts" in v):
                return v
            d = find_ansible_group(v, group)
            if d is not None:
                return d
    return None


def deep_yaml_parsing(data: dict[str, Any], hosts: list[AntaInventoryHost] | None = None) -> list[AntaInventoryHost]:
    """Deep parsing of YAML file to extract hosts and associated IPs."""
    if hosts is None:
        hosts = []
    for key, value in data.items():
        if isinstance(value, dict) and "ansible_host" in value:
            logger.info("   * adding entry for %s", key)
            hosts.append(AntaInventoryHost(name=key, host=value["ansible_host"]))
        elif isinstance(value, dict):
            deep_yaml_parsing(value, hosts)
        else:
            return hosts
    return hosts


def create_inventory_from_ansible(inventory: Path, output: Path, ansible_group: str = "all") -> None:
    """Create an ANTA inventory from an Ansible inventory YAML file.

    Parameters
    ----------
    inventory
        Ansible Inventory file to read.
    output
        ANTA inventory file to generate.
    ansible_group
        Ansible group from where to extract data.

    """
    try:
        with inventory.open(encoding="utf-8") as inv:
            ansible_inventory = yaml.safe_load(inv)
    except yaml.constructor.ConstructorError as exc:
        if exc.problem and "!vault" in exc.problem:
            logger.error(
                "`anta get from-ansible` does not support inline vaulted variables, comment them out to generate your inventory. "
                "If the vaulted variable is necessary to build the inventory (e.g. `ansible_host`), it needs to be unvaulted for "
                "`from-ansible` command to work."
            )
        msg = f"Could not parse {inventory}."
        raise ValueError(msg) from exc
    except OSError as exc:
        msg = f"Could not parse {inventory}."
        raise ValueError(msg) from exc

    if not ansible_inventory:
        msg = f"Ansible inventory {inventory} is empty"
        raise ValueError(msg)

    ansible_inventory = find_ansible_group(ansible_inventory, ansible_group)

    if ansible_inventory is None:
        msg = f"Group {ansible_group} not found in Ansible inventory"
        raise ValueError(msg)
    ansible_hosts = deep_yaml_parsing(ansible_inventory)
    write_inventory_to_file(ansible_hosts, output)
