#!/usr/bin/env python
# coding: utf-8 -*-
"""
ANTA CLI
"""

import logging
import pathlib
from typing import Any, Callable, Dict, List, Tuple

import click

from anta import __version__
from anta.cli.debug import commands as debug_commands
from anta.cli.exec import commands as exec_commands
from anta.cli.get import commands as get_commands
from anta.cli.nrfu import commands as check_commands
from anta.cli.utils import IgnoreRequiredWithHelp, parse_catalog, parse_inventory, requires_enable, setup_logging
from anta.result_manager.models import TestResult


# @click.group()
@click.group(cls=IgnoreRequiredWithHelp)
@click.pass_context
@click.version_option(__version__)
@click.option(
    "--username",
    show_envvar=True,
    help="Username to connect to EOS",
    required=True,
)
@click.option(
    "--password",
    show_envvar=True,
    help="Password to connect to EOS",
    required=True,
)
@click.option(
    "--timeout",
    show_envvar=True,
    default=5,
    help="Global connection timeout",
    show_default=True,
)
@click.option(
    "--insecure",
    show_envvar=True,
    is_flag=True,
    default=False,
    help="Disable SSH Host Key validation",
    show_default=True,
)
@click.option(
    "--enable",
    show_envvar=True,
    is_flag=True,
    default=False,
    help="Add enable mode towards the devices if required to connect",
    show_default=True,
)
@click.option(
    "--enable-password",
    show_envvar=True,
    help="Enable password if required to connect, --enable MUST be set",
    callback=requires_enable,
)
@click.option(
    "--inventory",
    "-i",
    show_envvar=True,
    required=True,
    help="Path to the inventory YAML file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=pathlib.Path),
)
@click.option(
    "--log-level",
    "--log",
    show_envvar=True,
    help="ANTA logging level",
    default=logging.getLevelName(logging.INFO),
    show_default=True,
    type=click.Choice(
        [
            logging.getLevelName(logging.CRITICAL),
            logging.getLevelName(logging.ERROR),
            logging.getLevelName(logging.WARNING),
            logging.getLevelName(logging.INFO),
            logging.getLevelName(logging.DEBUG),
        ],
        case_sensitive=False,
    ),
    callback=setup_logging,
)
@click.option("--ignore-status", show_envvar=True, is_flag=True, default=False, help="Always exit with success")
@click.option("--ignore-error", show_envvar=True, is_flag=True, default=False, help="Only report failures and not errors")
def anta(ctx: click.Context, inventory: pathlib.Path, ignore_status: bool, ignore_error: bool, **kwargs: Any) -> None:
    # pylint: disable=unused-argument
    """Arista Network Test Automation (ANTA) CLI"""
    ctx.ensure_object(dict)
    ctx.obj["inventory"] = parse_inventory(ctx, inventory)
    ctx.obj["ignore_status"] = ignore_status
    ctx.obj["ignore_error"] = ignore_error


@anta.group(cls=IgnoreRequiredWithHelp)
@click.pass_context
@click.option(
    "--catalog",
    "-c",
    show_envvar=True,
    help="Path to the tests catalog YAML file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True),
    required=True,
    callback=parse_catalog,
)
def nrfu(ctx: click.Context, catalog: List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]) -> None:
    """Run NRFU against inventory devices"""
    ctx.obj["catalog"] = catalog


@anta.group("exec")
def _exec() -> None:
    """Execute commands to inventory devices"""


@anta.group("get")
def _get() -> None:
    """Get data from/to ANTA"""


@anta.group("debug")
def _debug() -> None:
    """Debug commands for building ANTA"""


# Load group commands
# Prefixing with `_` for avoiding the confusion when importing anta.cli.debug.commands as otherwise the debug group has
# a commands attribute.
_exec.add_command(exec_commands.clear_counters)
_exec.add_command(exec_commands.snapshot)
_exec.add_command(exec_commands.collect_tech_support)


_get.add_command(get_commands.from_cvp)
_get.add_command(get_commands.from_ansible)
_get.add_command(get_commands.inventory)
_get.add_command(get_commands.tags)

_debug.add_command(debug_commands.run_cmd)
_debug.add_command(debug_commands.run_template)

nrfu.add_command(check_commands.table)
nrfu.add_command(check_commands.json)
nrfu.add_command(check_commands.text)
nrfu.add_command(check_commands.tpl_report)


# ANTA CLI Execution
def cli() -> None:
    """Entrypoint for pyproject.toml"""
    anta(obj={}, auto_envvar_prefix="ANTA")  # pragma: no cover


if __name__ == "__main__":
    cli()
