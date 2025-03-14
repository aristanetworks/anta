#!/usr/bin/env python
# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Generates SVG for documentation purposes."""

import sys
from pathlib import Path

# TODO: svg in  another PR
from generate_snippet import main as generate_snippet

sys.path.insert(0, str(Path(__file__).parents[2]))

COMMANDS = [
    "anta --help",
    "anta nrfu --help",
    "anta nrfu csv --help",
    "anta nrfu json --help",
    "anta nrfu table --help",
    "anta nrfu text --help",
    "anta nrfu tpl-report --help",
    "anta nrfu md-report --help",
    "anta get tags --help",
]

for command in COMMANDS:
    # TODO: svg in  another PR
    generate_snippet(command.split(" "), output="txt")
