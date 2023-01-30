#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=no-value-for-parameter
# pylint: disable=cyclic-import
# pylint: disable=redefined-builtin
# pylint: disable=too-many-arguments


"""
ANTA CLI Baseline.
"""

import click

from anta.cli.check import commands as check_commands
from anta.cli.exec import commands as exec_commands

# Top level entrypoint


@click.group()
@click.pass_context
@click.option('--username', show_envvar=True, default='arista', help='Username to connect to EOS')
@click.option('--password', show_envvar=True, default='arista123', help='Password to connect to EOS')
@click.option('--timeout', show_envvar=True, default=5, help='Connection timeout (default 5)')
@click.option('--enable-password', show_envvar=True, default='', help='Enable password if required to connect')
@click.option('--inventory', '-i', show_envvar=True, prompt='Inventory path', help='Path to your inventory file', type=click.File())
def anta(ctx: click.Context, username: str, password: str, enable_password: str, inventory: str, timeout: int) -> None:
    """Arista Network Test CLI """
    ctx.ensure_object(dict)
    ctx.obj['inventory'] = inventory
    ctx.obj['username'] = username
    ctx.obj['password'] = password
    ctx.obj['timeout'] = timeout
    ctx.obj['enable_password'] = enable_password


@anta.group()
@click.pass_context
@click.option('--timeout', show_envvar=True, default=5, help='Connection timeout (default 5)')
def exec(ctx: click.Context, timeout: int) -> None:
    """Execute commands to inventory devices"""
    ctx.ensure_object(dict)
    ctx.obj['timeout'] = timeout

# ANTA CLI Execution


if __name__ == '__main__':
    # Load group commands
    exec.add_command(exec_commands.clear_counters)
    exec.add_command(exec_commands.snapshot)
    anta.add_command(check_commands.check)  # type: ignore
    anta.add_command(check_commands.ci)  # type: ignore
    # Load CLI
    anta(
        obj={},
        auto_envvar_prefix='ANTA'
    )
