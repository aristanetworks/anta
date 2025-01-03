# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.check."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.cli._main import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_anta_check(click_runner: CliRunner) -> None:
    """Test anta check."""
    result = click_runner.invoke(anta, ["check"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta check" in result.output


def test_anta_check_help(click_runner: CliRunner) -> None:
    """Test anta check --help."""
    result = click_runner.invoke(anta, ["check", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta check" in result.output
