# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.debug."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.cli._main import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_anta_debug(click_runner: CliRunner) -> None:
    """Test anta debug."""
    result = click_runner.invoke(anta, ["debug"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta debug" in result.output


def test_anta_debug_help(click_runner: CliRunner) -> None:
    """Test anta debug --help."""
    result = click_runner.invoke(anta, ["debug", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta debug" in result.output
