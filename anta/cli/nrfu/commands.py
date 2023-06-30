#!/usr/bin/env python
# coding: utf-8 -*-
"""
Commands for Anta CLI to run nrfu commands.
"""

import logging
import pathlib
from typing import Optional

import click

from .utils import check_run, print_jinja, print_json, print_settings, print_table, print_text

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
@click.option("--device", "-d", help="Show a summary for this device", type=str, required=False)
@click.option("--test", "-t", help="Show a summary for this test", type=str, required=False)
def table(ctx: click.Context, tags: Optional[str], device: Optional[str], test: Optional[str]) -> None:
    """ANTA command to check network states with table result"""
    print_settings(ctx)
    results = check_run(inventory=ctx.obj["inventory"], catalog=ctx.obj["catalog"], tags=tags)
    print_table(results=results, device=device, test=test)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=False,
    help="Path to save report as a file",
)
def json(ctx: click.Context, tags: Optional[str], output: Optional[pathlib.Path]) -> None:
    """ANTA command to check network state with JSON result"""
    print_settings(ctx)
    results = check_run(inventory=ctx.obj["inventory"], catalog=ctx.obj["catalog"], tags=tags)
    print_json(results=results, output=output)


@click.command()
@click.pass_context
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
@click.option("--search", "-s", help="Regular expression to search in both name and test", type=str, required=False)
@click.option("--skip-error/--no-skip-error", help="Hide tests in errors due to connectivity issue", default=False, show_default=True, required=False)
def text(ctx: click.Context, tags: Optional[str], search: Optional[str], skip_error: bool) -> None:
    """ANTA command to check network states with text result"""
    print_settings(ctx)
    results = check_run(inventory=ctx.obj["inventory"], catalog=ctx.obj["catalog"], tags=tags)
    print_text(results=results, search=search, skip_error=skip_error)


@click.command()
@click.pass_context
@click.option(
    "--template",
    "-tpl",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to the template to use for the report",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=False,
    help="Path to save report as a file",
)
@click.option("--tags", "-t", help="List of tags using comma as separator: tag1,tag2,tag3", type=str, required=False)
def tpl_report(ctx: click.Context, tags: Optional[str], template: pathlib.Path, output: Optional[pathlib.Path]) -> None:
    """ANTA command to check network state with templated report"""
    print_settings(ctx, template, output)
    results = check_run(inventory=ctx.obj["inventory"], catalog=ctx.obj["catalog"], tags=tags)
    print_jinja(results=results, template=template, output=output)
