#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments

"""
Commands for Anta CLI to run check commands.
"""

import re
import logging
import click

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel

from anta import RICH_COLOR_THEME
from anta.cli.cli import anta
from .utils import check_run, display_table, display_json, display_list

logger = logging.getLogger(__name__)


@anta.command(no_args_is_help=True)
@click.pass_context
# Generic options
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=click.File())
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
@click.option('--display', default='table', type=click.Choice(['table', 'json', 'list'], case_sensitive=False), help='output format selection. default is table')
# Options valid with --display table
@click.option('--search', default=None, help='Value to search in result. Can be test name or host name', type=str)
@click.option('--group-by', default='none', type=click.Choice(['none', 'host', 'test'], case_sensitive=False), help='Group result by test or host. default none')
# Options valid with --display json
@click.option('--output', '-o', default=None, help='Path to save output in json or list', type=click.Path())
# Debug stuf
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def check_default(ctx: click.Context, catalog: str, display: str, tags: str, group_by: str, search: str, output: str, log_level: str) -> bool:
    """ANTA command to check network states"""
    console = Console()
    inventory = ctx.obj['inventory']

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(
        inventory=inventory,
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password=ctx.obj['enable_password'],
        tags=tags,
        loglevel=log_level
    )
    if display == 'table':
        display_table(console=console, results=results, group_by=group_by, search=search)
    elif display == 'json':
        display_json(console=console, results=results, output_file=output)
    elif display == 'list':
        display_list(console=console, results=results, output_file=output)

    return True


@anta.command(no_args_is_help=True)
@click.pass_context
# Generic options
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=str)
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
# Options valid with --display table
@click.option('--search', default=None, help='Value to search in result. Can be test name or host name', type=str)
@click.option('--group-by', default=None, type=click.Choice(['none', 'host', 'test'], case_sensitive=False), help='Group result by test or host. default none')
# Debug stuf
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def table(ctx: click.Context, catalog: str, tags: str, group_by: str, search: str, log_level: str) -> bool:
    """ANTA command to check network states with table result"""
    console = Console()
    inventory = ctx.obj['inventory']

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(
        inventory=inventory,
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password=ctx.obj['enable_password'],
        tags=tags,
        loglevel=log_level
    )
    display_table(console=console, results=results, group_by=group_by, search=search)

    return True


@anta.command(no_args_is_help=True)
@click.pass_context
# Generic options
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=str)
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
# Options valid with --display json
@click.option('--output', '-o', default=None, help='Path to save output in json or list', type=click.File())
# Debug stuf
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def json(ctx: click.Context, catalog: str, output: str, tags: str, log_level: str) -> bool:
    # pylint: disable=redefined-builtin
    """ANTA command to check network state with JSON result"""
    console = Console()
    inventory = ctx.obj['inventory']

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(
        inventory=inventory,
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password=ctx.obj['enable_password'],
        tags=tags,
        loglevel=log_level
    )
    display_json(console=console, results=results, output_file=output)

    return True


@anta.command(no_args_is_help=True)
@click.pass_context
# Generic options
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=str)
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
@click.option('--output', '-o', default=None, help='Path to save output in json or list', type=click.File())
# Debug stuf
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def list(ctx: click.Context, catalog: str, tags: str, output: str, log_level: str) -> bool:
    # pylint: disable=redefined-builtin
    """ANTA command to check network states with list result"""
    console = Console()
    inventory = ctx.obj['inventory']

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(
        inventory=inventory,
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password=ctx.obj['enable_password'],
        tags=tags,
        loglevel=log_level
    )
    display_list(console=console, results=results, output_file=output)

    return True


@anta.command()
@click.pass_context
@click.option('--catalog', '-c', show_envvar=True, prompt='Path for tests catalog', help='Path for tests catalog', type=str)
@click.option('--tags', '-t', default='all', help='List of tags using coma as separator: tag1,tag2,tag3', type=str)
@click.option('--search', default=".*", help='Regular expression to search in both name and test', type=str)
@click.option('--skip-error/--no-skip-error', help='Hide tests in errors due to connectivity issue', default=False)
@click.option('--log-level', '--log', default='warning', type=click.Choice(['debug', 'info', 'warning', 'critical'], case_sensitive=False))
def ci(ctx: click.Context, catalog: str, tags: str, search: str, skip_error: bool, log_level: str) -> bool:
    """Execute network testing in context of CI by mimicing Pytest output"""
    custom_theme = Theme(RICH_COLOR_THEME)
    console = Console(theme=custom_theme)
    results = check_run(
        inventory=ctx.obj['inventory'],
        catalog=catalog,
        username=ctx.obj['username'],
        password=ctx.obj['password'],
        timeout=ctx.obj['timeout'],
        enable_password=ctx.obj['enable_password'],
        tags=tags,
        loglevel=log_level
    )
    regexp = re.compile(search)
    for line in results.get_results(output_format="list"):
        if any(regexp.match(entry) for entry in [line.name, line.test]) and (
            not skip_error or line.result != 'error'
        ):
            message = f" ({str(line.messages[0])})" if len(line.messages) > 0 else ''
            console.print(
                f'{line.name} :: {line.test} :: [{line.result}]{line.result.upper()}[/{line.result}]{message}', highlight=False)
    return True
