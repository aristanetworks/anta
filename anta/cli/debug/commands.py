#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable = redefined-outer-name

"""
Commands for Anta CLI to run debug commands.
"""

import asyncio
import logging
from typing import List, Literal, Union

import click
from click import Option

from anta.cli.console import console
from anta.cli.utils import EapiVersion
from anta.device import AntaDevice
from anta.models import AntaTestCommand, AntaTemplate

logger = logging.getLogger(__name__)


def get_device(ctx: click.Context, param: Option, value: str) -> List[str]:
    # pylint: disable=unused-argument
    """
    Click option callback to get an AntaDevice instance from a string
    """
    if value is not None:
        # TODO - @mtache write public method to get a device from its name
        return [dev for dev in ctx.obj["inventory"] if dev.name == value][0]
    return None


@click.command()
@click.option("--command", "-c", type=str, required=True, help="Command to run")
@click.option("--ofmt", type=click.Choice(["text", "json"]), default="json", help="EOS eAPI format to use. can be text or json")
@click.option("--api-version", "--version", type=EapiVersion(), default="latest", help="EOS eAPI version to use")
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use", callback=get_device)
def run_cmd(command: str, ofmt: str, api_version: Union[int, Literal["latest"]], device: AntaDevice) -> None:
    """Run arbitrary command to an ANTA device"""
    console.print(f"Run command [green]{command}[/green] on [red]{device.name}[/red]")
    c = AntaTestCommand(command=command, ofmt=ofmt, version=api_version)
    asyncio.run(device.collect(c))
    console.print(c.output)


@click.command()
@click.option("--template", "-t", type=str, required=True, help="Command template to run. E.g. 'show vlan {vlan_id}'")
@click.option("--ofmt", type=click.Choice(["text", "json"]), default="json", help="EOS eAPI format to use. can be text or json")
@click.option("--api-version", "--version", type=EapiVersion(), default="latest", help="EOS eAPI version to use")
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use", callback=get_device)
@click.argument("params", required=True, nargs=-1)
def run_template(template: str, params: List[str], ofmt: str, api_version: Union[int, Literal["latest"]], device: AntaDevice) -> None:
    """Run arbitrary templated command to an ANTA device.

    Takes a list of arguments (keys followed by a value) to build a dictionary used as template parameters.
    Example:

    anta debug run-template -d leaf1a -t 'show vlan {vlan_id}' vlan_id 1
    """
    template_params = dict(zip(params[::2], params[1::2]))

    console.print(f"Run templated command [blue]'{template}'[/blue] with [orange]{template_params}[/orange] on [red]{device.name}[/red]")
    c = AntaTestCommand(
        command=template.format(**template_params), template=AntaTemplate(template=template), template_params=template_params, ofmt=ofmt, version=api_version
    )
    asyncio.run(device.collect(c))
    console.print(c.output)
