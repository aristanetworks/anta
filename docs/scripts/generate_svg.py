"""
"""

import io
import os
import sys
from contextlib import redirect_stdout, suppress
from importlib import import_module
from importlib.metadata import entry_points
from unittest.mock import patch

from anta.cli.console import console
from anta.cli.nrfu.utils import anta_progress_bar


def custom_progress_bar():
    """
    Set the console of progress_bar to main anta console

    Caveat: this capture all steps of the progress bar..
    Disabling refresh to only capture beginning and end
    """
    progress = anta_progress_bar()
    progress.live.auto_refresh = False
    progress.live.console = console
    return progress


if __name__ == "__main__":
    # Sane rich size
    os.environ["COLUMNS"] = "165"

    # stolen from https://github.com/ewels/rich-click/blob/main/src/rich_click/cli.py
    args = sys.argv[1:]
    script_name = "anta"
    scripts = {script.name: script for script in entry_points().get("console_scripts")}

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

    sys.argv = [prog, *args[1:]]
    module = import_module(module_path)
    function = getattr(module, function_name)

    # Record what is happening in ANTA console
    console.record = True

    # redirect potential progress bar output to console by patching
    with patch("anta.cli.nrfu.commands.anta_progress_bar", custom_progress_bar):
        with suppress(SystemExit):
            function()

    console.save_svg("command.svg", title=" ".join(args))
