#!/usr/bin/env python
# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""A script to generate svg or txt files from anta command.

usage:

python generate_snippet.py anta ...
"""
# This script is not a package
# ruff: noqa: INP001
# This script contains print statements
# ruff: noqa: T201

import io
import logging
import os
import pathlib
import sys
from contextlib import redirect_stdout, suppress
from importlib import import_module
from importlib.metadata import entry_points
from typing import Literal
from unittest.mock import patch

from rich.logging import RichHandler
from rich.markup import escape
from rich.progress import Progress

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from anta.cli.console import console
from anta.cli.nrfu.utils import anta_progress_bar

root = logging.getLogger()

r = RichHandler(console=console)
root.addHandler(r)


def custom_progress_bar() -> Progress:
    """Set the console of progress_bar to main anta console.

    Caveat: this capture all steps of the progress bar..
    Disabling refresh to only capture beginning and end
    """
    progress = anta_progress_bar()
    progress.live.auto_refresh = False
    progress.live.console = console
    return progress


def main(args: list[str], output: Literal["svg", "txt"] = "svg") -> None:
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

    pipe = io.StringIO()
    console.record = True
    console.file = pipe
    # Redirect stdout of the program towards another StringIO to capture help
    # that is not part or anta rich console
    # redirect potential progress bar output to console by patching
    with redirect_stdout(io.StringIO()) as f, patch("anta.cli.nrfu.utils.anta_progress_bar", custom_progress_bar), suppress(SystemExit):
        if output == "txt":
            console.print(f"$ {' '.join(sys.argv)}")
        function()

    if "--help" in args:
        console.print(escape(f.getvalue()))

    filename = f"{'_'.join(x.replace('/', '_').replace('-', '').replace('.', '') for x in args)}.{output}"
    filename = output_dir / filename
    if output == "txt":
        content = console.export_text()[:-1]
        with filename.open("w") as fd:
            fd.write(content)
        # TODO: Not using this to avoid newline console.save_text(str(filename))
    elif output == "svg":
        console.save_svg(str(filename), title=" ".join(args))

    print(f"File saved at {filename}")


if __name__ == "__main__":
    main(sys.argv[1:], "txt")
