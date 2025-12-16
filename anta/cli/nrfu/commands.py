# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands that render ANTA tests results."""

from __future__ import annotations

import logging
import pathlib
from typing import Literal

import click

from anta.cli.utils import exit_with_code

from .utils import print_jinja, print_json, print_table, print_text, run_tests, save_markdown_report, save_to_csv

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
@click.option(
    "--sort-by",
    default=None,
    type=click.Choice(["name", "test", "categories", "description", "result", "messages"], case_sensitive=False),
    multiple=True,
    help="Sort test results.",
    required=False,
)
@click.option(
    "--expand",
    "-x",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
    help="Flag to indicate if atomic results should be shown.",
)
def table(ctx: click.Context, *, group_by: Literal["device", "test"] | None, sort_by: tuple[str] | None, expand: bool) -> None:
    """ANTA command to check network state with table results."""
    _ = run_tests(ctx)
    print_table(ctx, group_by=group_by, sort_by=sort_by, expand=expand)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=False,
    help="Path to save report as a JSON file",
)
def json(ctx: click.Context, output: pathlib.Path | None) -> None:
    """ANTA command to check network state with JSON results.

    If no `--output` is specified, the output is printed to stdout.
    """
    _ = run_tests(ctx)
    print_json(ctx, output=output)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--expand",
    "-x",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
    help="Flag to indicate if atomic results should be shown.",
)
def text(ctx: click.Context, *, expand: bool) -> None:
    """ANTA command to check network state with text results."""
    _ = run_tests(ctx)
    print_text(ctx, expand=expand)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--csv-output",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=False,
        writable=True,
        path_type=pathlib.Path,
    ),
    show_envvar=True,
    required=True,
    help="Path to save report as a CSV file",
)
def csv(ctx: click.Context, csv_output: pathlib.Path) -> None:
    """ANTA command to check network state with CSV report."""
    _ = run_tests(ctx)
    save_to_csv(ctx, csv_file=csv_output)
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
    _ = run_tests(ctx)
    print_jinja(results=ctx.obj["result_manager"], template=template, output=output)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--md-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save the report as a Markdown file",
)
@click.option(
    "--expand",
    "-x",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
    help="Flag to indicate if atomic results should be shown.",
)
def md_report(ctx: click.Context, md_output: pathlib.Path, *, expand: bool) -> None:
    """ANTA command to check network state with Markdown report."""
    run_context = run_tests(ctx)
    save_markdown_report(ctx, md_output=md_output, run_context=run_context, expand=expand)
    exit_with_code(ctx)
