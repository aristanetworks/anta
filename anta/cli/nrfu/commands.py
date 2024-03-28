# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands that render ANTA tests results."""

from __future__ import annotations

import logging
import pathlib
from typing import Literal

import click

from anta.cli.utils import exit_with_code

from .utils import print_jinja, print_json, print_table, print_text

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@click.option(
    "--group-by",
    default=None,
    type=click.Choice(["device", "test"], case_sensitive=False),
    help="Group result by test or device.",
    required=False,
)
def table(
    ctx: click.Context,
    group_by: Literal["device", "test"] | None,
) -> None:
    """ANTA command to check network states with table result."""
    print_table(ctx, group_by=group_by)
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
    """ANTA command to check network state with JSON result."""
    print_json(ctx, output=output)
    exit_with_code(ctx)


@click.command()
@click.pass_context
def text(ctx: click.Context) -> None:
    """ANTA command to check network states with text result."""
    print_text(ctx)
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
    """ANTA command to check network state with templated report."""
    print_jinja(results=ctx.obj["result_manager"], template=template, output=output)
    exit_with_code(ctx)
