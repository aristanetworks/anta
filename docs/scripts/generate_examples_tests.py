#!/usr/bin/env python
"""Generates examples/tests.py."""

import os
from contextlib import redirect_stdout
from pathlib import Path

examples_tests_path = Path(__file__).parents[2] / "examples" / "tests.yaml"


prev = os.environ.get("TERM", "")
os.environ["TERM"] = "dumb"
# imported after TERM is set to act upon rich console.
from anta.cli.get.commands import tests  # noqa: E402

with examples_tests_path.open("w") as f:
    f.write("---\n")
    with redirect_stdout(f):
        # removing the style
        tests()

os.environ["TERM"] = prev
