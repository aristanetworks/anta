#!/usr/bin/python
# coding: utf-8 -*-

import click

from anta.cli.check import commands as check_commands

# Top level entrypoint

@click.group()
@click.pass_context
@click.option('--username', show_envvar=True, default='arista', help='Username to connect to EOS')
@click.option('--password', show_envvar=True, default='arista123', help='Password to connect to EOS')
@click.option('--timeout', show_envvar=True, default=5, help='Connection timeout (default 5)')
@click.option('--enable-password', show_envvar=True, default='unset', help='Enable password if required to connect')
def anta(ctx,username, password, enable_password, timeout):
    """Arista Network Test CLI """
    ctx.ensure_object(dict)
    ctx.obj['username'] = username
    ctx.obj['password'] = password
    ctx.obj['timeout'] = timeout
    ctx.obj['enable_password'] = enable_password
    return

# ANTA CLI Execution

if __name__ == '__main__':
    # Load group commands
    anta.add_command(check_commands.check)
    # Load CLI
    anta(
        obj={},
        auto_envvar_prefix='ANTA'
    )
