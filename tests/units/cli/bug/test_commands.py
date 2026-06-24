# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Integration tests for anta.cli.bug commands.

Tests the full CLI flow with mocked eAPI, covering:
- Database loading and parsing
- Device connection and SysDB queries via Acons
- Tag resolution (hardware + feature)
- Bug matching and report generation
- All output formats (table, json, csv, md-report)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"
ALERTBASE_PATH: str = str(DATA_DIR / "test_alertbase.json")


# ──────────────────────────────────────────────────────────────────────
# Help tests
# ──────────────────────────────────────────────────────────────────────


def test_anta_bug_help(click_runner: CliRunner) -> None:
    """Test anta bug --help."""
    result = click_runner.invoke(anta, ["bug", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Check inventory devices against the Arista bug database" in result.output


def test_anta_bug_table_help(click_runner: CliRunner) -> None:
    """Test anta bug table --help."""
    result = click_runner.invoke(anta, ["bug", "table", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta bug table" in result.output


def test_anta_bug_json_help(click_runner: CliRunner) -> None:
    """Test anta bug json --help."""
    result = click_runner.invoke(anta, ["bug", "json", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta bug json" in result.output


def test_anta_bug_csv_help(click_runner: CliRunner) -> None:
    """Test anta bug csv --help."""
    result = click_runner.invoke(anta, ["bug", "csv", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta bug csv" in result.output


def test_anta_bug_md_report_help(click_runner: CliRunner) -> None:
    """Test anta bug md-report --help."""
    result = click_runner.invoke(anta, ["bug", "md-report", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta bug md-report" in result.output


# ──────────────────────────────────────────────────────────────────────
# Integration tests with mocked eAPI
# ──────────────────────────────────────────────────────────────────────


def test_anta_bug_table(click_runner: CliRunner) -> None:
    """Test anta bug table end-to-end with mocked eAPI."""
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "table"])
    assert result.exit_code == ExitCode.OK
    assert "Bug Compliance Summary" in result.output
    # The mock device is DCS-7280CR3-32P4-F / 4.31.1F — should match bugs 1002 (version-only)
    assert "1002" in result.output


def test_anta_bug_table_default(click_runner: CliRunner) -> None:
    """Test anta bug without subcommand defaults to table."""
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH])
    assert result.exit_code == ExitCode.OK
    assert "Bug Compliance Summary" in result.output


def test_anta_bug_json(click_runner: CliRunner) -> None:
    """Test anta bug json output."""
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "json"])
    assert result.exit_code == ExitCode.OK
    # The JSON output should be parseable — find the JSON array in the output
    # The click_runner output includes Rich markup, so we look for the key fields
    assert "device" in result.output
    assert "hw_model" in result.output


def test_anta_bug_json_to_file(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta bug json with file output."""
    output_file = tmp_path / "bug_report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert isinstance(data, list)
    assert len(data) > 0
    report = data[0]
    assert "device" in report
    assert "hw_model" in report
    assert "eos_version" in report
    assert "resolved_tags" in report
    assert "bugs" in report


def test_anta_bug_csv(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta bug csv output."""
    csv_file = tmp_path / "bug_report.csv"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "csv", "--csv-output", str(csv_file)])
    assert result.exit_code == ExitCode.OK
    assert csv_file.exists()
    content = csv_file.read_text()
    assert "Device,Model,EOS Version,Bug ID" in content


def test_anta_bug_md_report(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test anta bug md-report output."""
    md_file = tmp_path / "bug_report.md"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "md-report", "--md-output", str(md_file)])
    assert result.exit_code == ExitCode.OK
    assert md_file.exists()
    content = md_file.read_text()
    assert "# ANTA Bug Compliance Report" in content
    assert "## Summary" in content


def test_anta_bug_severity_filter(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test severity filtering — only sev1 bugs."""
    output_file = tmp_path / "sev1_report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "--severity", "sev1", "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    data = json.loads(output_file.read_text())
    for report in data:
        for bug in report["bugs"]:
            assert bug["severity"] == "sev1"


def test_anta_bug_device_filter(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test device name filtering."""
    output_file = tmp_path / "filtered_report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "-d", "leaf1", "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    data = json.loads(output_file.read_text())
    assert all(r["device"] == "leaf1" for r in data)


def test_anta_bug_no_database(click_runner: CliRunner) -> None:
    """Test error when neither --token nor --bug-database is provided."""
    result = click_runner.invoke(anta, ["bug", "table"])
    assert result.exit_code != ExitCode.OK
    assert "Either --token or --bug-database" in result.output


def test_anta_bug_json_report_structure(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test the structure of the JSON report matches expected schema."""
    output_file = tmp_path / "report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    data = json.loads(output_file.read_text())

    for report in data:
        assert isinstance(report["device"], str)
        assert isinstance(report["hw_model"], str)
        assert isinstance(report["eos_version"], str)
        assert isinstance(report["resolved_tags"], list)
        assert isinstance(report["bugs"], list)
        for bug in report["bugs"]:
            assert isinstance(bug["bug_id"], int)
            assert bug["severity"] in {"sev1", "sev2", "sev3", "sev4"}
            assert isinstance(bug["alert_summary"], str)
            assert isinstance(bug["version_fixed"], list)
            assert isinstance(bug["matched_by"], str)


def test_anta_bug_hardware_tag_resolution(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test that hardware tags are resolved from model name via tagImplication.

    The mock device model is DCS-7280CR3-32P4-F which doesn't match the test
    alertbase tagImplication (which has 7280CR3K). This verifies that the tag
    resolution correctly handles partial matches.
    """
    output_file = tmp_path / "tags_report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    data = json.loads(output_file.read_text())
    assert len(data) > 0
    # At minimum, the device model itself should be in tags
    for report in data:
        assert report["hw_model"] in report["resolved_tags"]


def test_anta_bug_version_matching(click_runner: CliRunner, tmp_path: Path) -> None:
    """Test that version matching works correctly.

    The mock device runs 4.31.1F. Test alertbase has:
    - Bug 1002: introduced 4.28.0, fixed 4.35.5 → SHOULD match (version-only)
    - Bug 1004: introduced 4.30.0, fixed 4.35.4 → SHOULD match (4.31.1 < 4.35.4)
    - Bug 1005: product=cvp → SHOULD NOT match
    """
    output_file = tmp_path / "version_report.json"
    result = click_runner.invoke(anta, ["bug", "-b", ALERTBASE_PATH, "json", "-o", str(output_file)])
    assert result.exit_code == ExitCode.OK
    data = json.loads(output_file.read_text())

    # Collect all matched bug IDs across all devices
    matched_ids = set()
    for report in data:
        for bug in report["bugs"]:
            matched_ids.add(bug["bug_id"])

    # Version-only bugs should match
    assert 1002 in matched_ids, "Bug 1002 (version-only, 4.28-4.35.5) should match device on 4.31.1F"
    assert 1004 in matched_ids, "Bug 1004 (version-only, 4.30-4.35.4) should match device on 4.31.1F"
    # Non-EOS bug should not match
    assert 1005 not in matched_ids, "Bug 1005 (product=cvp) should not match"
