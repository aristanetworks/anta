#!/usr/bin/env python
# coding: utf-8 -*-
"""
Commands for Anta CLI to run nrfu commands.
"""

import logging
import re

import click
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from anta import RICH_COLOR_THEME

from .utils import check_run, display_jinja, display_json, display_table

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
# Generic options
@click.option("--catalog", "-c", show_envvar=True, prompt="Path for tests catalog", help="Path for tests catalog", type=click.Path(), required=True)
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
# Options valid with --display table
@click.option("--search", "-s", default=None, help="Value to search in result. Can be test name or host name", type=str, required=False)
@click.option(
    "--group-by", default=None, type=click.Choice(["none", "host", "test"], case_sensitive=False), help="Group result by test or host. default none", required=False
)
def table(ctx: click.Context, catalog: str, tags: str, group_by: str, search: str) -> None:
    """ANTA command to check network states with table result"""
    # pylint: disable=too-many-arguments
    console = Console()
    inventory = ctx.obj["inventory"]

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(inventory=inventory, catalog=catalog, tags=tags)
    display_table(console=console, results=results, group_by=group_by, search=search)


@click.command()
@click.pass_context
@click.option("--catalog", "-c", show_envvar=True, prompt="Path for tests catalog", help="Path for tests catalog", type=click.Path(), required=True)
@click.option("--tags", "-t", default="all", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
# Options valid with --display json
@click.option("--output", "-o", default=None, help="Path to save output in json or list", type=click.File(), required=False)
def json(ctx: click.Context, catalog: str, output: str, tags: str) -> None:
    """ANTA command to check network state with JSON result"""
    console = Console()
    inventory = ctx.obj["inventory"]

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}",
            title="[green]Settings",
        )
    )

    results = check_run(inventory=inventory, catalog=catalog, tags=tags)
    display_json(console=console, results=results, output_file=output)


@click.command()
@click.pass_context
@click.option("--catalog", "-c", show_envvar=True, prompt="Path for tests catalog", help="Path for tests catalog", type=click.Path(), required=True)
@click.option("--tags", "-t", default="all", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
@click.option("--search", "-s", default=".*", help="Regular expression to search in both name and test", type=str, required=False)
@click.option("--skip-error/--no-skip-error", help="Hide tests in errors due to connectivity issue", default=False, required=False)
def text(ctx: click.Context, catalog: str, tags: str, search: str, skip_error: bool) -> None:
    """ANTA command to check network states with text result"""
    # pylint: disable=too-many-arguments
    custom_theme = Theme(RICH_COLOR_THEME)
    console = Console(theme=custom_theme)
    results = check_run(inventory=ctx.obj["inventory"], catalog=catalog, tags=tags)
    regexp = re.compile(search)
    for line in results.get_results(output_format="list"):
        if any(regexp.match(entry) for entry in [line.name, line.test]) and (not skip_error or line.result != "error"):
            message = f" ({str(line.messages[0])})" if len(line.messages) > 0 else ""
            console.print(f"{line.name} :: {line.test} :: [{line.result}]{line.result.upper()}[/{line.result}]{message}", highlight=False)


@click.command()
@click.pass_context
@click.option("--catalog", "-c", show_envvar=True, prompt="Path for tests catalog", help="Path for tests catalog", type=click.Path(), required=True)
@click.option("--template", "-tpl", type=click.Path(), required=True, help="Path to the template to use for your report")
@click.option("--output", "-o", type=click.Path(), default=None, required=False, help="Path to use to save report")
@click.option("--tags", "-t", default="all", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
def tpl_report(ctx: click.Context, catalog: str, tags: str, template: str, output: str) -> bool:
    # pylint: disable=too-many-arguments
    """ANTA command to check network state with templated report"""
    console = Console()
    inventory = ctx.obj["inventory"]

    results = check_run(inventory=inventory, catalog=catalog, tags=tags)

    # @mtache - TODO
    # if log_level.upper() == "DEBUG":
    #     console.print(Panel.fit("List results of all tests", style="red"))
    #     console.print(results.get_results(output_format="json"))

    console.print(
        Panel.fit(
            f"Running check-devices with:\n\
              - Inventory: {inventory}\n\
              - Tests catalog: {catalog}\n\
              - Template: {template}",
            style="cyan",
            title="[green]Settings",
        )
    )

    display_jinja(console=console, results=results, template=template, output=output)

    return True
