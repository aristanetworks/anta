# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils functions to use with anta.cli.nrfu.commands module."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import rich
from rich.panel import Panel
from rich.pretty import pprint
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from anta.cli.console import console
from anta.reporter import ReportJinja, ReportTable

if TYPE_CHECKING:
    import pathlib

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory
    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


def print_settings(
    inventory: AntaInventory,
    catalog: AntaCatalog,
) -> None:
    """Print ANTA settings before running tests."""
    message = f"Running ANTA tests:\n- {inventory}\n- Tests catalog contains {len(catalog.tests)} tests"
    console.print(Panel.fit(message, style="cyan", title="[green]Settings"))
    console.print()


def print_table(results: ResultManager, group_by: str | None = None) -> None:
    """Print result in a table."""
    reporter = ReportTable()
    console.print()

    if group_by == "device":
        console.print(reporter.report_summary_hosts(result_manager=results, host=None))
    elif group_by == "test":
        console.print(reporter.report_summary_tests(result_manager=results, testcase=None))
    else:
        console.print(reporter.report_all(result_manager=results))


def print_json(results: ResultManager, output: pathlib.Path | None = None) -> None:
    """Print result in a json format."""
    console.print()
    console.print(Panel("JSON results of all tests", style="cyan"))
    rich.print_json(results.get_json_results())
    if output is not None:
        with output.open(mode="w", encoding="utf-8") as fout:
            fout.write(results.get_json_results())


def print_list(results: ResultManager, output: pathlib.Path | None = None) -> None:
    """Print result in a list."""
    console.print()
    console.print(Panel.fit("List results of all tests", style="cyan"))
    pprint(results.get_results())
    if output is not None:
        with output.open(mode="w", encoding="utf-8") as fout:
            fout.write(str(results.get_results()))


def print_text(results: ResultManager, *, skip_error: bool = False, skip_failure: bool = False, skip_success: bool = False) -> None:
    """Print results as simple text."""
    console.print()
    for line in results.get_results():
        if not (skip_error and "error" in line.result) and not (skip_failure and "failure" in line.result) and not (skip_success and "success" in line.result):
            message = f" ({line.messages[0]!s})" if len(line.messages) > 0 else ""
            console.print(f"{line.name} :: {line.test} :: [{line.result}]{line.result.upper()}[/{line.result}]{message}", highlight=False)


def print_jinja(results: ResultManager, template: pathlib.Path, output: pathlib.Path | None = None) -> None:
    """Print result based on template."""
    console.print()
    reporter = ReportJinja(template_path=template)
    json_data = json.loads(results.get_json_results())
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
