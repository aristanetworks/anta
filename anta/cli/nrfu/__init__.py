# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Click commands that run ANTA tests using anta.runner
"""
from __future__ import annotations

import asyncio

import click

from anta.catalog import AntaCatalog
from anta.cli.nrfu import commands
from anta.cli.utils import catalog_options, inventory_options
from anta.inventory import AntaInventory
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main

from .utils import anta_progress_bar, print_settings


@click.group(invoke_without_command=True)
@click.pass_context
@inventory_options
@catalog_options
@click.option("--ignore-status", help="Always exit with success", show_envvar=True, is_flag=True, default=False)
@click.option("--ignore-error", help="Only report failures and not errors", show_envvar=True, is_flag=True, default=False)
def nrfu(ctx: click.Context, inventory: AntaInventory, tags: list[str] | None, catalog: AntaCatalog, ignore_status: bool, ignore_error: bool) -> None:
    """Run NRFU against inventory devices"""
    # We use ctx.obj to pass stuff to the next Click functions
    ctx.ensure_object(dict)
    ctx.obj["result_manager"] = ResultManager()
    ctx.obj["ignore_status"] = ignore_status
    ctx.obj["ignore_error"] = ignore_error
    print_settings(inventory, catalog)
    with anta_progress_bar() as AntaTest.progress:
        asyncio.run(main(ctx.obj["result_manager"], inventory, catalog, tags=tags))
    # Invoke `anta nrfu table` if no command is passed
    if ctx.invoked_subcommand is None:
        ctx.invoke(commands.table)


nrfu.add_command(commands.table)
nrfu.add_command(commands.json)
nrfu.add_command(commands.text)
nrfu.add_command(commands.tpl_report)
