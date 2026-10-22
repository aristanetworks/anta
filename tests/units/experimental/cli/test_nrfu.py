# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for experimental NRFU CLI commands."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.cli import anta
from anta.cli.utils import ExitCode
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus, TestResult

if TYPE_CHECKING:
    from pathlib import Path

    import click
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
    assert "--hide is ignored" not in result.output
    assert "JUnit report saved to" in result.output
    assert junit_output.exists()


@pytest.mark.parametrize("hidden_statuses", [("success",), ("failure",), ("error",), ("skipped",), ("success", "failure", "error", "skipped")])
def test_anta_nrfu_junit_ignores_hide(click_runner: CliRunner, tmp_path: Path, hidden_statuses: tuple[str, ...]) -> None:
    """Keep every outcome in the XML and preserve the exit code when --hide is supplied."""
    manager = ResultManager()
    for status in AntaTestStatus:
        manager.add(TestResult(name="leaf1", test=f"Verify_{status}", categories=["system"], description="Test status", result=status))

    def populate_results(ctx: click.Context) -> None:
        ctx.obj["result_manager"] = manager

    junit_output = tmp_path / "junit.xml"
    hide_options = [argument for status in hidden_statuses for argument in ("--hide", status)]
    with patch("anta.cli.nrfu.utils.run_tests", side_effect=populate_results):
        result = click_runner.invoke(anta, ["nrfu", *hide_options, "junit", "--junit-output", str(junit_output)])

    assert result.exit_code == ExitCode.TESTS_ERROR
    assert result.output.count("WARNING: --hide is ignored for JUnit reporting; all results are included.") == 1
    root = ET.parse(junit_output).getroot()  # noqa: S314
    assert root.get("tests") == "5"
    assert root.get("failures") == "1"
    assert root.get("errors") == "2"
    assert root.get("skipped") == "1"
    assert {case.get("name") for case in root.findall("./testsuite/testcase")} == {f"Verify_{status} - Test status" for status in AntaTestStatus}
    assert len(root.findall("./testsuite/testcase/error")) == 2
    assert len(root.findall("./testsuite/testcase/failure")) == 1
    assert len(root.findall("./testsuite/testcase/skipped")) == 1


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
