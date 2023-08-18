#!/usr/bin/env python
# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# coding: utf-8 -*-

"""
Utils functions to use with anta.cli.check.commands module.
"""

import json
import logging
import pathlib
import re
from typing import Optional

import click
import rich
from rich.panel import Panel
from rich.pretty import pprint
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from anta.cli.console import console
from anta.reporter import ReportJinja, ReportTable
from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


def print_settings(context: click.Context, report_template: Optional[pathlib.Path] = None, report_output: Optional[pathlib.Path] = None) -> None:
    """Print ANTA settings before running tests"""
    message = f"Running ANTA tests:\n- {context.obj['inventory']}\n- Tests catalog contains {len(context.obj['catalog'])} tests"
    if report_template:
        message += f"\n- Report template: {report_template}"
    if report_output:
        message += f"\n- Report output: {report_output}"
    console.print(Panel.fit(message, style="cyan", title="[green]Settings"))
    console.print()


def print_table(results: ResultManager, device: Optional[str] = None, test: Optional[str] = None, group_by: Optional[str] = None) -> None:
    """Print result in a table"""
    reporter = ReportTable()
    console.print()
    if device:
        console.print(reporter.report_all(result_manager=results, host=device))
    elif test:
        console.print(reporter.report_all(result_manager=results, testcase=test))
    elif group_by == "device":
        console.print(reporter.report_summary_hosts(result_manager=results, host=None))
    elif group_by == "test":
        console.print(reporter.report_summary_tests(result_manager=results, testcase=None))
    else:
        console.print(reporter.report_all(result_manager=results))


def print_json(results: ResultManager, output: Optional[pathlib.Path] = None) -> None:
    """Print result in a json format"""
    console.print()
    console.print(Panel("JSON results of all tests", style="cyan"))
    rich.print_json(results.get_results(output_format="json"))
    if output is not None:
        with open(output, "w", encoding="utf-8") as fout:
            fout.write(results.get_results(output_format="json"))


def print_list(results: ResultManager, output: Optional[pathlib.Path] = None) -> None:
    """Print result in a list"""
    console.print()
    console.print(Panel.fit("List results of all tests", style="cyan"))
    pprint(results.get_results(output_format="list"))
    if output is not None:
        with open(output, "w", encoding="utf-8") as fout:
            fout.write(str(results.get_results(output_format="list")))


def print_text(results: ResultManager, search: Optional[str] = None, skip_error: bool = False) -> None:
    """Print results as simple text"""
    console.print()
    regexp = re.compile(search if search else ".*")
    for line in results.get_results(output_format="list"):
        if any(regexp.match(entry) for entry in [line.name, line.test]) and (not skip_error or line.result != "error"):
            message = f" ({str(line.messages[0])})" if len(line.messages) > 0 else ""
            console.print(f"{line.name} :: {line.test} :: [{line.result}]{line.result.upper()}[/{line.result}]{message}", highlight=False)


def print_jinja(results: ResultManager, template: pathlib.Path, output: Optional[pathlib.Path] = None) -> None:
    """Print result based on template."""
    console.print()
    reporter = ReportJinja(template_path=template)
    json_data = json.loads(results.get_results(output_format="json"))
    report = reporter.render(json_data)
    console.print(report)
    if output is not None:
        with open(output, "w", encoding="utf-8") as file:
            file.write(report)


# Adding our own ANTA spinner - overriding rich SPINNERS for our own
# so ignore warning for redefinition
rich.spinner.SPINNERS = {  # type: ignore[attr-defined] # noqa: F811
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
    }
}


def anta_progress_bar() -> Progress:
    """
    Return a customized Progress for progress bar
    """
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
