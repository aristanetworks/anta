# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands that run ANTA tests using anta.runner."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, cast

import click

from anta.cli.nrfu import commands
from anta.cli.utils import AliasedGroup, catalog_options, inventory_options
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class IgnoreRequiredWithHelp(AliasedGroup):
    """Custom Click Group.

    https://stackoverflow.com/questions/55818737/python-click-application-required-parameters-have-precedence-over-sub-command-he

    Solution to allow help without required options on subcommand
    This is not planned to be fixed in click as per: https://github.com/pallets/click/issues/295#issuecomment-708129734.
    """

    @override
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Ignore MissingParameter exception when parsing arguments if `--help` is present for a subcommand."""
        # Adding a flag for potential callbacks
        _: dict[str, Any] = ctx.ensure_object(dict)
        ctx.obj["args"] = args
        if "--help" in args:
            ctx.obj["_anta_help"] = True

        try:
            return super().parse_args(ctx, args)
        except click.MissingParameter:
            if "--help" not in args:
                raise

            # Fake presence of the required params so that help can display
            for param in self.params:
                if param.required:
                    param.value_is_missing = lambda value: False  # type: ignore[method-assign] # noqa: ARG005

            return super().parse_args(ctx, args)


HIDE_STATUS: list[str] = list(AntaTestStatus)
HIDE_STATUS.remove("unset")


def _build_nrfu_command(
    *,
    name: str,
    help_text: str,
    default_catalog_factory: Callable[[], AntaCatalog] | None = None,
    progress_spinner: str = "anta",
) -> click.Group:
    """Build an NRFU command group, optionally with a programmatic default catalog."""

    @click.group(name=name, help=help_text, invoke_without_command=True, cls=IgnoreRequiredWithHelp)
    @inventory_options
    @catalog_options(required=default_catalog_factory is None)
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
        help="Ignore test errors when determining the exit code.",
        show_envvar=True,
        is_flag=True,
        default=False,
    )
    @click.option(
        "--hide",
        default=None,
        type=click.Choice(HIDE_STATUS, case_sensitive=False),
        multiple=True,
        help="Hide results by type: success / inconclusive / failure / error / skipped.",
        required=False,
    )
    @click.option(
        "--dry-run",
        help=f"Run anta {name} command but stop before starting to execute the tests. Considers all devices as connected.",
        type=bool,
        show_envvar=True,
        is_flag=True,
        default=False,
    )
    @click.option(
        "--disconnect/--no-disconnect",
        help="Disconnect inventory devices once the test run is complete.",
        show_envvar=True,
        envvar="ANTA_DISCONNECT_INVENTORY",
        default=True,
        show_default=True,
    )
    @click.pass_context
    def command(
        ctx: click.Context,
        inventory: AntaInventory,
        tags: set[str] | None,
        catalog: AntaCatalog | None,
        device: tuple[str],
        test: tuple[str],
        hide: tuple[str],
        *,
        ignore_status: bool,
        ignore_error: bool,
        dry_run: bool,
        disconnect: bool,
        catalog_format: str = "yaml",
    ) -> None:
        if ctx.obj.get("_anta_help"):
            return

        if catalog is None and default_catalog_factory is not None:
            catalog = default_catalog_factory()
        if catalog is None:
            msg = f"Missing catalog for anta {name}"
            raise RuntimeError(msg)

        _: dict[str, Any] = ctx.ensure_object(dict)
        ctx.obj["result_manager"] = ResultManager()
        ctx.obj["ignore_status"] = ignore_status
        ctx.obj["ignore_error"] = ignore_error
        ctx.obj["hide"] = set(hide) if hide else None
        ctx.obj["catalog"] = catalog
        ctx.obj["catalog_format"] = catalog_format
        ctx.obj["inventory"] = inventory
        ctx.obj["tags"] = tags
        ctx.obj["device"] = device
        ctx.obj["test"] = test
        ctx.obj["dry_run"] = dry_run
        ctx.obj["disconnect"] = disconnect
        ctx.obj["progress_spinner"] = progress_spinner

        if not ctx.invoked_subcommand:
            ctx.invoke(commands.table)

    group = cast("click.Group", command)
    for report_command in (commands.table, commands.csv, commands.json, commands.text, commands.tpl_report, commands.md_report):
        group.add_command(report_command)
    return group


nrfu = _build_nrfu_command(name="nrfu", help_text="Run ANTA tests on selected inventory devices.")
