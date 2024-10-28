# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable = redefined-outer-name
"""Click commands to execute EOS commands on remote devices."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Literal

import click

from anta.cli.console import console
from anta.cli.debug.utils import debug_options
from anta.cli.utils import ExitCode
from anta.models import AntaCommand, AntaTemplate

if TYPE_CHECKING:
    from anta.device import AntaDevice

logger = logging.getLogger(__name__)


@click.command
@debug_options
@click.pass_context
@click.option("--command", "-c", type=str, required=True, help="Command to run")
def run_cmd(
    ctx: click.Context,
    device: AntaDevice,
    command: str,
    ofmt: Literal["json", "text"],
    version: Literal["1", "latest"],
    revision: int,
) -> None:
    """Run arbitrary command to an ANTA device."""
    console.print(f"Run command [green]{command}[/green] on [red]{device.name}[/red]")
    # I do not assume the following line, but click make me do it
    v: Literal[1, "latest"] = version if version == "latest" else 1
    c = AntaCommand(command=command, ofmt=ofmt, version=v, revision=revision)
    asyncio.run(device.collect(c))
    if not c.collected:
        console.print(f"[bold red] Command '{c.command}' failed to execute!")
        ctx.exit(ExitCode.USAGE_ERROR)
    elif ofmt == "json":
        console.print(c.json_output)
    elif ofmt == "text":
        console.print(c.text_output)


@click.command
@debug_options
@click.pass_context
@click.option(
    "--template",
    "-t",
    type=str,
    required=True,
    help="Command template to run. E.g. 'show vlan {vlan_id}'",
)
@click.argument("params", required=True, nargs=-1)
def run_template(
    ctx: click.Context,
    device: AntaDevice,
    template: str,
    params: list[str],
    ofmt: Literal["json", "text"],
    version: Literal["1", "latest"],
    revision: int,
) -> None:
    # Using \b for click
    # ruff: noqa: D301
    """Run arbitrary templated command to an ANTA device.

    Takes a list of arguments (keys followed by a value) to build a dictionary used as template parameters.

    \b
    Example
    -------
        anta debug run-template -d leaf1a -t 'show vlan {vlan_id}' vlan_id 1

    """
    template_params = dict(zip(params[::2], params[1::2]))

    console.print(f"Run templated command [blue]'{template}'[/blue] with [orange]{template_params}[/orange] on [red]{device.name}[/red]")
    # I do not assume the following line, but click make me do it
    v: Literal[1, "latest"] = version if version == "latest" else 1
    t = AntaTemplate(template=template, ofmt=ofmt, version=v, revision=revision)
    c = t.render(**template_params)
    asyncio.run(device.collect(c))
    if not c.collected:
        console.print(f"[bold red] Command '{c.command}' failed to execute!")
        ctx.exit(ExitCode.USAGE_ERROR)
    elif ofmt == "json":
        console.print(c.json_output)
    elif ofmt == "text":
        console.print(c.text_output)
