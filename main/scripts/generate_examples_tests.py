#!/usr/bin/env python
# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Generates examples/tests.py."""

import os
from contextlib import redirect_stdout
from pathlib import Path
from sys import path

from yaml import YAMLError

# Override global path to load anta from pwd instead of any installed version.
path.insert(0, str(Path(__file__).parents[2]))

from anta.catalog import AntaCatalog

examples_tests_path = Path(__file__).parents[2] / "examples" / "tests.yaml"


prev = os.environ.get("TERM", "")
os.environ["TERM"] = "dumb"
# imported after TERM is set to act upon rich console.
from anta.cli.get.commands import tests  # noqa: E402

try:
    with examples_tests_path.open("w") as f:
        f.write("---\n")
        with redirect_stdout(f):
            # removing the style
            tests()
except SystemExit:
    pass

os.environ["TERM"] = prev

try:
    _ = AntaCatalog.parse(examples_tests_path)
except (TypeError, ValueError, YAMLError, OSError) as e:
    msg = f"Failed to parse catalog: {e}"
    raise ValueError(msg) from None
