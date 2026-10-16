# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for experimental NRFU CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner


def test_anta_nrfu_junit_failure(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu junit failure for OS reason."""
    junit_output = tmp_path / "junit.xml"
    with patch("anta.experimental.cli.nrfu.JUnitReporter.generate", side_effect=OSError()):
        result = click_runner.invoke(anta, ["nrfu", "junit", "--junit-output", str(junit_output)])

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Failed to save JUnit report to" in result.output
    assert not junit_output.exists()


def test_anta_nrfu_junit(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu junit."""
    junit_output = tmp_path / "junit.xml"
    result = click_runner.invoke(anta, ["nrfu", "junit", "--junit-output", str(junit_output)])
    assert result.exit_code == ExitCode.OK
    assert result.output.count("WARNING: You are using an experimental ANTA feature: JUnit reporting.") == 1
    assert result.output.index("WARNING:") < result.output.index("Settings")
    assert "JUnit report saved to" in result.output
    assert junit_output.exists()


def test_anta_nrfu_junit_help(click_runner: CliRunner) -> None:
    """Show the experimental status in help without executing the command."""
    result = click_runner.invoke(anta, ["nrfu", "junit", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "[Experimental]" in result.output
    assert "WARNING:" not in result.output


def test_anta_nrfu_junit_dry_run(click_runner: CliRunner, tmp_path: Path) -> None:
    """Warn about experimental reporting even when execution stops after a dry run."""
    junit_output = tmp_path / "junit.xml"
    result = click_runner.invoke(anta, ["nrfu", "--dry-run", "junit", "--junit-output", str(junit_output)])
    assert result.exit_code == ExitCode.OK
    assert "WARNING: You are using an experimental ANTA feature:" in result.output
    assert not junit_output.exists()
