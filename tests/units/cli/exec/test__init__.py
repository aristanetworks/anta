# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.exec."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_anta_exec(click_runner: CliRunner) -> None:
    """Test anta exec."""
    result = click_runner.invoke(anta, ["exec"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta exec" in result.output


def test_anta_exec_help(click_runner: CliRunner) -> None:
    """Test anta exec --help."""
    result = click_runner.invoke(anta, ["exec", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta exec" in result.output
