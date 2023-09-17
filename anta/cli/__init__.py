#!/usr/bin/env python
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# coding: utf-8 -*-
"""
ANTA CLI
"""
from __future__ import annotations

import logging
import pathlib
from typing import Any, Callable, Literal

import click

from anta import __version__
from anta.cli.debug import commands as debug_commands
from anta.cli.exec import commands as exec_commands
from anta.cli.get import commands as get_commands
from anta.cli.nrfu import commands as check_commands
from anta.cli.utils import AliasedGroup, IgnoreRequiredWithHelp, parse_catalog, parse_inventory
from anta.loader import setup_logging
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult


@click.group(cls=IgnoreRequiredWithHelp)
@click.pass_context
@click.version_option(__version__)
@click.option(
    "--username",
    help="Username to connect to EOS",
    show_envvar=True,
    required=True,
)
@click.option("--password", help="Password to connect to EOS that must be provided. It can be prompted using '--prompt' option.", show_envvar=True)
@click.option(
    "--enable-password",
    help="Password to access EOS Privileged EXEC mode. It can be prompted using '--prompt' option. Requires '--enable' option.",
    show_envvar=True,
)
@click.option(
    "--enable",
    help="Some commands may require EOS Privileged EXEC mode. This option tries to access this mode before sending a command to the device.",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
)
@click.option(
    "--prompt",
    "-P",
    help="Prompt for passwords if they are not provided.",
    default=False,
    is_flag=True,
    show_default=True,
)
@click.option(
    "--timeout",
    help="Global connection timeout",
    default=30,
    show_envvar=True,
    show_default=True,
)
@click.option(
    "--insecure",
    help="Disable SSH Host Key validation",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
)
@click.option(
    "--inventory",
    "-i",
    help="Path to the inventory YAML file",
    show_envvar=True,
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=pathlib.Path),
)
@click.option(
    "--log-file",
    help="Send the logs to a file. If logging level is DEBUG, only INFO or higher will be sent to stdout.",
    show_envvar=True,
    type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=pathlib.Path),
)
@click.option(
    "--log-level",
    "--log",
    help="ANTA logging level",
    default=logging.getLevelName(logging.INFO),
    show_envvar=True,
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
)
@click.option("--ignore-status", help="Always exit with success", show_envvar=True, is_flag=True, default=False)
@click.option("--ignore-error", help="Only report failures and not errors", show_envvar=True, is_flag=True, default=False)
def anta(
    ctx: click.Context, inventory: pathlib.Path, log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], log_file: pathlib.Path, **kwargs: Any
) -> None:
    # pylint: disable=unused-argument
    """Arista Network Test Automation (ANTA) CLI"""
    setup_logging(log_level, log_file)

    if not ctx.obj.get("_anta_help"):
        if ctx.params.get("prompt"):
            # User asked for a password prompt
            if ctx.params.get("password") is None:
                ctx.params["password"] = click.prompt("Please enter a password to connect to EOS", type=str, hide_input=True, confirmation_prompt=True)
            if ctx.params.get("enable"):
                if ctx.params.get("enable_password") is None:
                    if click.confirm("Is a password required to enter EOS privileged EXEC mode?"):
                        ctx.params["enable_password"] = click.prompt(
                            "Please enter a password to enter EOS privileged EXEC mode", type=str, hide_input=True, confirmation_prompt=True
                        )
        if ctx.params.get("password") is None:
            raise click.BadParameter(
                f"EOS password needs to be provided by using either the '{anta.params[2].opts[0]}' option or the '{anta.params[5].opts[0]}' option."
            )
        if not ctx.params.get("enable") and ctx.params.get("enable_password"):
            raise click.BadParameter(f"Providing a password to access EOS Privileged EXEC mode requires '{anta.params[4].opts[0]}' option.")

    ctx.ensure_object(dict)
    ctx.obj["inventory"] = parse_inventory(ctx, inventory)


@anta.group("nrfu", cls=IgnoreRequiredWithHelp)
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
def _nrfu(ctx: click.Context, catalog: list[tuple[Callable[..., TestResult], dict[Any, Any]]]) -> None:
    """Run NRFU against inventory devices"""
    ctx.obj["catalog"] = catalog
    ctx.obj["result_manager"] = ResultManager()


@anta.group("exec", cls=AliasedGroup)
def _exec() -> None:
    """Execute commands to inventory devices"""


@anta.group("get", cls=AliasedGroup)
def _get() -> None:
    """Get data from/to ANTA"""


@anta.group("debug", cls=AliasedGroup)
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

_nrfu.add_command(check_commands.table)
_nrfu.add_command(check_commands.json)
_nrfu.add_command(check_commands.text)
_nrfu.add_command(check_commands.tpl_report)


# ANTA CLI Execution
def cli() -> None:
    """Entrypoint for pyproject.toml"""
    anta(obj={}, auto_envvar_prefix="ANTA")  # pragma: no cover


if __name__ == "__main__":
    cli()
