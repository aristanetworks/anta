#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable = redefined-outer-name

"""
Commands for Anta CLI to run debug commands.
"""

import asyncio
import json
import logging
from typing import Literal, Union

import click
from rich import print_json
from rich.console import Console

from anta.cli.debug.utils import RunArbitraryCommand
from anta.cli.utils import EapiVersion, setup_logging
from anta.inventory import AntaInventory
from anta.models import AntaTest, AntaTestCommand, AntaTestTemplate

logger = logging.getLogger(__name__)
templater: str = ""


@click.command()
@click.pass_context
@click.option("--command", "-c", type=str, required=True, help="Command to run on EOS using eAPI")
@click.option("--ofmt", type=click.Choice(["text", "json"]), default="json", help="eAPI format to use. can be text or json")
@click.option("--api-version", "--version", type=EapiVersion(), default="latest", help="Version of the command through eAPI")
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use")
@click.option("--log-level", "--log", help="Logging level of the command", default="warning")
def run_cmd(ctx: click.Context, command: str, ofmt: str, api_version: Union[int, Literal["latest"]], device: str, log_level: str) -> None:
    """Run arbitrary command to an EOS device and get result using eAPI"""
    # pylint: disable=too-many-arguments
    console = Console()
    setup_logging(level=log_level)

    inventory_anta = AntaInventory(
        inventory_file=ctx.obj["inventory"], username=ctx.obj["username"], password=ctx.obj["password"], enable_password=ctx.obj["enable_password"]
    )

    device_anta = [inventory_device for inventory_device in inventory_anta.get_inventory() if inventory_device.name == device][0]

    logger.info(f"receive device from inventory: {device_anta}")

    console.print(f"run command [green]{command}[/green] on [red]{device}[/red]")

    run_command = RunArbitraryCommand(device=device_anta)
    run_command.instance_commands = [AntaTestCommand(command=command, ofmt=ofmt, version=api_version)]
    asyncio.run(run_command.collect())
    result = run_command.instance_commands[0].output
    console.print(result)


@click.command()
@click.pass_context
@click.option("--template", "-t", type=str, required=False, default="{}", help="Command template to run on EOS using eAPI")
@click.option("--params", "-p", type=str, required=True, help="Command parameters to use with template. Must be a JSON string for a list of dict")
@click.option("--ofmt", type=click.Choice(["text", "json"]), default="json", help="eAPI format to use. can be text or json")
@click.option("--api-version", "--version", type=EapiVersion(), default="latest", help="Version of the command through eAPI")
@click.option("--device", "-d", type=str, required=True, help="Device from inventory to use")
@click.option("--log-level", "--log", help="Logging level of the command", default="warning")
def run_template(ctx: click.Context, template: str, params: str, ofmt: str, api_version: Union[int, Literal["latest"]], device: str, log_level: str) -> None:
    """Run arbitrary command to an EOS device and get result using eAPI"""
    # pylint: disable=too-many-arguments
    # pylint: disable=unused-argument
    console = Console()
    setup_logging(level=log_level)
    inventory_anta = AntaInventory(
        inventory_file=ctx.obj["inventory"], username=ctx.obj["username"], password=ctx.obj["password"], enable_password=ctx.obj["enable_password"]
    )
    device_anta = [inventory_device for inventory_device in inventory_anta.get_inventory() if inventory_device.name == device][0]
    logger.info(f"receive device from inventory: {device_anta}")
    console.print(f"run dynmic command [blue]{template}[/blue] with [orange]{params}[/orange] on [red]{device}[/red]")

    params = json.loads(params)
    assert isinstance(params, list)

    templater = template

    class RunArbitraryTemplateCommand(AntaTest):
        """
        Run an EOS command and return result
        Based on AntaTest to build relevant output for pytest
        """

        name = "Run aributrary EOS command"
        description = "To be used only with anta debug commands"
        template = AntaTestTemplate(template=templater)
        categories = ["debug"]

        @AntaTest.anta_test
        def test(self) -> None:
            """
            Fake test function
            CLI should only call self.collect()
            """

    async def internal_run() -> None:
        """Workaround for running potential multipple asyncio call without closing loop"""
        # template_obj = AntaTestTemplate(template=template, ofmt=ofmt, version=api_version)
        # RunArbitraryTemplateCommand.__class__.template = template_obj
        run_command1 = RunArbitraryTemplateCommand(device_anta, params)
        for cmd in run_command1.instance_commands:
            console.print(f"run_command = [green]{cmd.command}[/green] [red]{device}[/red]")
            await run_command1.collect()
            result = run_command1.instance_commands
            print_json(json.dumps(result[0].output))

    asyncio.run(internal_run())
