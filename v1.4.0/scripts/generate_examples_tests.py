#!/usr/bin/env python
# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Generates examples/tests.py."""

import os
from contextlib import redirect_stdout
from pathlib import Path
from sys import path

# Override global path to load anta from pwd instead of any installed version.
path.insert(0, str(Path(__file__).parents[2]))

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
