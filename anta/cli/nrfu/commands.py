# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Click commands that render ANTA tests results
"""
from __future__ import annotations

import logging
import pathlib

import click

from anta.cli.utils import exit_with_code

from .utils import print_jinja, print_json, print_table, print_text

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option("--device", "-d", help="Show a summary for this device", type=str, required=False)
@click.option("--test", "-t", help="Show a summary for this test", type=str, required=False)
@click.option(
    "--group-by", default=None, type=click.Choice(["device", "test"], case_sensitive=False), help="Group result by test or host. default none", required=False
)
def table(ctx: click.Context, device: str | None, test: str | None, group_by: str) -> None:
    """ANTA command to check network states with table result"""
    print_table(results=ctx.obj["result_manager"], device=device, group_by=group_by, test=test)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=False,
    help="Path to save report as a file",
)
def json(ctx: click.Context, output: pathlib.Path | None) -> None:
    """ANTA command to check network state with JSON result"""
    print_json(results=ctx.obj["result_manager"], output=output)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option("--search", "-s", help="Regular expression to search in both name and test", type=str, required=False)
@click.option("--skip-error", help="Hide tests in errors due to connectivity issue", default=False, is_flag=True, show_default=True, required=False)
def text(ctx: click.Context, search: str | None, skip_error: bool) -> None:
    """ANTA command to check network states with text result"""
    print_text(results=ctx.obj["result_manager"], search=search, skip_error=skip_error)
    exit_with_code(ctx)


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
def tpl_report(ctx: click.Context, template: pathlib.Path, output: pathlib.Path | None) -> None:
    """ANTA command to check network state with templated report"""
    print_jinja(results=ctx.obj["result_manager"], template=template, output=output)
    exit_with_code(ctx)
