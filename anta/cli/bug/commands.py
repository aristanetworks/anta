# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands for bug compliance report output formats."""

from __future__ import annotations

import pathlib

import click

from .utils import print_bug_json, print_bug_table, run_bug_analysis, save_bug_csv, save_bug_markdown


@click.command()
@click.pass_context
def table(ctx: click.Context) -> None:
    """Display bug compliance results in table format."""
    reports = run_bug_analysis(ctx)
    print_bug_table(reports)


@click.command()
@click.pass_context
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=False,
    help="Path to save report as a JSON file.",
)
def json(ctx: click.Context, output: pathlib.Path | None) -> None:
    """Display bug compliance results in JSON format."""
    reports = run_bug_analysis(ctx)
    print_bug_json(reports, output=output)


@click.command()
@click.pass_context
@click.option(
    "--csv-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save report as a CSV file.",
)
def csv(ctx: click.Context, csv_output: pathlib.Path) -> None:
    """Save bug compliance results as a CSV file."""
    reports = run_bug_analysis(ctx)
    save_bug_csv(reports, csv_file=csv_output)


@click.command()
@click.pass_context
@click.option(
    "--md-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save report as a Markdown file.",
)
def md_report(ctx: click.Context, md_output: pathlib.Path) -> None:
    """Save bug compliance results as a Markdown file."""
    reports = run_bug_analysis(ctx)
    save_bug_markdown(reports, md_file=md_output)
