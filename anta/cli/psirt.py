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
from anta._advisory.reporter.table_reporter import SecurityAdvisoryReportTable
from anta._advisory.results import _get_advisory_metadata
from anta.cli.console import console
from anta.cli.nrfu import _build_nrfu_command
from anta.cli.nrfu.utils import _get_result_manager, run_tests
from anta.cli.utils import ExitCode, exit_with_code
from anta.reporter.table_reporter import ReportTable
from anta.result_manager import ResultManager
from anta.tests.advisories import get_catalog

if TYPE_CHECKING:
    from anta.catalog import AntaCatalog


def _load_default_catalog() -> AntaCatalog:
    """Load the complete built-in advisory catalog at invocation time."""
    return get_catalog()


def _build_advisory_report(ctx: click.Context, *, allow_empty: bool = False) -> SecurityAdvisoryReport:
    """Build a security advisory report from the visible test results."""
    return SecurityAdvisoryReport.from_result_manager(_get_result_manager(ctx), allow_empty=allow_empty)


def _partition_results(manager: ResultManager) -> tuple[ResultManager, ResultManager]:
    """Partition visible results into advisory and ordinary result managers."""
    advisory_results = ResultManager()
    ordinary_results = ResultManager()
    for result in manager.results:
        target = advisory_results if _get_advisory_metadata(result) is not None else ordinary_results
        target.add(result)
    return advisory_results, ordinary_results


@click.command(name="table")
@click.pass_context
@click.option(
    "--summary-only",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
    help="Only show summary tables.",
)
@click.option(
    "--expand",
    "-x",
    default=False,
    show_envvar=True,
    is_flag=True,
    show_default=True,
    help="Show atomic findings in the per-device table.",
)
def _table(ctx: click.Context, *, summary_only: bool, expand: bool) -> None:
    """Render security advisory summary and per-device tables."""
    if summary_only and expand:
        message = "--summary-only and --expand cannot be used together."
        raise click.UsageError(message)

    _ = run_tests(ctx)
    visible_results = _get_result_manager(ctx)
    advisory_results, ordinary_results = _partition_results(visible_results)
    console.print()

    if advisory_results.results:
        try:
            report = SecurityAdvisoryReport.from_result_manager(advisory_results)
        except ValueError as error:
            console.print(f"Failed to generate security advisory table report: {error} ❌", style="cyan")
            ctx.exit(ExitCode.USAGE_ERROR)
        reporter = SecurityAdvisoryReportTable()
        console.print(reporter.generate_summary(report))
        if not summary_only:
            console.print(reporter.generate_device_findings(report, expand_results=expand))

    if ordinary_results.results:
        reporter = ReportTable()
        if summary_only:
            console.print(reporter.generate_summary_by_test(ordinary_results))
        elif expand:
            console.print(reporter.generate_expanded(ordinary_results))
        else:
            console.print(reporter.generate(ordinary_results))

    if not visible_results.results:
        console.print("No results to display.", style="cyan")

    exit_with_code(ctx)


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
    default_report_command=_table,
)
# Override the generic NRFU commands registered by the factory with the
# security-advisory-specific reporters under the same Click command names.
psirt.add_command(_csv)
psirt.add_command(_md_report)
psirt.add_command(_table)


__all__ = ["psirt"]
