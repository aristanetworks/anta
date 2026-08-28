# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the ``anta psirt`` command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from anta._advisory.reporter.reporting import SecurityAdvisoryReportConfig
from anta.catalog import AntaCatalog
from anta.cli import anta
from anta.cli.utils import ExitCode
from anta.result_manager import ResultManager

if TYPE_CHECKING:
    from click.testing import CliRunner

DATA_DIR: Path = Path(__file__).parents[2].resolve() / "data"


def test_anta_psirt_help(click_runner: CliRunner) -> None:
    """Expose the built-in PSIRT command and its report formats."""
    with patch("anta.cli.psirt.get_catalog") as catalog_mock:
        result = click_runner.invoke(anta, ["psirt", "--help"])

    help_output = " ".join(result.output.split())
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta psirt" in help_output
    assert "[PREVIEW] Run ANTA tests for Arista security advisories" in help_output
    assert "This command is a preview feature" in help_output
    assert "may change at any time without a deprecation notice" in help_output
    assert "--catalog" in help_output
    for envvar in (
        "ANTA_PSIRT_IGNORE_STATUS",
        "ANTA_PSIRT_IGNORE_ERROR",
        "ANTA_PSIRT_DRY_RUN",
        "ANTA_DISCONNECT_INVENTORY",
    ):
        assert envvar in help_output
    for report in ("csv", "json", "md-report", "table", "text", "tpl-report"):
        assert report in help_output
    catalog_mock.assert_not_called()


def test_anta_psirt_uses_builtin_catalog(click_runner: CliRunner) -> None:
    """Use every registered built-in advisory test when no override is supplied."""
    catalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
    with patch("anta.cli.psirt.get_catalog", return_value=catalog) as catalog_mock:
        result = click_runner.invoke(anta, ["psirt", "--dry-run"], env={"ANTA_CATALOG": None})

    assert result.exit_code == ExitCode.OK
    assert "Tests catalog contains 1 tests" in result.output
    assert "Dry-run" in result.output
    catalog_mock.assert_called_once_with()


def test_anta_psirt_missing_default_catalog(click_runner: CliRunner) -> None:
    """Raise an explicit error when the default catalog factory returns no catalog."""
    with patch("anta.cli.psirt.get_catalog", return_value=None):
        result = click_runner.invoke(anta, ["psirt", "--dry-run"], env={"ANTA_CATALOG": None})

    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "Missing catalog for anta psirt"


@pytest.mark.parametrize(
    ("args", "env"),
    [
        pytest.param(["psirt", "--dry-run", "--catalog", str(DATA_DIR / "test_catalog.yml")], {}, id="option"),
        pytest.param(["psirt", "--dry-run"], {"ANTA_CATALOG": str(DATA_DIR / "test_catalog.yml")}, id="environment"),
    ],
)
def test_anta_psirt_catalog_override(click_runner: CliRunner, args: list[str], env: dict[str, str]) -> None:
    """A file catalog replaces the built-in catalog and may contain ordinary ANTA tests."""
    with patch("anta.cli.psirt.get_catalog") as catalog_mock:
        result = click_runner.invoke(anta, args, env=env)

    assert result.exit_code == ExitCode.OK
    assert "Tests catalog contains 1 tests" in result.output
    catalog_mock.assert_not_called()


def test_anta_psirt_dry_run_environment_variable(click_runner: CliRunner) -> None:
    """Use the command-specific ANTA_PSIRT_DRY_RUN environment variable."""
    catalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
    with patch("anta.cli.psirt.get_catalog", return_value=catalog):
        result = click_runner.invoke(anta, ["psirt"], env={"ANTA_CATALOG": None, "ANTA_PSIRT_DRY_RUN": "true"})

    assert result.exit_code == ExitCode.OK
    assert "Dry-run" in result.output


@pytest.mark.parametrize("report", ["csv", "json", "md-report", "table", "text", "tpl-report"])
def test_anta_psirt_report_help(click_runner: CliRunner, report: str) -> None:
    """Expose report commands under the PSIRT profile."""
    result = click_runner.invoke(anta, ["psirt", report, "--help"])

    assert result.exit_code == ExitCode.OK
    assert f"Usage: anta psirt {report}" in result.output


@pytest.mark.parametrize(
    ("command", "output_option", "filename", "generator", "label", "extra_args", "expand_results"),
    [
        pytest.param("csv", "--csv-output", "report.csv", "generate_security_advisory_csv_report", "CSV", (), None, id="csv"),
        pytest.param(
            "md-report",
            "--md-output",
            "report.md",
            "generate_security_advisory_md_report",
            "Markdown",
            (),
            False,
            id="markdown",
        ),
        pytest.param(
            "md-report",
            "--md-output",
            "report.md",
            "generate_security_advisory_md_report",
            "Markdown",
            ("--expand",),
            True,
            id="markdown-expanded",
        ),
    ],
)
def test_anta_psirt_advisory_report(
    click_runner: CliRunner,
    tmp_path: Path,
    command: str,
    output_option: str,
    filename: str,
    generator: str,
    label: str,
    extra_args: tuple[str, ...],
    expand_results: bool | None,
) -> None:
    """Use the advisory-specific report model and generator."""
    output = tmp_path / filename
    report = MagicMock()
    run_context = MagicMock()
    with (
        patch("anta.cli.psirt.run_tests", return_value=run_context) as run_tests_mock,
        patch("anta.cli.psirt.SecurityAdvisoryReport.from_result_manager", return_value=report) as report_mock,
        patch(f"anta.cli.psirt.{generator}") as generator_mock,
    ):
        result = click_runner.invoke(anta, ["psirt", command, output_option, str(output), *extra_args])

    assert result.exit_code == ExitCode.OK
    assert f"Security advisory {label} report saved to {output}" in " ".join(result.output.split())
    run_tests_mock.assert_called_once()
    assert isinstance(report_mock.call_args.args[0], ResultManager)
    if command == "md-report":
        generator_mock.assert_called_once()
        args, _kwargs = generator_mock.call_args
        assert args[0] is report
        assert args[1] == output
        assert args[2] is run_context
        assert isinstance(args[3], SecurityAdvisoryReportConfig)
        assert args[3].expand_results is expand_results
    else:
        generator_mock.assert_called_once_with(report, output)


def test_anta_psirt_advisory_report_rejects_invalid_results(click_runner: CliRunner, tmp_path: Path) -> None:
    """Report invalid advisory result sets as CLI usage errors."""
    output = tmp_path / "report.csv"
    error = "Security advisory reports only support advisory test results."
    with patch("anta.cli.psirt.run_tests"), patch("anta.cli.psirt.SecurityAdvisoryReport.from_result_manager", side_effect=ValueError(error)):
        result = click_runner.invoke(anta, ["psirt", "csv", "--csv-output", str(output)])

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert error in " ".join(result.output.split())
    assert not output.exists()


def test_anta_psirt_advisory_markdown_report_error(click_runner: CliRunner, tmp_path: Path) -> None:
    """Report Markdown generation errors as CLI usage errors."""
    output = tmp_path / "report.md"
    error = "Unable to write the Markdown report."
    with (
        patch("anta.cli.psirt.run_tests", return_value=MagicMock()),
        patch("anta.cli.psirt.SecurityAdvisoryReport.from_result_manager", return_value=MagicMock()),
        patch("anta.cli.psirt.generate_security_advisory_md_report", side_effect=OSError(error)),
    ):
        result = click_runner.invoke(anta, ["psirt", "md-report", "--md-output", str(output)])

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert error in " ".join(result.output.split())
    assert not output.exists()
