# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.get.commands module."""

from __future__ import annotations

import functools
import importlib
import inspect
import ipaddress
import json
import logging
import pkgutil
import re
import sys
import textwrap
from pathlib import Path
from sys import stdin
from typing import Any, Callable

import click
import requests
import urllib3
import yaml

from anta.cli.console import console
from anta.cli.utils import ExitCode
from anta.inventory import AntaInventory
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput
from anta.models import AntaTest

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
    """Write a file inventory from pydantic models.

    Parameters
    ----------
    hosts:
        the list of AntaInventoryHost to write to an inventory file
    output:
        the Path where the inventory should be written.

    Raises
    ------
    OSError
        When anything goes wrong while writing the file.
    """
    i = AntaInventoryInput(hosts=hosts)
    try:
        with output.open(mode="w", encoding="UTF-8") as out_fd:
            out_fd.write(yaml.dump({AntaInventory.INVENTORY_ROOT_KEY: yaml.safe_load(i.yaml())}))
        logger.info("ANTA inventory file has been created: '%s'", output)
    except OSError as exc:
        msg = f"Could not write inventory to path '{output}'."
        raise OSError(msg) from exc


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


def create_inventory_from_netbox(nb_instance: str, output: Path, token: str, platform: str = "Arista EOS", site: str | None = None, verify: bool = False) -> None:
    """Fetch devices from NetBox filtered by a specific platform.

    Parameters
    ----------
    nb_instance
        The NetBox API instance.
    output
        ANTA inventory file to generate.
    token
        The token used to authenticate to the NetBox instance.
    platform
        The platform to filter devices by.
    site
        The site to filter devices by.
    verify
        Verify the SSL certification of the NetBox instance.

    """
    session = requests.session()
    session.verify = verify
    try:
        import pynetbox
    except ImportError as e:
        logging.error(e)

    try:
        # Initialize NetBox API
        nb = pynetbox.api(nb_instance, token=token)

        # Platform name to filter
        platform = nb.dcim.platforms.get(q=[platform])

        devices = nb.dcim.devices.filter(platform=platform.slug, site=site) if site else nb.dcim.devices.filter(platform=platform.slug)

        inventory = []
        for device in devices:
            host_entry = {
                "host": str(ipaddress.ip_interface(device.primary_ip).ip),
                "name": device.name,
                "tags": [tag.name for tag in device.tags],
            }
            inventory.append(host_entry)

        write_inventory_to_file(inventory, output)

    except Exception as e:
        raise ValueError(e) from e


def explore_package(module_name: str, test_name: str | None = None, *, short: bool = False, count: bool = False) -> int:
    """Parse ANTA test submodules recursively and print AntaTest examples.

    Parameters
    ----------
    module_name
        Name of the module to explore (e.g., 'anta.tests.routing.bgp').
    test_name
        If provided, only show tests starting with this name.
    short
        If True, only print test names without their inputs.
    count
        If True, only count the tests.

    Returns
    -------
    int:
        The number of tests found.
    """
    try:
        module_spec = importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        # Relying on module_spec check below.
        module_spec = None
    except ImportError as e:
        msg = "`anta get tests --module <module>` does not support relative imports"
        raise ValueError(msg) from e

    # Giving a second chance adding CWD to PYTHONPATH
    if module_spec is None:
        try:
            logger.info("Could not find module `%s`, injecting CWD in PYTHONPATH and retrying...", module_name)
            sys.path = [str(Path.cwd()), *sys.path]
            module_spec = importlib.util.find_spec(module_name)
        except ImportError:
            module_spec = None

    if module_spec is None or module_spec.origin is None:
        msg = f"Module `{module_name}` was not found!"
        raise ValueError(msg)

    tests_found = 0
    if module_spec.submodule_search_locations:
        for _, sub_module_name, ispkg in pkgutil.walk_packages(module_spec.submodule_search_locations):
            qname = f"{module_name}.{sub_module_name}"
            if ispkg:
                tests_found += explore_package(qname, test_name=test_name, short=short, count=count)
                continue
            tests_found += find_tests_examples(qname, test_name, short=short, count=count)

    else:
        tests_found += find_tests_examples(module_spec.name, test_name, short=short, count=count)

    return tests_found


def find_tests_examples(qname: str, test_name: str | None, *, short: bool = False, count: bool = False) -> int:
    """Print tests from `qname`, filtered by `test_name` if provided.

    Parameters
    ----------
    qname
        Name of the module to explore (e.g., 'anta.tests.routing.bgp').
    test_name
        If provided, only show tests starting with this name.
    short
        If True, only print test names without their inputs.
    count
        If True, only count the tests.

    Returns
    -------
    int:
        The number of tests found.
    """
    try:
        qname_module = importlib.import_module(qname)
    except (AssertionError, ImportError) as e:
        msg = f"Error when importing `{qname}` using importlib!"
        raise ValueError(msg) from e

    module_printed = False
    tests_found = 0

    for _name, obj in inspect.getmembers(qname_module):
        # Only retrieves the subclasses of AntaTest
        if not inspect.isclass(obj) or not issubclass(obj, AntaTest) or obj == AntaTest:
            continue
        if test_name and not obj.name.startswith(test_name):
            continue
        if not module_printed:
            if not count:
                console.print(f"{qname}:")
            module_printed = True
        tests_found += 1
        if count:
            continue
        print_test(obj, short=short)

    return tests_found


def print_test(test: type[AntaTest], *, short: bool = False) -> None:
    """Print a single test.

    Parameters
    ----------
    test
        the representation of the AntaTest as returned by inspect.getmembers
    short
        If True, only print test names without their inputs.
    """
    if not test.__doc__ or (example := extract_examples(test.__doc__)) is None:
        msg = f"Test {test.name} in module {test.__module__} is missing an Example"
        raise LookupError(msg)
    # Picking up only the inputs in the examples
    # Need to handle the fact that we nest the routing modules in Examples.
    # This is a bit fragile.
    inputs = example.split("\n")
    try:
        test_name_line = next((i for i, input_entry in enumerate(inputs) if test.name in input_entry))
    except StopIteration as e:
        msg = f"Could not find the name of the test '{test.name}' in the Example section in the docstring."
        raise ValueError(msg) from e
    # TODO: handle not found
    console.print(f"  {inputs[test_name_line].strip()}")
    # Injecting the description
    console.print(f"      # {test.description}", soft_wrap=True)
    if not short and len(inputs) > test_name_line + 2:  # There are params
        console.print(textwrap.indent(textwrap.dedent("\n".join(inputs[test_name_line + 1 : -1])), " " * 6))


def extract_examples(docstring: str) -> str | None:
    """Extract the content of the Example section in a Numpy docstring.

    Returns
    -------
    str | None
        The content of the section if present, None if the section is absent or empty.
    """
    pattern = r"Examples\s*--------\s*(.*)(?:\n\s*\n|\Z)"
    match = re.search(pattern, docstring, flags=re.DOTALL)
    return match[1].strip() if match and match[1].strip() != "" else None
