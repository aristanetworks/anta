#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
# pylint: disable=line-too-long
# flake8: noqa E501

"""
Commands for Anta CLI to execute EOS commands.
"""

import sys
import logging
import asyncio
import click
from yaml import safe_load

from anta.inventory import AntaInventory
from anta.cli.utils import setup_logging
from anta.cli.exec.utils import clear_counters_utils, collect_commands
# from anta.cli.cli import exec
# from .utils import check_run, display_table, display_json, display_list

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
# Generic options
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
# Debug stuf
@click.option('--log-level', '--log', help='Logging level of the command', default='info', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def clear_counters(ctx: click.Context, log_level: str, tags: str) -> None:
    """Clear counter statistics on EOS devices"""

    setup_logging(level=log_level)

    inventory_anta = AntaInventory(
        inventory_file=ctx.obj['inventory'],
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        enable_password=ctx.obj['enable_password']
    )
    asyncio.run(clear_counters_utils(
        inventory_anta, ctx.obj['enable_password'], tags=tags.split(','))
        )


@click.command()
@click.pass_context
# Generic options
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
@click.option('--commands-list', '-c', show_envvar=True, type=click.Path(), help='File with list of commands to grab')
@click.option('--output-directory', '-outut', '-o', show_envvar=True, type=click.Path(), help='Path where to save commands output')
# Debug stuf
@click.option('--log-level', '--log', help='Logging level of the command', default='info', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def snapshot(ctx: click.Context, commands_list: str, log_level: str, output_directory: str, tags: str) -> None:
    """Collect commands output from devices in inventory"""
    setup_logging(level=log_level)
    try:
        with open(commands_list, "r", encoding="utf8") as file:
            file_content = file.read()
            eos_commands = safe_load(file_content)
    except FileNotFoundError:
        logger.error(f"Error reading {commands_list}")
        sys.exit(1)
    inventory = AntaInventory(
        inventory_file=ctx.obj['inventory'],
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        enable_password=ctx.obj['enable_password']
    )
    asyncio.run(collect_commands(inventory, ctx.obj['enable_password'],
                eos_commands, output_directory, tags=tags.split(',')))
