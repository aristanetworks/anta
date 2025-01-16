# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.nrfu.commands."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


def test_anta_nrfu_table_help(click_runner: CliRunner) -> None:
    """Test anta nrfu table --help."""
    result = click_runner.invoke(anta, ["nrfu", "table", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu table" in result.output


def test_anta_nrfu_text_help(click_runner: CliRunner) -> None:
    """Test anta nrfu text --help."""
    result = click_runner.invoke(anta, ["nrfu", "text", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu text" in result.output


def test_anta_nrfu_json_help(click_runner: CliRunner) -> None:
    """Test anta nrfu json --help."""
    result = click_runner.invoke(anta, ["nrfu", "json", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu json" in result.output


def test_anta_nrfu_template_help(click_runner: CliRunner) -> None:
    """Test anta nrfu tpl-report --help."""
    result = click_runner.invoke(anta, ["nrfu", "tpl-report", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu tpl-report" in result.output


def test_anta_nrfu_table(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "table"])
    assert result.exit_code == ExitCode.OK
    assert "leaf1  │ VerifyEOSVersion │ success" in result.output


def test_anta_nrfu_table_group_by_device(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "table", "--group-by", "device"])
    assert result.exit_code == ExitCode.OK
    assert "Summary per device" in result.output


def test_anta_nrfu_table_group_by_test(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "table", "--group-by", "test"])
    assert result.exit_code == ExitCode.OK
    assert "Summary per test" in result.output


def test_anta_nrfu_text(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "text"])
    assert result.exit_code == ExitCode.OK
    assert "leaf1 :: VerifyEOSVersion :: SUCCESS" in result.output


def test_anta_nrfu_text_multiple_failures(click_runner: CliRunner) -> None:
    """Test anta nrfu text with multiple failures, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "text"], env={"ANTA_CATALOG": str(DATA_DIR / "test_catalog_double_failure.yml")})
    assert result.exit_code == ExitCode.TESTS_FAILED
    assert (
        """spine1 :: VerifyInterfacesSpeed :: FAILURE
    Interface `Ethernet2` is not found.
    Interface `Ethernet3` is not found.
    Interface `Ethernet4` is not found."""
        in result.output
    )


def test_anta_nrfu_json(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "json"])
    assert result.exit_code == ExitCode.OK
    assert "JSON results" in result.output
    match = re.search(r"\[\n {2}{[\s\S]+ {2}}\n\]", result.output)
    assert match is not None
    result_list = json.loads(match.group())
    for res in result_list:
        if res["name"] == "leaf1":
            assert res["test"] == "VerifyEOSVersion"
            assert res["result"] == "success"


def test_anta_nrfu_json_output(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu json with output file."""
    json_output = tmp_path / "test.json"
    result = click_runner.invoke(anta, ["nrfu", "json", "--output", str(json_output)])

    # Making sure the output is not printed to stdout
    match = re.search(r"\[\n {2}{[\s\S]+ {2}}\n\]", result.output)
    assert match is None

    assert result.exit_code == ExitCode.OK
    assert "JSON results saved to" in result.output
    assert json_output.exists()


def test_anta_nrfu_json_output_failure(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu json with output file."""
    json_output = tmp_path / "test.json"

    original_open = Path.open

    def mock_path_open(*args: Any, **kwargs: Any) -> Path:  # noqa: ANN401
        """Mock Path.open only for the json_output file of this test."""
        if args[0] == json_output:
            msg = "Simulated OSError"
            raise OSError(msg)

        # If not the json_output file, call the original Path.open
        return original_open(*args, **kwargs)

    with patch("pathlib.Path.open", mock_path_open):
        result = click_runner.invoke(anta, ["nrfu", "json", "--output", str(json_output)])

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Failed to save JSON results to" in result.output
    assert not json_output.exists()


def test_anta_nrfu_template(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "tpl-report", "--template", str(DATA_DIR / "template.j2")])
    assert result.exit_code == ExitCode.OK
    assert "* VerifyEOSVersion is SUCCESS for leaf1" in result.output


def test_anta_nrfu_csv(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu csv."""
    csv_output = tmp_path / "test.csv"
    result = click_runner.invoke(anta, ["nrfu", "csv", "--csv-output", str(csv_output)])
    assert result.exit_code == ExitCode.OK
    assert "CSV report saved to" in result.output
    assert csv_output.exists()


def test_anta_nrfu_csv_failure(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu csv."""
    csv_output = tmp_path / "test.csv"
    with patch("anta.reporter.csv_reporter.ReportCsv.generate", side_effect=OSError()):
        result = click_runner.invoke(anta, ["nrfu", "csv", "--csv-output", str(csv_output)])
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Failed to save CSV report to" in result.output
    assert not csv_output.exists()


def test_anta_nrfu_md_report(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu md-report."""
    md_output = tmp_path / "test.md"
    result = click_runner.invoke(anta, ["nrfu", "md-report", "--md-output", str(md_output)])
    assert result.exit_code == ExitCode.OK
    assert "Markdown report saved to" in result.output
    assert md_output.exists()


def test_anta_nrfu_md_report_failure(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu md-report failure."""
    md_output = tmp_path / "test.md"
    with patch("anta.reporter.md_reporter.MDReportGenerator.generate", side_effect=OSError()):
        result = click_runner.invoke(anta, ["nrfu", "md-report", "--md-output", str(md_output)])

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Failed to save Markdown report to" in result.output
    assert not md_output.exists()


def test_anta_nrfu_md_report_with_hide(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta nrfu md-report with the `--hide` option."""
    md_output = tmp_path / "test.md"
    result = click_runner.invoke(anta, ["nrfu", "--hide", "success", "md-report", "--md-output", str(md_output)])

    assert result.exit_code == ExitCode.OK
    assert "Markdown report saved to" in result.output
    assert md_output.exists()

    with md_output.open("r", encoding="utf-8") as f:
        content = f.read()

    # Use regex to find the "Total Tests Success" value
    match = re.search(r"\| (\d+) \| (\d+) \| \d+ \| \d+ \| \d+ \|", content)

    assert match is not None

    total_tests = int(match.group(1))
    total_tests_success = int(match.group(2))

    assert total_tests == 0
    assert total_tests_success == 0
