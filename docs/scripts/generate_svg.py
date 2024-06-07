# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""A script to generate svg files from anta command.

usage:

python generate_svg.py anta ...
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
from unittest.mock import patch

from rich.console import Console
from rich.logging import RichHandler

from anta.cli.console import console
from anta.cli.nrfu.utils import anta_progress_bar

root = logging.getLogger()

r = RichHandler(console=console)
root.addHandler(r)


OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "imgs"


def custom_progress_bar() -> None:
    """Set the console of progress_bar to main anta console.

    Caveat: this capture all steps of the progress bar..
    Disabling refresh to only capture beginning and end
    """
    progress = anta_progress_bar()
    progress.live.auto_refresh = False
    progress.live.console = console
    return progress


if __name__ == "__main__":
    # Sane rich size
    os.environ["COLUMNS"] = "120"

    # stolen from https://github.com/ewels/rich-click/blob/main/src/rich_click/cli.py
    args = sys.argv[1:]
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

    # Console to captur everything
    new_console = Console(record=True)

    pipe = io.StringIO()
    console.record = True
    console.file = pipe
    with redirect_stdout(io.StringIO()) as f:
        # tweaks to record and redirect to a dummy file

        console.print(f"ant@anthill$ {' '.join(sys.argv)}")

        # Redirect stdout of the program towards another StringIO to capture help
        # that is not part or anta rich console
        # redirect potential progress bar output to console by patching
        with patch("anta.cli.nrfu.anta_progress_bar", custom_progress_bar), suppress(SystemExit):
            function()

    if "--help" in args:
        console.print(f.getvalue())

    filename = f"{'_'.join(x.replace('/', '_').replace('-', '_').replace('.', '_') for x in args)}.svg"
    filename = f"{OUTPUT_DIR}/{filename}"
    print(f"File saved at {filename}")
    console.save_svg(filename, title=" ".join(args))
