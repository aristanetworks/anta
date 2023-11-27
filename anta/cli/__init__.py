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
from typing import Any

import click

from anta import __version__
from anta.catalog import AntaCatalog
from anta.cli.check import commands as check_commands
from anta.cli.debug import commands as debug_commands
from anta.cli.exec import commands as exec_commands
from anta.cli.get import commands as get_commands
from anta.cli.nrfu import commands as nrfu_commands
from anta.cli.utils import AliasedGroup, IgnoreRequiredWithHelp, catalog_options, inventory_options
from anta.inventory import AntaInventory
from anta.logger import Log, LogLevel, setup_logging
from anta.result_manager import ResultManager


@click.group(cls=IgnoreRequiredWithHelp)
@click.pass_context
@click.version_option(__version__)
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
        [Log.CRITICAL, Log.ERROR, Log.WARNING, Log.INFO, Log.DEBUG],
        case_sensitive=False,
    ),
)
def anta(ctx: click.Context, log_level: LogLevel, log_file: pathlib.Path) -> None:
    """Arista Network Test Automation (ANTA) CLI"""
    ctx.ensure_object(dict)
    setup_logging(log_level, log_file)


@anta.group("nrfu", cls=IgnoreRequiredWithHelp)
@click.pass_context
@inventory_options
@catalog_options
@click.option("--ignore-status", help="Always exit with success", show_envvar=True, is_flag=True, default=False)
@click.option("--ignore-error", help="Only report failures and not errors", show_envvar=True, is_flag=True, default=False)
def _nrfu(ctx: click.Context, inventory: AntaInventory, catalog: AntaCatalog, **kwargs: dict[str, Any]) -> None:
    # pylint: disable=unused-argument
    """Run NRFU against inventory devices"""
    ctx.obj["catalog"] = catalog
    ctx.obj["inventory"] = inventory
    ctx.obj["result_manager"] = ResultManager()


@anta.group("check", cls=AliasedGroup)
def _check() -> None:
    """Check commands for building ANTA"""


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
_check.add_command(check_commands.catalog)
# Inventory cannot be implemented for now as main 'anta' CLI is already parsing it
# _check.add_command(check_commands.inventory)

_exec.add_command(exec_commands.clear_counters)
_exec.add_command(exec_commands.snapshot)
_exec.add_command(exec_commands.collect_tech_support)

_get.add_command(get_commands.from_cvp)
_get.add_command(get_commands.from_ansible)
_get.add_command(get_commands.inventory)
_get.add_command(get_commands.tags)

_debug.add_command(debug_commands.run_cmd)
_debug.add_command(debug_commands.run_template)

_nrfu.add_command(nrfu_commands.table)
_nrfu.add_command(nrfu_commands.json)
_nrfu.add_command(nrfu_commands.text)
_nrfu.add_command(nrfu_commands.tpl_report)


# ANTA CLI Execution
def cli() -> None:
    """Entrypoint for pyproject.toml"""
    anta(obj={}, auto_envvar_prefix="ANTA")  # pragma: no cover


if __name__ == "__main__":
    cli()
