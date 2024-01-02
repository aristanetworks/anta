# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.get
"""
from __future__ import annotations

from click.testing import CliRunner

from anta.cli import anta
from anta.cli.utils import ExitCode


def test_anta_get(click_runner: CliRunner) -> None:
    """
    Test anta get
    """
    result = click_runner.invoke(anta, ["get"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta get" in result.output


def test_anta_get_help(click_runner: CliRunner) -> None:
    """
    Test anta get --help
    """
    result = click_runner.invoke(anta, ["get", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta get" in result.output
