# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli._main."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.cli._main import anta, cli
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_anta(click_runner: CliRunner) -> None:
    """Test anta main entrypoint."""
    result = click_runner.invoke(anta)
    assert result.exit_code == ExitCode.OK
    assert "Usage" in result.output


def test_anta_help(click_runner: CliRunner) -> None:
    """Test anta --help."""
    result = click_runner.invoke(anta, ["--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage" in result.output


def test_anta_exec_help(click_runner: CliRunner) -> None:
    """Test anta exec --help."""
    result = click_runner.invoke(anta, ["exec", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta exec" in result.output


def test_anta_debug_help(click_runner: CliRunner) -> None:
    """Test anta debug --help."""
    result = click_runner.invoke(anta, ["debug", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta debug" in result.output


def test_anta_get_help(click_runner: CliRunner) -> None:
    """Test anta get --help."""
    result = click_runner.invoke(anta, ["get", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta get" in result.output


def test_uncaught_failure_anta(caplog: pytest.LogCaptureFixture) -> None:
    """Test uncaught failure when running ANTA cli."""
    with (
        pytest.raises(SystemExit) as e_info,
        patch("anta.cli._main.anta", side_effect=ZeroDivisionError()),
    ):
        cli()
    assert "CRITICAL" in caplog.text
    assert "Uncaught Exception when running ANTA CLI" in caplog.text
    assert e_info.value.code == 1
