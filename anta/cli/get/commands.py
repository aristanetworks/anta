#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable = redefined-outer-name

"""
Commands for Anta CLI to run check commands.
"""

import asyncio
import json
import logging
import os
from typing import List, Optional

import click
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
from rich.pretty import pretty_repr

from anta.cli.console import console
from anta.cli.utils import parse_tags
from anta.models import DEFAULT_TAG

from .utils import create_inventory, get_cv_token

logger = logging.getLogger(__name__)


@click.command(no_args_is_help=True)
@click.option("--cvp-ip", "-ip", default=None, help="CVP IP Address", type=str, required=True)
@click.option("--cvp-username", "-u", default=None, help="CVP Username", type=str, required=True)
@click.option("--cvp-password", "-p", default=None, help="CVP Password / token", type=str, required=True)
@click.option("--cvp-container", "-c", default=None, help="Container where devices are configured", type=str, required=False)
@click.option("--inventory-directory", "-d", default=None, help="Path to save inventory file", type=click.Path())
def from_cvp(inventory_directory: str, cvp_ip: str, cvp_username: str, cvp_password: str, cvp_container: str) -> None:
    """Build ANTA inventory from Cloudvision"""
    # pylint: disable=too-many-arguments
    logger.info(f"Getting auth token from {cvp_ip} for user {cvp_username}")
    token = get_cv_token(cvp_ip=cvp_ip, cvp_username=cvp_username, cvp_password=cvp_password)

    # Create output directory
    cwd = os.getcwd()
    out_dir = os.path.dirname(f"{cwd}/{inventory_directory}/")
    if not os.path.exists(out_dir):
        logger.info(f"Creating inventory folder {out_dir}")
        os.makedirs(out_dir)

    clnt = CvpClient()
    try:
        clnt.connect(nodes=[cvp_ip], username="", password="", api_token=token)
    except CvpApiError as error:
        logger.error(f"Error connecting to cvp: {error}")
    logger.info(f"Connected to CVP {cvp_ip}")

    cvp_inventory = None
    if cvp_container is None:
        # Get a list of all devices
        logger.info(f"Getting full inventory from {cvp_ip}")
        cvp_inventory = clnt.api.get_inventory()
    else:
        # Get devices under a container
        logger.info(f"Getting inventory for container {cvp_container} from {cvp_ip}")
        cvp_inventory = clnt.api.get_devices_in_container(cvp_container)
    create_inventory(cvp_inventory, out_dir, cvp_container)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
@click.option("--connected/--not-connected", help="Display inventory after connection has been created", default=False, required=False)
def inventory(ctx: click.Context, tags: Optional[List[str]], connected: bool) -> None:
    """Show inventory loaded in ANTA."""

    logger.debug(f"Requesting devices for tags: {tags}")
    console.print("Current inventory content is:", style="white on blue")

    if connected:
        asyncio.run(ctx.obj["inventory"].connect_inventory())

    inventory_result = ctx.obj["inventory"].get_inventory(tags=tags)
    console.print(pretty_repr(inventory_result))


@click.command()
@click.pass_context
def tags(ctx: click.Context) -> None:
    """Get list of configured tags in user inventory."""
    tags_found = []
    for device in ctx.obj["inventory"]:
        tags_found += device.tags
    tags_found = sorted(set(tags_found))
    console.print("Tags found:")
    console.print_json(json.dumps(tags_found, indent=2))
    console.print(f"\n* note that tag [green]{DEFAULT_TAG}[/green] has been added by anta")
