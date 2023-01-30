#!/usr/bin/python
# coding: utf-8 -*-
# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments

"""
Commands for Anta CLI to execute EOS commands.
"""

import logging
import asyncio
import click

from anta.inventory import AntaInventory
from anta.cli.utils import setup_logging
from anta.cli.exec.utils import clear_counters_utils
# from anta.cli.cli import exec
# from .utils import check_run, display_table, display_json, display_list

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
# Generic options
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
# Debug stuf
@click.option('--log-level', '--log', default='info', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
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
