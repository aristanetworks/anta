# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.nrfu.commands module."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Literal

import rich
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from anta.cli.console import console
from anta.reporter import ReportJinja, ReportTable

if TYPE_CHECKING:
    import pathlib

    import click

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


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
    """Print result in a json format."""
    results = _get_result_manager(ctx)
    console.print()
    console.print(Panel("JSON results", style="cyan"))
    rich.print_json(results.json)
    if output is not None:
        with output.open(mode="w", encoding="utf-8") as fout:
            fout.write(results.json)


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
