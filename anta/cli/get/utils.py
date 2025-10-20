# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.get.commands module."""

from __future__ import annotations

import functools
import importlib
import inspect
import json
import logging
import pkgutil
import re
import sys
import textwrap
from importlib import util as importlib_util
from itertools import groupby
from pathlib import Path
from sys import stdin
from typing import TYPE_CHECKING, Any, TypeVar

import click
import requests
import urllib3
import yaml
from typing_extensions import deprecated

from anta.cli.console import console
from anta.cli.utils import ExitCode
from anta.inventory import AntaInventory
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput
from anta.models import AntaCommand, AntaTest

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta.catalog import AntaCatalog

R = TypeVar("R")

logger = logging.getLogger(__name__)


def inventory_output_options(f: Callable[..., R]) -> Callable[..., R]:
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
        *,
        output: Path,
        overwrite: bool,
        **kwargs: Any,  # noqa: ANN401
    ) -> R:
        # Boolean to check if the file is empty
        output_is_not_empty = output.exists() and output.stat().st_size != 0
        # Check overwrite when file is not empty
        if not overwrite and output_is_not_empty:
            is_tty = stdin.isatty()
            if is_tty:
                # File has content and it is in an interactive TTY --> Prompt user
                _ = click.confirm(
                    f"Your destination file '{output}' is not empty, continue?",
                    abort=True,
                )
            else:
                # File has content and it is not interactive TTY nor overwrite set to True --> execution stop
                logger.critical("Conversion aborted since destination file is not empty (not running in interactive TTY)")
                ctx.exit(ExitCode.USAGE_ERROR)
        output.parent.mkdir(parents=True, exist_ok=True)
        return f(output=output, **kwargs)

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
            _ = out_fd.write(yaml.dump({AntaInventory.INVENTORY_ROOT_KEY: yaml.safe_load(i.yaml())}))
        logger.info("ANTA inventory file has been created: '%s'", output)
    except OSError as exc:
        msg = f"Could not write inventory to path '{output}'."
        raise OSError(msg) from exc


def create_inventory_from_cvp(inv: list[dict[str, Any]], output: Path) -> None:
    """Create an inventory file from Arista CloudVision inventory."""
    logger.debug("Received %s device(s) from CloudVision", len(inv))
    hosts: list[AntaInventoryHost] = []
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
            ansible_inventory: dict[str, Any] = yaml.safe_load(inv)
    except yaml.constructor.ConstructorError as exc:
        if exc.problem and "!vault" in exc.problem:
            msg = (
                "`anta get from-ansible` does not support inline vaulted variables, comment them out to generate your inventory. "
                "If the vaulted variable is necessary to build the inventory (e.g. `ansible_host`), it needs to be unvaulted for "
                "`from-ansible` command to work."
            )
            logger.error(msg)
        msg = f"Could not parse {inventory}."
        raise ValueError(msg) from exc
    except OSError as exc:
        msg = f"Could not parse {inventory}."
        raise ValueError(msg) from exc

    if not ansible_inventory:
        msg = f"Ansible inventory {inventory} is empty"
        raise ValueError(msg)

    filtered_ansible_inventory = find_ansible_group(ansible_inventory, ansible_group)

    if filtered_ansible_inventory is None:
        msg = f"Group {ansible_group} not found in Ansible inventory"
        raise ValueError(msg)
    ansible_hosts = deep_yaml_parsing(filtered_ansible_inventory)
    write_inventory_to_file(ansible_hosts, output)


def _explore_package(module_name: str, test_name: str | None = None, *, short: bool = False, count: bool = False) -> list[type[AntaTest]]:
    """Parse ANTA test submodules recursively and return a list of the found AntaTest.

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
    list[type[AntaTest]]:
        A list of the AntaTest found.
    """
    result: list[type[AntaTest]] = []
    try:
        module_spec = importlib_util.find_spec(module_name)
    except ModuleNotFoundError:
        # Relying on module_spec check below.
        module_spec = None
    except ImportError as e:
        msg = "`--module <module>` option does not support relative imports"
        raise ValueError(msg) from e

    # Giving a second chance adding CWD to PYTHONPATH
    if module_spec is None:
        try:
            logger.info("Could not find module `%s`, injecting CWD in PYTHONPATH and retrying...", module_name)
            sys.path = [str(Path.cwd()), *sys.path]
            module_spec = importlib_util.find_spec(module_name)
        except ImportError:
            module_spec = None

    if module_spec is None or module_spec.origin is None:
        msg = f"Module `{module_name}` was not found!"
        raise ValueError(msg)

    if module_spec.submodule_search_locations:
        for _, sub_module_name, ispkg in pkgutil.walk_packages(module_spec.submodule_search_locations):
            qname = f"{module_name}.{sub_module_name}"
            if ispkg:
                result.extend(_explore_package(qname, test_name=test_name, short=short, count=count))
                continue
            result.extend(find_tests_in_module(qname, test_name))

    else:
        result.extend(find_tests_in_module(module_spec.name, test_name))

    return result


def find_tests_in_module(qname: str, test_name: str | None) -> list[type[AntaTest]]:
    """Return the list of AntaTest in the passed module qname, potentially filtering on test_name.

    Parameters
    ----------
    qname
        Name of the module to explore (e.g., 'anta.tests.routing.bgp').
    test_name
        If provided, only show tests starting with this name.

    Returns
    -------
    list[type[AntaTest]]:
        A list of the AntaTest found in the module.
    """
    results: list[type[AntaTest]] = []
    try:
        qname_module = importlib.import_module(qname)
    except (AssertionError, ImportError) as e:
        msg = f"Error when importing `{qname}` using importlib!"
        raise ValueError(msg) from e

    for _name, obj in inspect.getmembers(qname_module):
        # Only retrieves the subclasses of AntaTest
        if not inspect.isclass(obj) or not issubclass(obj, AntaTest) or obj == AntaTest:
            continue
        if test_name and not obj.name.startswith(test_name):
            continue
        results.append(obj)

    return results


def _filter_tests_via_catalog(tests: list[type[AntaTest]], catalog: AntaCatalog) -> list[type[AntaTest]]:
    """Return the filtered list of tests present in the catalog.

    Parameters
    ----------
    tests:
        List of tests.
    catalog:
        The AntaCatalog to use as filtering.

    Returns
    -------
    list[type[AntaTest]]:
        The filtered list of tests containing uniquely the tests found in the catalog.
    """
    catalog_test_names = {test.test.name for test in catalog.tests}
    return [test for test in tests if test.name in catalog_test_names]


def print_tests(tests: list[type[AntaTest]], *, short: bool = False) -> None:
    """Print a list of AntaTest.

    Parameters
    ----------
    tests
        A list of AntaTest subclasses.
    short
        If True, only print test names without their inputs.
    """

    def module_name(test: type[AntaTest]) -> str:
        """Return the module name for the input test.

        Used to group the test by module.
        """
        return test.__module__

    for module, module_tests in groupby(tests, module_name):
        console.print(f"{module}:")
        for test in module_tests:
            print_test(test, short=short)


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
    test_name_lines = [i for i, input_entry in enumerate(inputs) if test.name in input_entry]
    if not test_name_lines:
        msg = f"Could not find the name of the test '{test.name}' in the Example section in the docstring."
        raise ValueError(msg)
    for list_index, line_index in enumerate(test_name_lines):
        end = test_name_lines[list_index + 1] if list_index + 1 < len(test_name_lines) else -1
        console.print(f"  {inputs[line_index].strip()}")
        # Injecting the description for the first example
        if list_index == 0:
            console.print(f"      # {test.description}", soft_wrap=True)
        if not short and len(inputs) > line_index + 2:  # There are params
            console.print(textwrap.indent(textwrap.dedent("\n".join(inputs[line_index + 1 : end])), " " * 6))


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


def _print_commands(tests: list[type[AntaTest]]) -> None:
    """Print a list of commands per module and per test.

    Parameters
    ----------
    tests
        A list of AntaTest subclasses.
    """

    def module_name(test: type[AntaTest]) -> str:
        """Return the module name for the input test.

        Used to group the test by module.
        """
        return test.__module__

    for module, module_tests in groupby(tests, module_name):
        console.print(f"{module}:")
        for test in module_tests:
            console.print(f"  - {test.name}:")
            for command in test.commands:
                if isinstance(command, AntaCommand):
                    console.print(f"    - {command.command}")
                else:  # isinstance(command, AntaTemplate):
                    console.print(f"    - {command.template}")


def _get_unique_commands(tests: list[type[AntaTest]]) -> set[str]:
    """Return a set of unique commands used by the tests.

    Parameters
    ----------
    tests
        A list of AntaTest subclasses.

    Returns
    -------
    set[str]
        A set of commands or templates used by each test.
    """
    result: set[str] = set()

    for test in tests:
        for command in test.commands:
            if isinstance(command, AntaCommand):
                result.add(command.command)
            else:  # isinstance(command, AntaTemplate):
                result.add(command.template)

    return result


@deprecated("This function is deprecated, use `_explore_package`. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
def explore_package(module_name: str, test_name: str | None = None, *, short: bool = False, count: bool = False) -> int:  # pragma: no cover
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
        module_spec = importlib_util.find_spec(module_name)
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
            module_spec = importlib_util.find_spec(module_name)
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


@deprecated("This function is deprecated, use `find_tests_in_module`. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
def find_tests_examples(qname: str, test_name: str | None, *, short: bool = False, count: bool = False) -> int:  # pragma: no cover
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
