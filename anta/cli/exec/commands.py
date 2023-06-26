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

import click
from yaml import safe_load

from anta.cli.exec.utils import clear_counters_utils, collect_commands, collect_scheduled_show_tech
from anta.inventory.models import DEFAULT_TAG

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option("--tags", "-t", default="all", help="List of tags using coma as separator: tag1,tag2,tag3", type=str)
def clear_counters(ctx: click.Context, tags: str) -> None:
    """Clear counter statistics on EOS devices"""
    asyncio.run(clear_counters_utils(ctx.obj["inventory"], tags=tags.split(",")))


def _get_snapshot_dir(ctx: click.Context, param: click.Parameter, value: str) -> str:  # pylint: disable=unused-argument
    """Build directory name for command snapshots, including current time"""
    return f"{value}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"


@click.command()
@click.pass_context
@click.option("--tags", "-t", default=DEFAULT_TAG, help="List of tags using coma as separator: tag1,tag2,tag3", type=str)
@click.option("--commands-list", "-c", show_envvar=True, type=click.Path(), help="File with list of commands to grab", required=True)
@click.option(
    "--output-directory",
    "-output",
    "-o",
    show_envvar=True,
    type=click.Path(),
    help="Path where to save commands output",
    default="anta_snapshot",
    callback=_get_snapshot_dir,
)
def snapshot(ctx: click.Context, commands_list: str, output_directory: str, tags: str) -> None:
    """Collect commands output from devices in inventory"""
    try:
        with open(commands_list, "r", encoding="UTF-8") as file:
            file_content = file.read()
            eos_commands = safe_load(file_content)
    except FileNotFoundError:
        logger.error(f"Error reading {commands_list}")
        sys.exit(1)
    asyncio.run(collect_commands(ctx.obj["inventory"], eos_commands, output_directory, tags=tags.split(",")))


@click.command()
@click.pass_context
@click.option("--output", "-o", default="./tech-support", show_default=True, help="Path for tests catalog", type=click.Path(path_type=Path), required=False)
@click.option("--latest", help="Number of scheduled show-tech to retrieve", type=int, required=False)
@click.option(
    "--configure/--not-configure",
    help="Ensure device has 'aaa authorization exec default local' configured (required for SCP)",
    default=False,
    show_default=True,
    required=False,
)
@click.option("--tags", "-t", default=DEFAULT_TAG, help="List of tags using coma as separator: tag1,tag2,tag3", type=str, required=False)
def collect_tech_support(ctx: click.Context, output: Path, latest: int, configure: bool, tags: str) -> None:
    """Collect scheduled tech-support from EOS devices"""
    asyncio.run(collect_scheduled_show_tech(ctx.obj["inventory"], output, tags.split(","), latest, configure))
