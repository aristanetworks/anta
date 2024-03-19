# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Click commands that render ANTA tests results."""

from __future__ import annotations

import logging
import pathlib

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
    help="Group result by test or host. default none",
    required=False,
)
@click.option(
    "--skip-error",
    help="Hide tests in errors due to connectivity issue",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
@click.option(
    "--skip-failure",
    help="Hide tests in failure",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
@click.option(
    "--skip-success",
    help="Hide tests in success to focus on error or failure",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
def table(
    ctx: click.Context,
    group_by: str,
    *,
    skip_error: bool,
    skip_failure: bool,
    skip_success: bool,
) -> None:
    """ANTA command to check network states with table result."""
    if skip_error:
        ignore_state = "error"
    elif skip_failure:
        ignore_state = "failure"
    elif skip_success:
        ignore_state = "success"
    else:
        ignore_state = None

    print_table(results=ctx.obj["result_manager"], group_by=group_by, ignore_state=ignore_state)
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
    print_json(results=ctx.obj["result_manager"], output=output)
    exit_with_code(ctx)


@click.command()
@click.pass_context
@click.option(
    "--skip-error",
    help="Hide tests in errors due to connectivity issue",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
@click.option(
    "--skip-failure",
    help="Hide tests in failure",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
@click.option(
    "--skip-success",
    help="Hide tests in success to focus on error or failure",
    default=False,
    is_flag=True,
    show_default=True,
    required=False,
)
def text(ctx: click.Context, *, skip_error: bool, skip_failure: bool, skip_success: bool) -> None:
    """ANTA command to check network states with text result."""
    print_text(
        results=ctx.obj["result_manager"],
        skip_error=skip_error,
        skip_failure=skip_failure,
        skip_success=skip_success,
    )
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
