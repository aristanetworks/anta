# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import asyncio
from typing import Any

import click

from anta.cli.nrfu import commands
from anta.cli.utils import catalog_options, inventory_options
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main

from .utils import anta_progress_bar, print_settings


@click.group("nrfu", invoke_without_command=True)
@click.pass_context
@inventory_options
@catalog_options
@click.option("--ignore-status", help="Always exit with success", show_envvar=True, is_flag=True, default=False)
@click.option("--ignore-error", help="Only report failures and not errors", show_envvar=True, is_flag=True, default=False)
def nrfu(ctx: click.Context, **kwargs: dict[str, Any]) -> None:
    # pylint: disable=unused-argument
    """Run NRFU against inventory devices"""
    ctx.obj["result_manager"] = ResultManager()
    print_settings(ctx)
    with anta_progress_bar() as AntaTest.progress:
        asyncio.run(main(ctx.obj["result_manager"], ctx.obj["inventory"], ctx.obj["catalog"], tags=ctx.params.get("tags")))
    # Invoke `anta nrfu table` if no command is passed
    if ctx.invoked_subcommand is None:
        ctx.invoke(commands.table)


nrfu.add_command(commands.table)
nrfu.add_command(commands.json)
nrfu.add_command(commands.text)
nrfu.add_command(commands.tpl_report)
