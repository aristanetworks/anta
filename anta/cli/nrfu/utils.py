# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.nrfu.commands module."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Literal

import rich
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from anta.cli.console import console
from anta.cli.utils import ExitCode
from anta.models import AntaTest
from anta.reporter import ReportJinja, ReportTable
from anta.reporter.csv_reporter import ReportCsv
from anta.reporter.md_reporter import MDReportGenerator
from anta.runner import main

if TYPE_CHECKING:
    import pathlib

    import click

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


def run_tests(ctx: click.Context) -> None:
    """Run the tests."""
    # Digging up the parameters from the parent context
    if ctx.parent is None:
        ctx.exit()
    nrfu_ctx_params = ctx.parent.params
    tags = nrfu_ctx_params["tags"]
    device = nrfu_ctx_params["device"] or None
    test = nrfu_ctx_params["test"] or None
    dry_run = nrfu_ctx_params["dry_run"]

    catalog = ctx.obj["catalog"]
    inventory = ctx.obj["inventory"]

    print_settings(inventory, catalog)
    with anta_progress_bar() as AntaTest.progress:
        asyncio.run(
            main(
                ctx.obj["result_manager"],
                inventory,
                catalog,
                tags=tags,
                devices=set(device) if device else None,
                tests=set(test) if test else None,
                dry_run=dry_run,
            )
        )
    if dry_run:
        ctx.exit()


def _get_result_manager(ctx: click.Context) -> ResultManager:
    """Get a ResultManager instance based on Click context."""
    return ctx.obj["result_manager"].filter(ctx.obj.get("hide")) if ctx.obj.get("hide") is not None else ctx.obj["result_manager"]


def print_settings(
    inventory: AntaInventory,
    catalog: AntaCatalog,
) -> None:
    """Print ANTA settings before running tests."""
    message = f"- {inventory}\n- Tests catalog contains {len(catalog.tests)} tests"
    console.print(Panel.fit(message, style="cyan", title="[green]Settings"))
    console.print()


def print_table(ctx: click.Context, group_by: Literal["device", "test"] | None = None) -> None:
    """Print result in a table."""
    reporter = ReportTable()
    console.print()
    results = _get_result_manager(ctx)

    if group_by == "device":
        console.print(reporter.report_summary_devices(results))
    elif group_by == "test":
        console.print(reporter.report_summary_tests(results))
    else:
        console.print(reporter.report_all(results))


def print_json(ctx: click.Context, output: pathlib.Path | None = None) -> None:
    """Print results as JSON. If output is provided, save to file instead."""
    results = _get_result_manager(ctx)

    if output is None:
        console.print()
        console.print(Panel("JSON results", style="cyan"))
        rich.print_json(results.json)
    else:
        try:
            with output.open(mode="w", encoding="utf-8") as file:
                file.write(results.json)
            console.print(f"JSON results saved to {output} ✅", style="cyan")
        except OSError:
            console.print(f"Failed to save JSON results to {output} ❌", style="cyan")
            ctx.exit(ExitCode.USAGE_ERROR)


def print_text(ctx: click.Context) -> None:
    """Print results as simple text."""
    console.print()
    for test in _get_result_manager(ctx).results:
        message = f" ({test.messages[0]!s})" if len(test.messages) > 0 else ""
        console.print(f"{test.name} :: {test.test} :: [{test.result}]{test.result.upper()}[/{test.result}]{message}", highlight=False)


def print_jinja(results: ResultManager, template: pathlib.Path, output: pathlib.Path | None = None) -> None:
    """Print result based on template."""
    console.print()
    reporter = ReportJinja(template_path=template)
    json_data = json.loads(results.json)
    report = reporter.render(json_data)
    console.print(report)
    if output is not None:
        with output.open(mode="w", encoding="utf-8") as file:
            file.write(report)


def save_to_csv(ctx: click.Context, csv_file: pathlib.Path) -> None:
    """Save results to a CSV file."""
    try:
        ReportCsv.generate(results=_get_result_manager(ctx), csv_filename=csv_file)
        console.print(f"CSV report saved to {csv_file} ✅", style="cyan")
    except OSError:
        console.print(f"Failed to save CSV report to {csv_file} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)


def save_markdown_report(ctx: click.Context, md_output: pathlib.Path) -> None:
    """Save the markdown report to a file.

    Parameters
    ----------
    ctx
        Click context containing the result manager.
    md_output
        Path to save the markdown report.
    """
    try:
        MDReportGenerator.generate(results=_get_result_manager(ctx), md_filename=md_output)
        console.print(f"Markdown report saved to {md_output} ✅", style="cyan")
    except OSError:
        console.print(f"Failed to save Markdown report to {md_output} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)


# Adding our own ANTA spinner - overriding rich SPINNERS for our own
# so ignore warning for redefinition
rich.spinner.SPINNERS = {  # type: ignore[attr-defined]
    "anta": {
        "interval": 150,
        "frames": [
            "(     🐜)",
            "(    🐜 )",
            "(   🐜  )",
            "(  🐜   )",
            "( 🐜    )",
            "(🐜     )",
            "(🐌     )",
            "( 🐌    )",
            "(  🐌   )",
            "(   🐌  )",
            "(    🐌 )",
            "(     🐌)",
        ],
    },
}


def anta_progress_bar() -> Progress:
    """Return a customized Progress for progress bar."""
    return Progress(
        SpinnerColumn("anta"),
        TextColumn("•"),
        TextColumn("{task.description}[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        expand=True,
    )
