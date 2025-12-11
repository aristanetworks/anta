# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.nrfu.commands module."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Literal

from rich._spinners import SPINNERS
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from anta import __version__ as anta_version
from anta._runner import AntaRunContext, AntaRunFilters, AntaRunner
from anta.cli.console import console
from anta.cli.utils import ExitCode
from anta.models import AntaTest
from anta.reporter import ReportJinja, ReportTable
from anta.reporter.csv_reporter import ReportCsv
from anta.reporter.md_reporter import MDReportGenerator

if TYPE_CHECKING:
    import pathlib

    import click

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


def run_tests(ctx: click.Context) -> AntaRunContext:
    """Run the tests."""
    # Digging up the parameters from the parent context
    if ctx.parent is None:
        ctx.exit()
    nrfu_ctx_params = ctx.parent.params
    tags = nrfu_ctx_params["tags"]
    device = nrfu_ctx_params["device"] or None
    test = nrfu_ctx_params["test"] or None
    dry_run = nrfu_ctx_params["dry_run"]

    catalog: AntaCatalog = ctx.obj["catalog"]
    inventory: AntaInventory = ctx.obj["inventory"]

    print_settings(inventory, catalog)
    with anta_progress_bar() as AntaTest.progress:
        runner = AntaRunner()
        filters = AntaRunFilters(
            devices=set(device) if device else None,
            tests=set(test) if test else None,
            tags=tags,
        )
        run_ctx = asyncio.run(runner.run(inventory=inventory, catalog=catalog, result_manager=ctx.obj["result_manager"], filters=filters, dry_run=dry_run))

    if dry_run:
        ctx.exit()

    return run_ctx


def _get_result_manager(ctx: click.Context, *, apply_hide_filter: bool = True) -> ResultManager:
    """Get a ResultManager instance based on Click context."""
    if apply_hide_filter:
        return ctx.obj["result_manager"].filter(ctx.obj.get("hide")) if ctx.obj.get("hide") is not None else ctx.obj["result_manager"]
    return ctx.obj["result_manager"]


def print_settings(
    inventory: AntaInventory,
    catalog: AntaCatalog,
) -> None:
    """Print ANTA settings before running tests."""
    message = f"- {inventory}\n- Tests catalog contains {len(catalog.tests)} tests"
    console.print(Panel.fit(message, style="cyan", title="[green]Settings"))
    console.print()


def print_table(
    ctx: click.Context,
    *,
    expand: bool,
    group_by: Literal["device", "test"] | None = None,
    sort_by: tuple[str] | None = None,
) -> None:
    """Print result in a table."""
    reporter = ReportTable()
    console.print()
    results = _get_result_manager(ctx)
    if sort_by:
        results = _get_result_manager(ctx).sort(list(sort_by))

    if group_by == "device":
        console.print(reporter.generate_summary_by_device(results))
    elif group_by == "test":
        console.print(reporter.generate_summary_by_test(results))
    elif expand:
        console.print(reporter.generate_expanded(results))
    else:
        console.print(reporter.generate(results))


def print_json(ctx: click.Context, output: pathlib.Path | None = None) -> None:
    """Print results as JSON. If output is provided, save to file instead."""
    results = _get_result_manager(ctx)

    if output is None:
        console.print()
        console.print(Panel("JSON results", style="cyan"))
        console.print_json(results.json)
    else:
        try:
            with output.open(mode="w", encoding="utf-8") as file:
                file.write(results.json)
            console.print(f"JSON results saved to {output} ✅", style="cyan")
        except OSError:
            console.print(f"Failed to save JSON results to {output} ❌", style="cyan")
            ctx.exit(ExitCode.USAGE_ERROR)


def print_text(ctx: click.Context, *, expand: bool) -> None:
    """Print results as simple text."""
    console.print()
    for result in _get_result_manager(ctx).results:
        console.print(f"{result.name} :: {result.test} :: [{result.result}]{result.result.upper()}[/{result.result}]", highlight=False)
        if expand:
            for r in result.atomic_results:
                console.print(f"    {r.description} :: [{r.result}]{r.result.upper()}[/{r.result}]", highlight=False)
                if r.messages:
                    console.print("\n".join(f"      {message}" for message in r.messages), highlight=False)
        elif result.messages:
            console.print("\n".join(f"    {message}" for message in result.messages), highlight=False)


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


def save_markdown_report(ctx: click.Context, md_output: pathlib.Path, run_context: AntaRunContext | None = None, *, expand: bool = False) -> None:
    """Save the markdown report to a file.

    Parameters
    ----------
    ctx
        Click context containing the result manager.
    md_output
        Path to save the markdown report.
    run_context
        Optional `AntaRunContext` instance returned from `AntaRunner.run()`.
        If provided, a `Run Overview` section will be generated in the report including the run context information.
    expand
        Expand atomic results in the report "Test Results" section.
    """
    # TODO: Add support for `render_custom_field` in the CLI
    extra_data: dict[str, Any] = {"_report_options": {"expand_results": expand}}
    if run_context is not None:
        active_filters_dict = {}
        if run_context.filters.tags:
            active_filters_dict["tags"] = sorted(run_context.filters.tags)
        if run_context.filters.tests:
            active_filters_dict["tests"] = sorted(run_context.filters.tests)
        if run_context.filters.devices:
            active_filters_dict["devices"] = sorted(run_context.filters.devices)

        extra_data.update(
            {
                "anta_version": anta_version,
                "test_execution_start_time": run_context.start_time,
                "test_execution_end_time": run_context.end_time,
                "total_duration": run_context.duration,
                "total_devices_in_inventory": run_context.total_devices_in_inventory,
                "devices_unreachable_at_setup": run_context.devices_unreachable_at_setup,
                "devices_filtered_at_setup": run_context.devices_filtered_at_setup,
                "filters_applied": active_filters_dict if active_filters_dict else None,
            }
        )

        if run_context.warnings_at_setup:
            extra_data["warnings_at_setup"] = run_context.warnings_at_setup

    try:
        manager = _get_result_manager(ctx, apply_hide_filter=False).sort(["name", "categories", "test"])
        filtered_manager = _get_result_manager(ctx, apply_hide_filter=True).sort(["name", "categories", "test"])
        sections = [(section, filtered_manager) if section.__name__ == "TestResults" else (section, manager) for section in MDReportGenerator.DEFAULT_SECTIONS]
        MDReportGenerator.generate_sections(md_filename=md_output, sections=sections, extra_data=extra_data)
        console.print(f"Markdown report saved to {md_output} ✅", style="cyan")
    except OSError:
        console.print(f"Failed to save Markdown report to {md_output} ❌", style="cyan")
        ctx.exit(ExitCode.USAGE_ERROR)


# Adding our own ANTA spinner
SPINNERS["anta"] = {
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
