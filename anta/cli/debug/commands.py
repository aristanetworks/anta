# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable = redefined-outer-name
"""
Commands for Anta CLI to run debug commands.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Literal

import click
from click import Option

from anta.cli.console import console
from anta.device import AntaDevice
from anta.models import AntaCommand, AntaTemplate
from anta.tools.misc import anta_log_exception

logger = logging.getLogger(__name__)


# pylint: disable-next=inconsistent-return-statements
def get_device(ctx: click.Context, param: Option, value: str) -> list[str]:
    """
    Click option callback to get an AntaDevice instance from a string
    """
    # pylint: disable=unused-argument
    try:
        return ctx.obj["inventory"][value]
    except KeyError as e:
        message = f"Device {value} does not exist in Inventory"
        anta_log_exception(e, message, logger)
        ctx.fail(message)


@click.command()
@click.option("--command", "-c", type=str, required=True, help="Command to run")
@click.option("--ofmt", type=click.Choice(["json", "text"]), default="json", help="EOS eAPI format to use. can be text or json")
@click.option("--version", "-v", type=click.Choice(["1", "latest"]), default="latest", help="EOS eAPI version")
@click.option("--revision", "-r", type=int, help="eAPI command revision", required=False)
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use", callback=get_device)
def run_cmd(command: str, ofmt: Literal["json", "text"], version: Literal["1", "latest"], revision: int, device: AntaDevice) -> None:
    """Run arbitrary command to an ANTA device"""
    console.print(f"Run command [green]{command}[/green] on [red]{device.name}[/red]")
    # I do not assume the following line, but click make me do it
    v: Literal[1, "latest"] = version if version == "latest" else 1
    c = AntaCommand(command=command, ofmt=ofmt, version=v, revision=revision)
    asyncio.run(device.collect(c))
    if c.failed:
        console.print(f"[bold red] Command '{c.command}' failed to execute!")
        sys.exit(1)
    elif ofmt == "json":
        console.print(c.json_output)
    elif ofmt == "text":
        console.print(c.text_output)


@click.command()
@click.option("--template", "-t", type=str, required=True, help="Command template to run. E.g. 'show vlan {vlan_id}'")
@click.option("--ofmt", type=click.Choice(["json", "text"]), default="json", help="EOS eAPI format to use. can be text or json")
@click.option("--version", "-v", type=click.Choice(["1", "latest"]), default="latest", help="EOS eAPI version")
@click.option("--revision", "-r", type=int, help="eAPI command revision", required=False)
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use", callback=get_device)
@click.argument("params", required=True, nargs=-1)
def run_template(template: str, params: list[str], ofmt: Literal["json", "text"], version: Literal["1", "latest"], revision: int, device: AntaDevice) -> None:
    # pylint: disable=too-many-arguments
    """Run arbitrary templated command to an ANTA device.

    Takes a list of arguments (keys followed by a value) to build a dictionary used as template parameters.
    Example:

    anta debug run-template -d leaf1a -t 'show vlan {vlan_id}' vlan_id 1
    """
    template_params = dict(zip(params[::2], params[1::2]))

    console.print(f"Run templated command [blue]'{template}'[/blue] with [orange]{template_params}[/orange] on [red]{device.name}[/red]")
    # I do not assume the following line, but click make me do it
    v: Literal[1, "latest"] = version if version == "latest" else 1
    t = AntaTemplate(template=template, ofmt=ofmt, version=v, revision=revision)
    c = t.render(**template_params)  # type: ignore
    asyncio.run(device.collect(c))
    if c.failed:
        console.print(f"[bold red] Command '{c.command}' failed to execute!")
        sys.exit(1)
    elif ofmt == "json":
        console.print(c.json_output)
    elif ofmt == "text":
        console.print(c.text_output)
