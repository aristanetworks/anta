# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Experimental CLI commands for NRFU reports."""

from __future__ import annotations

import pathlib

import click

from anta.experimental.cli import warn_experimental
from anta.experimental.reporter.junit_reporter import JUnitReporter


@click.command()
@click.pass_context
@click.option(
    "--junit-output",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=False,
        writable=True,
        path_type=pathlib.Path,
    ),
    show_envvar=True,
    required=True,
    help="Path to save report as a JUnit file",
)
def junit(ctx: click.Context, junit_output: pathlib.Path) -> None:
    """[Experimental] Check network state with a JUnit report.

    Includes all results regardless of the NRFU --hide option.
    """
    # Defer stable CLI imports until command registration has completed.
    from anta.cli.nrfu.utils import run_tests  # noqa: PLC0415
    from anta.cli.utils import exit_with_code  # noqa: PLC0415

    warn_experimental("JUnit reporting")
    _ = run_tests(ctx)
    save_to_junit(ctx, junit_file=junit_output)
    exit_with_code(ctx)


def save_to_junit(ctx: click.Context, junit_file: pathlib.Path) -> None:
    """Save results to a JUnit file."""
    from anta.cli.console import console  # noqa: PLC0415
    from anta.cli.nrfu.utils import _get_result_manager  # noqa: PLC0415
    from anta.cli.utils import ExitCode  # noqa: PLC0415

    if ctx.obj.get("hide"):
        console.print("WARNING: --hide is ignored for JUnit reporting; all results are included.", style="yellow")

    try:
        JUnitReporter.generate(results=_get_result_manager(ctx, apply_hide_filter=False), output_path=junit_file)
        console.print(f"JUnit report saved to {junit_file} ✅", style="cyan")
    except OSError:
        console.print(f"Failed to save JUnit report to {junit_file} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)
    except ValueError as exc:
        console.print(f"Failed to save JUnit report to {junit_file} ❌", style="cyan")
        console.print(str(exc), markup=False, style="red")
        ctx.exit(ExitCode.USAGE_ERROR)
