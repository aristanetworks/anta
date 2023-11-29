# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.__init__
"""

from __future__ import annotations

from click.testing import CliRunner

from anta.cli import anta
from anta.cli.utils import ExitCode


def test_anta(click_runner: CliRunner) -> None:
    """
    Test anta main entrypoint
    """
    result = click_runner.invoke(anta)
    assert result.exit_code == ExitCode.OK
    assert "Usage" in result.output


def test_anta_help(click_runner: CliRunner) -> None:
    """
    Test anta --help
    """
    result = click_runner.invoke(anta, ["--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage" in result.output


def test_anta_nrfu_help(click_runner: CliRunner) -> None:
    """
    Test anta nrfu --help
    """
    result = click_runner.invoke(anta, ["nrfu", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu" in result.output


def test_anta_exec_help(click_runner: CliRunner) -> None:
    """
    Test anta exec --help
    """
    result = click_runner.invoke(anta, ["exec", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta exec" in result.output


def test_anta_debug_help(click_runner: CliRunner) -> None:
    """
    Test anta debug --help
    """
    result = click_runner.invoke(anta, ["debug", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta debug" in result.output


def test_anta_get_help(click_runner: CliRunner) -> None:
    """
    Test anta get --help
    """
    result = click_runner.invoke(anta, ["get", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta get" in result.output
