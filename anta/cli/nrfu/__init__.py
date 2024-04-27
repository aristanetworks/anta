# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands that run ANTA tests using anta.runner."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, get_args

import click

from anta.cli.nrfu import commands
from anta.cli.utils import AliasedGroup, catalog_options, inventory_options
from anta.custom_types import TestStatus
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main

from .utils import anta_progress_bar, print_settings

if TYPE_CHECKING:
    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory


class IgnoreRequiredWithHelp(AliasedGroup):
    """Custom Click Group.

    https://stackoverflow.com/questions/55818737/python-click-application-required-parameters-have-precedence-over-sub-command-he

    Solution to allow help without required options on subcommand
    This is not planned to be fixed in click as per: https://github.com/pallets/click/issues/295#issuecomment-708129734.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Ignore MissingParameter exception when parsing arguments if `--help` is present for a subcommand."""
        # Adding a flag for potential callbacks
        ctx.ensure_object(dict)
        if "--help" in args:
            ctx.obj["_anta_help"] = True

        try:
            return super().parse_args(ctx, args)
        except click.MissingParameter:
            if "--help" not in args:
                raise

            # remove the required params so that help can display
            for param in self.params:
                param.required = False

            return super().parse_args(ctx, args)


HIDE_STATUS: list[str] = list(get_args(TestStatus))
HIDE_STATUS.remove("unset")


@click.group(invoke_without_command=True, cls=IgnoreRequiredWithHelp)
@click.pass_context
@inventory_options
@catalog_options
@click.option(
    "--device",
    "-d",
    help="Run tests on a specific device. Can be provided multiple times.",
    type=str,
    multiple=True,
    required=False,
)
@click.option(
    "--test",
    "-t",
    help="Run a specific test. Can be provided multiple times.",
    type=str,
    multiple=True,
    required=False,
)
@click.option(
    "--ignore-status",
    help="Exit code will always be 0.",
    show_envvar=True,
    is_flag=True,
    default=False,
)
@click.option(
    "--ignore-error",
    help="Exit code will be 0 if all tests succeeded or 1 if any test failed.",
    show_envvar=True,
    is_flag=True,
    default=False,
)
@click.option(
    "--hide",
    default=None,
    type=click.Choice(HIDE_STATUS, case_sensitive=False),
    multiple=True,
    help="Group result by test or device.",
    required=False,
)
@click.option(
    "--dry-run",
    help="Run anta nrfu command but stop before starting to execute the tests. Considers all devices as connected.",
    type=str,
    show_envvar=True,
    is_flag=True,
    default=False,
)
# pylint: disable=too-many-arguments
def nrfu(
    ctx: click.Context,
    inventory: AntaInventory,
    tags: set[str] | None,
    catalog: AntaCatalog,
    device: tuple[str],
    test: tuple[str],
    hide: tuple[str],
    *,
    ignore_status: bool,
    ignore_error: bool,
    dry_run: bool,
) -> None:
    """Run ANTA tests on selected inventory devices."""
    # If help is invoke somewhere, skip the command
    if ctx.obj.get("_anta_help"):
        return
    # We use ctx.obj to pass stuff to the next Click functions
    ctx.ensure_object(dict)
    ctx.obj["result_manager"] = ResultManager()
    ctx.obj["ignore_status"] = ignore_status
    ctx.obj["ignore_error"] = ignore_error
    ctx.obj["hide"] = set(hide) if hide else None
    print_settings(inventory, catalog)
    with anta_progress_bar() as AntaTest.progress:
        asyncio.run(
            main(
                ctx.obj["result_manager"],
                inventory,
                catalog,
                tags=tags,
                devices=set(device) if device else None,
                tests=set(test) if test else None,
                dry_run=dry_run,
            )
        )
    if dry_run:
        return
    # Invoke `anta nrfu table` if no command is passed
    if ctx.invoked_subcommand is None:
        ctx.invoke(commands.table)


nrfu.add_command(commands.table)
nrfu.add_command(commands.json)
nrfu.add_command(commands.text)
nrfu.add_command(commands.tpl_report)
