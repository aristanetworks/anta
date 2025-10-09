# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands to execute various scripts on EOS devices."""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import click
from yaml import safe_load

from anta.cli.console import console
from anta.cli.exec import utils
from anta.cli.utils import inventory_options

if TYPE_CHECKING:
    from anta.inventory import AntaInventory

logger = logging.getLogger(__name__)


@click.command
@inventory_options
def clear_counters(inventory: AntaInventory, tags: set[str] | None) -> None:
    """Clear counter statistics on EOS devices."""
    asyncio.run(utils.clear_counters(inventory, tags=tags))


@click.command()
@inventory_options
@click.option(
    "--commands-list",
    "-c",
    help="File with list of commands to collect",
    required=True,
    show_envvar=True,
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=Path),
)
@click.option(
    "--output",
    "-o",
    show_envvar=True,
    type=click.Path(file_okay=False, dir_okay=True, exists=False, writable=True, path_type=Path),
    help="Directory to save commands output.",
    default=f"anta_snapshot_{datetime.now(tz=timezone.utc).astimezone().strftime('%Y-%m-%d_%H_%M_%S')}",
    show_default=True,
)
def snapshot(inventory: AntaInventory, tags: set[str] | None, commands_list: Path, output: Path) -> None:
    """Collect commands output from devices in inventory."""
    console.print(f"Collecting data for {commands_list}")
    console.print(f"Output directory is {output}")
    try:
        with commands_list.open(encoding="UTF-8") as file:
            file_content = file.read()
            # TODO: currently not checking if the format of the file is correct.
            eos_commands: dict[str, list[str]] = safe_load(file_content)
    except FileNotFoundError:
        logger.error("Error reading %s", commands_list)
        sys.exit(1)
    asyncio.run(utils.collect_commands(inventory, eos_commands, output, tags=tags))


@click.command()
@inventory_options
@click.option(
    "--output",
    "-o",
    default="./tech-support",
    show_default=True,
    help="Path for test catalog",
    type=click.Path(path_type=Path),
    required=False,
)
@click.option(
    "--latest",
    help="Number of scheduled show-tech to retrieve",
    type=int,
    required=False,
)
@click.option(
    "--configure",
    help=(
        "[DEPRECATED] Ensure devices have 'aaa authorization exec default local' configured (required for SCP on EOS). "
        "THIS WILL CHANGE THE CONFIGURATION OF YOUR NETWORK."
    ),
    default=False,
    is_flag=True,
    show_default=True,
)
def collect_tech_support(
    inventory: AntaInventory,
    tags: set[str] | None,
    output: Path,
    latest: int | None,
    *,
    configure: bool,
) -> None:
    """Collect scheduled tech-support from EOS devices."""
    asyncio.run(utils.collect_show_tech(inventory, output, configure=configure, tags=tags, latest=latest))
