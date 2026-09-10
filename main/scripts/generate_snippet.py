#!/usr/bin/env python
# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""A script to generate svg or txt files from anta command.

usage:

python generate_snippet.py [--format {svg,txt}] [--max-results MAX_RESULTS] [--max-lines MAX_LINES] anta ...
"""
# This script contains print statements
# ruff: noqa: T201

import argparse
import io
import logging
import os
import pathlib
import re
import sys
from contextlib import redirect_stdout, suppress
from importlib import import_module
from importlib.metadata import entry_points
from typing import Literal
from unittest.mock import patch

import click
from rich.logging import RichHandler
from rich.markup import escape
from rich.progress import Progress
from rich.text import Text

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from anta.cli.console import console
from anta.cli.nrfu import commands as nrfu_commands
from anta.cli.nrfu.utils import anta_progress_bar
from anta.result_manager import ResultManager

root = logging.getLogger()

r = RichHandler(console=console)
root.addHandler(r)

SNAPSHOT_OUTPUT_PATTERN = re.compile(r"anta_snapshot_\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}")


def positive_integer(value: str) -> int:
    """Parse a strictly positive integer."""
    parsed_value = int(value)
    if parsed_value <= 0:
        msg = "must be greater than zero"
        raise argparse.ArgumentTypeError(msg)
    return parsed_value


def parse_args(args: list[str] | None = None) -> tuple[list[str], Literal["svg", "txt"], int | None, int | None]:
    """Parse the snippet generator command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("svg", "txt"), default="svg", dest="output_format", help="Output format (default: svg).")
    parser.add_argument("--max-results", type=positive_integer, help="Maximum number of ANTA results to include in rendered reports.")
    parser.add_argument("--max-lines", type=positive_integer, help="Maximum number of terminal output lines to include.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="ANTA command and arguments to capture.")
    parsed_args = parser.parse_args(args)
    if not parsed_args.command:
        parser.error("an ANTA command is required")
    return parsed_args.command, parsed_args.output_format, parsed_args.max_results, parsed_args.max_lines


def limit_result_manager(manager: ResultManager, max_results: int | None) -> tuple[ResultManager, int]:
    """Return a result manager limited to the requested number of results."""
    if max_results is None or len(manager) <= max_results:
        return manager, 0

    limited_manager = ResultManager()
    limited_manager.results = manager.results[:max_results]
    return limited_manager, len(manager) - max_results


def format_omitted_results(count: int) -> str:
    """Format the message shown when results are omitted."""
    result_label = "result" if count == 1 else "results"
    return f"... {count} {result_label} omitted ..."


def normalize_svg_whitespace(svg_path: pathlib.Path) -> None:
    """Remove trailing horizontal whitespace emitted by Rich without changing SVG rendering."""
    content = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE), encoding="utf-8")


def limit_console_lines(max_lines: int | None) -> None:
    """Limit recorded console output while preserving ANSI styles and the final status line."""
    if max_lines is None:
        return

    rendered_output = console.export_text(clear=True, styles=True)
    output_lines = rendered_output.splitlines()
    if len(output_lines) <= max_lines:
        console.print(Text.from_ansi(rendered_output), end="")
        return

    head_count = max(max_lines - 1, 0)
    omitted_lines = len(output_lines) - head_count - 1
    line_label = "line" if omitted_lines == 1 else "lines"
    if head_count:
        console.print(Text.from_ansi("\n".join(output_lines[:head_count])))
    console.print(f"\n[dim]... {omitted_lines} {line_label} omitted ...[/]\n")
    console.print(Text.from_ansi(output_lines[-1]))


def finalize_console_output(max_lines: int | None, omitted_results: int) -> None:
    """Apply line truncation, then append result-omission metadata."""
    limit_console_lines(max_lines)
    if omitted_results:
        console.print(f"\n[dim]{format_omitted_results(omitted_results)}[/]")


def custom_progress_bar() -> Progress:
    """Set the console of progress_bar to main anta console.

    Caveat: this capture all steps of the progress bar..
    Disabling refresh to only capture beginning and end
    """
    progress = anta_progress_bar()
    progress.live.auto_refresh = False
    progress.live.console = console
    return progress


def main(args: list[str], output: Literal["svg", "txt"] = "svg", max_results: int | None = None, max_lines: int | None = None) -> None:
    """Execute the script."""
    # Sane rich size
    os.environ["COLUMNS"] = "120"

    output_dir = pathlib.Path(__file__).parent.parent / "snippets" if output == "txt" else pathlib.Path(__file__).parent.parent / "imgs"

    # stolen from https://github.com/ewels/rich-click/blob/main/src/rich_click/cli.py
    script_name = args[0]
    console_scripts = entry_points(group="console_scripts")
    scripts = {script.name: script for script in console_scripts}

    if script_name in scripts:
        # A VALID SCRIPT WAS passed
        script = scripts[script_name]
        module_path, function_name = script.value.split(":", 1)
        prog = script_name
    elif ":" in script_name:
        # the path to a function was passed
        module_path, function_name = args[0].split(":", 1)
        prog = module_path.split(".", 1)[0]
    else:
        print("This is supposed to be used with anta only")
        print("Usage: python generate_svg.py anta <options>")
        sys.exit(1)

    # possibly-used-before-assignment - prog / function_name -> not understanding sys.exit here...
    # pylint: disable=E0606
    sys.argv = [prog, *args[1:]]
    module = import_module(module_path)
    function = getattr(module, function_name)

    omitted_results = 0
    original_run_tests = nrfu_commands.run_tests

    def run_tests_and_limit_results(ctx: click.Context) -> object:
        """Run the tests and apply the snippet limit before rendering."""
        nonlocal omitted_results
        run_context = original_run_tests(ctx)
        limited_manager, omitted_results = limit_result_manager(ctx.obj["result_manager"], max_results)
        ctx.obj["result_manager"] = limited_manager
        return run_context

    pipe = io.StringIO()
    console.record = True
    console.file = pipe
    # Redirect stdout of the program towards another StringIO to capture help
    # that is not part or anta rich console
    # redirect potential progress bar output to console by patching
    with (
        redirect_stdout(io.StringIO()) as f,
        patch("anta.cli.nrfu.utils.anta_progress_bar", custom_progress_bar),
        patch("anta.cli.nrfu.commands.run_tests", run_tests_and_limit_results),
        suppress(SystemExit),
    ):
        if output == "txt":
            console.print(f"$ {' '.join(sys.argv)}")
        function()

    if "--help" in args:
        console.print(escape(f.getvalue()))

    finalize_console_output(max_lines, omitted_results)

    filename = f"{'_'.join(x.replace('/', '_').replace('-', '').replace('.', '') for x in args)}.{output}"
    filename = output_dir / filename
    if output == "txt":
        content = SNAPSHOT_OUTPUT_PATTERN.sub("anta_snapshot_<date>_<time>", console.export_text()[:-1])
        with filename.open("w") as fd:
            fd.write(content)
        # TODO: Not using this to avoid newline console.save_text(str(filename))
    elif output == "svg":
        console.save_svg(str(filename), title=" ".join(args))
        normalize_svg_whitespace(filename)

    print(f"File saved at {filename}")


if __name__ == "__main__":
    command, output_format, parsed_max_results, parsed_max_lines = parse_args()
    main(command, output_format, parsed_max_results, parsed_max_lines)
