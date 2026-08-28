# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Run the built-in ANTA security advisory catalog."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import click

from anta._advisory.reporter.reporting import (
    SecurityAdvisoryReport,
    SecurityAdvisoryReportConfig,
    generate_security_advisory_csv_report,
    generate_security_advisory_md_report,
)
from anta.cli.console import console
from anta.cli.nrfu import _build_nrfu_command
from anta.cli.nrfu.utils import _get_result_manager, run_tests
from anta.cli.utils import ExitCode, exit_with_code
from anta.tests.advisories import get_catalog

if TYPE_CHECKING:
    from anta.catalog import AntaCatalog


def _load_default_catalog() -> AntaCatalog:
    """Load the complete built-in advisory catalog at invocation time."""
    return get_catalog()


def _build_advisory_report(ctx: click.Context, *, allow_empty: bool = False) -> SecurityAdvisoryReport:
    """Build a security advisory report from the visible test results."""
    return SecurityAdvisoryReport.from_result_manager(_get_result_manager(ctx), allow_empty=allow_empty)


@click.command(name="csv")
@click.pass_context
@click.option(
    "--csv-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save the security advisory report as a CSV file",
)
def _csv(ctx: click.Context, csv_output: pathlib.Path) -> None:
    """Generate a detailed security advisory CSV report."""
    _ = run_tests(ctx)
    try:
        generate_security_advisory_csv_report(_build_advisory_report(ctx), csv_output)
    except (OSError, ValueError) as error:
        console.print(f"Failed to save security advisory CSV report to {csv_output}: {error} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)

    console.print(f"Security advisory CSV report saved to {csv_output} ✅", style="cyan")
    exit_with_code(ctx)


@click.command(name="md-report")
@click.pass_context
@click.option(
    "--md-output",
    type=click.Path(file_okay=True, dir_okay=False, exists=False, writable=True, path_type=pathlib.Path),
    show_envvar=True,
    required=True,
    help="Path to save the security advisory report as a Markdown file",
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
def _md_report(ctx: click.Context, md_output: pathlib.Path, *, expand: bool) -> None:
    """Generate a detailed security advisory Markdown report."""
    run_context = run_tests(ctx)
    config = SecurityAdvisoryReportConfig(expand_results=expand)
    try:
        report = _build_advisory_report(ctx, allow_empty=True)
        generate_security_advisory_md_report(report, md_output, run_context, config)
    except (OSError, ValueError) as error:
        console.print(f"Failed to save security advisory Markdown report to {md_output}: {error} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)

    console.print(f"Security advisory Markdown report saved to {md_output} ✅", style="cyan")
    exit_with_code(ctx)


psirt = _build_nrfu_command(
    name="psirt",
    help_text=(
        "[PREVIEW] Run ANTA tests for Arista security advisories. This command is a preview feature; its interface and behavior may change at any time without a "
        "deprecation notice."
    ),
    default_catalog_factory=_load_default_catalog,
)
# Override the generic NRFU commands registered by the factory with the
# security-advisory-specific reporters under the same Click command names.
psirt.add_command(_csv)
psirt.add_command(_md_report)


__all__ = ["psirt"]
