#!/usr/bin/env python
# coding: utf-8 -*-


"""
ANTA CLI Baseline.
"""

import logging

import click

from anta import __version__
from anta.cli.check import commands as check_commands
from anta.cli.debug import commands as debug_commands
from anta.cli.exec import commands as exec_commands
from anta.cli.get import commands as get_commands
from anta.cli.utils import setup_logging

# Top level entrypoint


@click.group()
@click.pass_context
@click.version_option(__version__)
@click.option("--username", show_envvar=True, default="admin", help="Username to connect to EOS", required=True)
@click.option("--password", show_envvar=True, default="arista123", help="Password to connect to EOS", required=True)
@click.option("--timeout", show_envvar=True, default=5, help="Connection timeout (default 5)", required=False)
@click.option("--enable-password", show_envvar=True, help="Enable password if required to connect", required=False)
@click.option(
    "--inventory",
    "-i",
    show_envvar=True,
    required=True,
    help="Path to your inventory file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True),
)
@click.option(
    "--log-level",
    "--log",
    show_envvar=True,
    help="ANTA logging level",
    default=logging.getLevelName(logging.INFO),
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
def anta(ctx: click.Context, username: str, password: str, enable_password: str, inventory: str, timeout: int, log_level: str) -> None:
    """Arista Network Test CLI"""
    # pylint: disable=too-many-arguments
    ctx.ensure_object(dict)
    ctx.obj["inventory"] = inventory
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["timeout"] = timeout
    ctx.obj["enable_password"] = enable_password
    ctx.obj["timeout"] = timeout
    setup_logging(level=log_level)


@anta.group()
def nrfu() -> None:
    """Run NRFU against inventory devices"""


@anta.group("exec")
def _exec() -> None:
    """Execute commands to inventory devices"""


@anta.group("get")
def get() -> None:
    """Get data from/to ANTA"""


@anta.group("debug")
def debug() -> None:
    """Debug commands for building ANTA"""


# ANTA CLI Execution
def cli() -> None:
    """Load ANTA CLI"""
    # Load group commands
    _exec.add_command(exec_commands.clear_counters)
    _exec.add_command(exec_commands.snapshot)
    _exec.add_command(exec_commands.collect_tech_support)

    get.add_command(get_commands.from_cvp)
    get.add_command(get_commands.inventory)
    get.add_command(get_commands.tags)

    debug.add_command(debug_commands.run_cmd)
    debug.add_command(debug_commands.run_template)

    nrfu.add_command(check_commands.table)
    nrfu.add_command(check_commands.json)
    nrfu.add_command(check_commands.text)
    nrfu.add_command(check_commands.tpl_report)
    # Load CLI
    anta(obj={}, auto_envvar_prefix="ANTA")


if __name__ == "__main__":
    cli()
