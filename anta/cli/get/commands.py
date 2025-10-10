# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable = redefined-outer-name
"""Click commands to get information from or generate inventories."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import click
import requests
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
from rich.pretty import pretty_repr

from anta.cli.console import console
from anta.cli.get.utils import inventory_output_options
from anta.cli.utils import ExitCode, catalog_options, inventory_options

from .utils import (
    _explore_package,
    _filter_tests_via_catalog,
    _get_unique_commands,
    _print_commands,
    create_inventory_from_ansible,
    create_inventory_from_cvp,
    get_cv_token,
    print_tests,
)

if TYPE_CHECKING:
    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


@click.command
@inventory_output_options
@click.option("--host", "-host", help="CloudVision instance FQDN or IP", type=str, required=True)
@click.option("--username", "-u", help="CloudVision username", type=str, required=True)
@click.option("--password", "-p", help="CloudVision password", type=str, required=True)
@click.option("--container", "-c", help="CloudVision container where devices are configured", type=str)
@click.option(
    "--ignore-cert",
    help="Ignore verifying the SSL certificate when connecting to CloudVision",
    show_envvar=True,
    is_flag=True,
    default=False,
)
@click.pass_context
def from_cvp(ctx: click.Context, output: Path, host: str, username: str, password: str, container: str | None, *, ignore_cert: bool) -> None:
    """Build ANTA inventory from CloudVision.

    NOTE: Only username/password authentication is supported for on-premises CloudVision instances.
    Token authentication for both on-premises and CloudVision as a Service (CVaaS) is not supported.
    """
    # TODO: - Handle get_cv_token, get_inventory and get_devices_in_container failures.
    logger.info("Getting authentication token for user '%s' from CloudVision instance '%s'", username, host)
    try:
        token = get_cv_token(cvp_ip=host, cvp_username=username, cvp_password=password, verify_cert=not ignore_cert)
    except requests.exceptions.SSLError as error:
        logger.error("Authentication to CloudVison failed: %s.", error)
        ctx.exit(ExitCode.USAGE_ERROR)

    clnt = CvpClient()
    try:
        clnt.connect(nodes=[host], username="", password="", api_token=token)
    except CvpApiError as error:
        logger.error("Error connecting to CloudVision: %s", error)
        ctx.exit(ExitCode.USAGE_ERROR)
    logger.info("Connected to CloudVision instance '%s'", host)

    cvp_inventory = None
    if container is None:
        # Get a list of all devices
        logger.info("Getting full inventory from CloudVision instance '%s'", host)
        cvp_inventory = clnt.api.get_inventory()
    else:
        # Get devices under a container
        logger.info("Getting inventory for container %s from CloudVision instance '%s'", container, host)
        cvp_inventory = clnt.api.get_devices_in_container(container)
    try:
        create_inventory_from_cvp(cvp_inventory, output)
    except OSError as e:
        logger.error(str(e))
        ctx.exit(ExitCode.USAGE_ERROR)


@click.command
@inventory_output_options
@click.option("--ansible-group", "-g", help="Ansible group to filter", type=str, default="all")
@click.option(
    "--ansible-inventory",
    help="Path to your ansible inventory file to read",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
    required=True,
)
@click.pass_context
def from_ansible(ctx: click.Context, output: Path, ansible_group: str, ansible_inventory: Path) -> None:
    """Build ANTA inventory from an ansible inventory YAML file.

    NOTE: This command does not support inline vaulted variables. Make sure to comment them out.

    """
    logger.info("Building inventory from ansible file '%s'", ansible_inventory)
    try:
        create_inventory_from_ansible(
            inventory=ansible_inventory,
            output=output,
            ansible_group=ansible_group,
        )
    except (ValueError, OSError) as e:
        logger.error(str(e))
        ctx.exit(ExitCode.USAGE_ERROR)


@click.command
@inventory_options
@click.option("--connected/--not-connected", help="Display inventory after connection has been created", default=False, required=False)
def inventory(inventory: AntaInventory, tags: set[str] | None, *, connected: bool) -> None:
    """Show inventory loaded in ANTA."""
    logger.debug("Requesting devices for tags: %s", tags)
    console.print("Current inventory content is:", style="white on blue")

    if connected:
        asyncio.run(inventory.connect_inventory())

    inventory_result = inventory.get_inventory(tags=tags)
    console.print(pretty_repr(inventory_result))


@click.command
@inventory_options
def tags(inventory: AntaInventory, **_kwargs: Any) -> None:  # noqa: ANN401
    """Get list of configured tags in user inventory."""
    tags: set[str] = set()
    for device in inventory.values():
        tags.update(device.tags)
    console.print("Tags defined in inventory:")
    console.print_json(data=sorted(tags), indent=2)


@click.command
@click.option("--module", help="Filter tests by module name.", default="anta.tests", show_default=True)
@click.option("--test", help="Filter by specific test name. If module is specified, searches only within that module.", type=str)
@click.option("--short", help="Display test names without their inputs.", is_flag=True, default=False)
@click.option("--count", help="Print only the number of tests found.", is_flag=True, default=False)
@click.pass_context
def tests(ctx: click.Context, module: str, test: str | None, *, short: bool, count: bool) -> None:
    """Show all builtin ANTA tests with an example output retrieved from each test documentation."""
    try:
        tests_found = _explore_package(module, test_name=test, short=short, count=count)
        if len(tests_found) == 0:
            console.print(f"""No test {f"'{test}' " if test else ""}found in '{module}'.""")
        elif count:
            if len(tests_found) == 1:
                console.print(f"There is 1 test available in '{module}'.")
            else:
                console.print(f"There are {len(tests_found)} tests available in '{module}'.")
        else:
            print_tests(tests_found, short=short)
    except ValueError as e:
        logger.error(str(e))
        ctx.exit(ExitCode.USAGE_ERROR)


@click.command
@click.option("--module", help="Filter commands by module name.", default="anta.tests", show_default=True)
@click.option("--test", help="Filter by specific test name. If module is specified, searches only within that module.", type=str)
@catalog_options(required=False)
@click.option("--unique", help="Print only the unique commands.", is_flag=True, default=False)
@click.pass_context
def commands(
    ctx: click.Context,
    module: str,
    test: str | None,
    catalog: AntaCatalog,
    catalog_format: Literal["yaml", "json"] = "yaml",  # noqa: ARG001
    *,
    unique: bool,
) -> None:
    """Print all EOS commands used by the selected ANTA tests.

    It can be filtered by module, test or using a catalog.
    If no filter is given, all built-in ANTA tests commands are retrieved.
    """
    # TODO: implement catalog format
    try:
        tests_found = _explore_package(module, test_name=test)
        if catalog:
            tests_found = _filter_tests_via_catalog(tests_found, catalog)
        if len(tests_found) == 0:
            console.print(f"""No test {f"'{test}' " if test else ""}found in '{module}'{f" for catalog '{catalog.filename}'" if catalog else ""}.""")
        if unique:
            for command in _get_unique_commands(tests_found):
                console.print(command)
        else:
            _print_commands(tests_found)
    except ValueError as e:
        logger.error(str(e))
        ctx.exit(ExitCode.USAGE_ERROR)
