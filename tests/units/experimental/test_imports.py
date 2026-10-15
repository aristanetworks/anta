# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Verify experimental imports do not interfere with CLI initialization."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("module", ["anta.experimental.cli", "anta.experimental.cli.nrfu"])
def test_experimental_cli_import_order(module: str) -> None:
    """Importing an experimental module first must leave the main CLI usable."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", f"import {module}; from anta.cli import anta; assert 'nrfu' in anta.commands"],
        cwd=Path(__file__).parents[3],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
