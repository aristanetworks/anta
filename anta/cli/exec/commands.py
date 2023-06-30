#!/usr/bin/env python
# coding: utf-8 -*-

"""
Commands for Anta CLI to execute EOS commands.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from yaml import safe_load

from anta.cli.exec.utils import clear_counters_utils, collect_commands, collect_scheduled_show_tech
from anta.cli.utils import parse_tags

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
def clear_counters(ctx: click.Context, tags: Optional[List[str]]) -> None:
    """Clear counter statistics on EOS devices"""
    asyncio.run(clear_counters_utils(ctx.obj["inventory"], tags=tags))


def _get_snapshot_dir(ctx: click.Context, param: click.Parameter, value: str) -> Path:  # pylint: disable=unused-argument
    """Build directory name for command snapshots, including current time"""
    return Path(f"{value}_{datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}")


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
    type=click.Path(file_okay=False, dir_okay=True, exists=False, writable=True),
    help="Directory to save commands output. Will have a suffix with the format _YEAR-MONTH-DAY_HOUR-MINUTES-SECONDS'",
    default="anta_snapshot",
    show_default=True,
    callback=_get_snapshot_dir,
)
def snapshot(ctx: click.Context, tags: Optional[List[str]], commands_list: Path, output: Path) -> None:
    """Collect commands output from devices in inventory"""
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
    "--configure/--not-configure", help="Ensure device has 'aaa authorization exec default local' configured (required for SCP)", default=False, show_default=True
)
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False, callback=parse_tags)
def collect_tech_support(ctx: click.Context, tags: Optional[List[str]], output: Path, latest: Optional[int], configure: bool) -> None:
    """Collect scheduled tech-support from EOS devices"""
    asyncio.run(collect_scheduled_show_tech(ctx.obj["inventory"], output, configure, tags=tags, latest=latest))
