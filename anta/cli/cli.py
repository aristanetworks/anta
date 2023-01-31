#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=no-value-for-parameter
# pylint: disable=cyclic-import
# pylint: disable=too-many-arguments


"""
ANTA CLI Baseline.
"""

import click

from anta.cli.check import commands as check_commands
from anta.cli.exec import commands as exec_commands
from anta.cli.inventory import commands as inv_commands

# Top level entrypoint


@click.group()
@click.pass_context
@click.option('--username', show_envvar=True, default='arista', help='Username to connect to EOS')
@click.option('--password', show_envvar=True, default='arista123', help='Password to connect to EOS')
@click.option('--timeout', show_envvar=True, default=5, help='Connection timeout (default 5)')
@click.option('--enable-password', show_envvar=True, default='', help='Enable password if required to connect')
@click.option('--inventory', '-i', show_envvar=True, default='', help='Path to your inventory file', type=str)
@click.option('--timeout', show_envvar=True, default=5, help='Connection timeout (default 5)')
def anta(ctx: click.Context, username: str, password: str, enable_password: str, inventory: str, timeout: int) -> None:
    """Arista Network Test CLI """
    ctx.ensure_object(dict)
    ctx.obj['inventory'] = inventory
    ctx.obj['username'] = username
    ctx.obj['password'] = password
    ctx.obj['timeout'] = timeout
    ctx.obj['enable_password'] = enable_password
    ctx.obj['timeout'] = timeout


@anta.group()
def check() -> None:
    """Run NRFU against inventory devices"""


@anta.group()
def exec() -> None:
    # pylint: disable=redefined-builtin
    """Execute commands to inventory devices"""


@anta.group()
def get() -> None:
    """Get data from/to ANTA"""

# ANTA CLI Execution


def cli() -> None:
    """Load ANTA CLI"""
    # Load group commands
    exec.add_command(exec_commands.clear_counters)
    exec.add_command(exec_commands.snapshot)
    get.add_command(inv_commands.from_cvp)
    check.add_command(check_commands.table)  # type: ignore
    check.add_command(check_commands.json)  # type: ignore
    check.add_command(check_commands.list)  # type: ignore
    check.add_command(check_commands.ci)    # type: ignore
    # Load CLI
    anta(
        obj={},
        auto_envvar_prefix='ANTA'
    )


if __name__ == '__main__':
    cli()

