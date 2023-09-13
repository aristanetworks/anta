# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""
Commands for Anta CLI to execute EOS commands.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from yaml import safe_load

from anta.cli.exec.utils import clear_counters_utils, collect_commands, collect_scheduled_show_tech
from anta.cli.utils import parse_tags

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
def clear_counters(ctx: click.Context, tags: Optional[list[str]]) -> None:
    """Clear counter statistics on EOS devices"""
    asyncio.run(clear_counters_utils(ctx.obj["inventory"], tags=tags))


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
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
    default=f"anta_snapshot_{datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}",
    show_default=True,
)
def snapshot(ctx: click.Context, tags: Optional[list[str]], commands_list: Path, output: Path) -> None:
    """Collect commands output from devices in inventory"""
    print(f"Collecting data for {commands_list}")
    print(f"Output directory is {output}")
    try:
        with open(commands_list, "r", encoding="UTF-8") as file:
            file_content = file.read()
            eos_commands = safe_load(file_content)
    except FileNotFoundError:
        logger.error(f"Error reading {commands_list}")
        sys.exit(1)
    asyncio.run(collect_commands(ctx.obj["inventory"], eos_commands, output, tags=tags))


@click.command()
@click.pass_context
@click.option("--output", "-o", default="./tech-support", show_default=True, help="Path for tests catalog", type=click.Path(path_type=Path), required=False)
@click.option("--latest", help="Number of scheduled show-tech to retrieve", type=int, required=False)
@click.option(
    "--configure",
    help="Ensure devices have 'aaa authorization exec default local' configured (required for SCP on EOS). THIS WILL CHANGE THE CONFIGURATION OF YOUR NETWORK.",
    default=False,
    is_flag=True,
    show_default=True,
)
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
def collect_tech_support(ctx: click.Context, tags: Optional[list[str]], output: Path, latest: Optional[int], configure: bool) -> None:
    """Collect scheduled tech-support from EOS devices"""
    asyncio.run(collect_scheduled_show_tech(ctx.obj["inventory"], output, configure, tags=tags, latest=latest))
