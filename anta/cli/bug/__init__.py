# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands for ANTA bug compliance analysis."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from anta.cli.bug import commands
from anta.cli.nrfu import IgnoreRequiredWithHelp
from anta.cli.utils import inventory_options

if TYPE_CHECKING:
    from anta.inventory import AntaInventory


@click.group(invoke_without_command=True, cls=IgnoreRequiredWithHelp)
@inventory_options
@click.option(
    "--token",
    help="Arista.com API token for downloading the bug database.",
    envvar="ANTA_BUG_TOKEN",
    show_envvar=True,
    type=str,
    required=False,
)
@click.option(
    "--bug-database",
    "-b",
    help="Path to a local AlertBase-CVP.json file.",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
    envvar="ANTA_BUG_DATABASE",
    show_envvar=True,
    required=False,
)
@click.option(
    "--severity",
    help="Minimum severity filter (sev1 is highest).",
    type=click.Choice(["sev1", "sev2", "sev3"], case_sensitive=False),
    default=None,
    required=False,
)
@click.option(
    "--device",
    "-d",
    help="Run analysis on a specific device. Can be provided multiple times.",
    type=str,
    multiple=True,
    required=False,
)
@click.option(
    "--target-version",
    "-t",
    help="Target EOS version to evaluate upgrade impact (e.g. 4.36.0F).",
    type=str,
    required=False,
)
@click.pass_context
def bug(
    ctx: click.Context,
    inventory: AntaInventory,
    tags: set[str] | None,
    token: str | None,
    bug_database: Path | None,
    severity: str | None,
    device: tuple[str],
    target_version: str | None,
) -> None:
    """Check inventory devices against the Arista bug database."""
    if ctx.obj.get("_anta_help"):
        return

    _: dict[str, Any] = ctx.ensure_object(dict)
    ctx.obj["inventory"] = inventory
    ctx.obj["tags"] = tags
    ctx.obj["token"] = token
    ctx.obj["bug_database"] = bug_database
    ctx.obj["severity"] = severity
    ctx.obj["device"] = device
    ctx.obj["target_version"] = target_version

    if not ctx.invoked_subcommand:
        ctx.invoke(commands.table)


bug.add_command(commands.table)
bug.add_command(commands.json)
bug.add_command(commands.csv)
bug.add_command(commands.md_report)
