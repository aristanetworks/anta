# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the ``anta psirt`` command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from anta._runner import AntaRunContext, AntaRunFilters
from anta.catalog import AntaCatalog
from anta.cli import anta
from anta.cli.psirt import psirt
from anta.cli.utils import ExitCode
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.reporting_data import SA146_ADVISORY, build_security_advisory_result

if TYPE_CHECKING:
    import click
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
    assert "JSON, text, and table reports are not currently implemented" in help_output
    assert "--catalog" not in help_output
    for envvar in (
        "ANTA_PSIRT_IGNORE_STATUS",
        "ANTA_PSIRT_IGNORE_ERROR",
        "ANTA_PSIRT_DRY_RUN",
    ):
        assert envvar in help_output
    assert "ANTA_DISCONNECT_INVENTORY" not in help_output
    option_names = {parameter.name for parameter in psirt.params}
    assert "test" in option_names
    assert "disconnect" not in option_names
    for report in ("csv", "md-report", "tpl-report"):
        assert report in help_output
    for report in ("json", "table", "text"):
        assert report not in psirt.commands
    catalog_mock.assert_not_called()


def test_anta_psirt_uses_builtin_catalog(click_runner: CliRunner) -> None:
    """Use every registered built-in advisory test and ignore the generic catalog environment variable."""
    catalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
    with patch("anta.cli.psirt.get_catalog", return_value=catalog) as catalog_mock:
        result = click_runner.invoke(
            anta,
            ["psirt", "--dry-run", "tpl-report", "--template", str(DATA_DIR / "template.j2")],
            env={"ANTA_CATALOG": str(DATA_DIR / "test_catalog_not_a_list.yml")},
        )

    assert result.exit_code == ExitCode.OK
    assert "Tests catalog contains 1 tests" in result.output
    assert "Dry-run" in result.output
    catalog_mock.assert_called_once_with()


def test_anta_psirt_missing_default_catalog(click_runner: CliRunner) -> None:
    """Raise an explicit error when the default catalog factory returns no catalog."""
    with patch("anta.cli.psirt.get_catalog", return_value=None):
        result = click_runner.invoke(anta, ["psirt", "--dry-run", "tpl-report", "--template", str(DATA_DIR / "template.j2")], env={"ANTA_CATALOG": None})

    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "Missing catalog for anta psirt"


def test_anta_psirt_fixed_options(click_runner: CliRunner) -> None:
    """Run selected advisory tests and always disconnect inventory devices."""

    def check_context(ctx: click.Context) -> None:
        assert ctx.obj["test"] == ("VerifySA117", "VerifySA140")
        assert ctx.obj["disconnect"] is True
        ctx.exit()

    with patch("anta.cli.nrfu.commands.run_tests", side_effect=check_context):
        result = click_runner.invoke(
            anta,
            [
                "psirt",
                "--test",
                "VerifySA117",
                "--test",
                "VerifySA140",
                "tpl-report",
                "--template",
                str(DATA_DIR / "template.j2"),
            ],
            env={"ANTA_DISCONNECT_INVENTORY": "false"},
        )

    assert result.exit_code == ExitCode.OK


def test_anta_psirt_rejects_unknown_test(click_runner: CliRunner) -> None:
    """Reject test filters that are not present in the built-in advisory catalog."""
    result = click_runner.invoke(
        anta,
        ["psirt", "--test", "VerifyUnknownSA", "tpl-report", "--template", str(DATA_DIR / "template.j2")],
    )

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Invalid value for '--test': Unknown security advisory test(s): VerifyUnknownSA" in result.output


def test_anta_psirt_dry_run_environment_variable(click_runner: CliRunner) -> None:
    """Use the command-specific ANTA_PSIRT_DRY_RUN environment variable."""
    catalog = AntaCatalog.parse(DATA_DIR / "test_catalog.yml")
    with patch("anta.cli.psirt.get_catalog", return_value=catalog):
        result = click_runner.invoke(
            anta,
            ["psirt", "tpl-report", "--template", str(DATA_DIR / "template.j2")],
            env={"ANTA_CATALOG": None, "ANTA_PSIRT_DRY_RUN": "true"},
        )

    assert result.exit_code == ExitCode.OK
    assert "Dry-run" in result.output


@pytest.mark.parametrize("report", ["csv", "md-report", "tpl-report"])
def test_anta_psirt_report_help(click_runner: CliRunner, report: str) -> None:
    """Expose report commands under the PSIRT profile."""
    result = click_runner.invoke(anta, ["psirt", report, "--help"])

    assert result.exit_code == ExitCode.OK
    assert f"Usage: anta psirt {report}" in result.output
    assert "--expand" not in result.output
    assert "ANTA_PSIRT_MD_REPORT_EXPAND" not in result.output


@pytest.mark.parametrize(
    ("command", "output_option", "filename", "generator", "label"),
    [
        pytest.param("csv", "--csv-output", "report.csv", "generate_security_advisory_csv_report", "CSV", id="csv"),
        pytest.param("md-report", "--md-output", "report.md", "generate_security_advisory_md_report", "Markdown", id="markdown"),
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
        result = click_runner.invoke(anta, ["psirt", command, output_option, str(output)])

    assert result.exit_code == ExitCode.OK
    assert f"Security advisory {label} report saved to {output}" in " ".join(result.output.split())
    run_tests_mock.assert_called_once()
    assert isinstance(report_mock.call_args.args[0], ResultManager)
    if command == "md-report":
        generator_mock.assert_called_once_with(report, output, run_context)
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


def test_anta_psirt_advisory_markdown_report_all_results_hidden(click_runner: CliRunner, tmp_path: Path) -> None:
    """Generate only the run overview when every advisory result is hidden."""
    output = tmp_path / "report.md"

    def run_tests_with_success(ctx: click.Context) -> AntaRunContext:
        manager = ctx.obj["result_manager"]
        manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", SA146_ADVISORY))
        inventory = MagicMock()
        inventory.__len__.return_value = 1
        return AntaRunContext(inventory=inventory, catalog=MagicMock(), manager=manager, filters=AntaRunFilters())

    with patch("anta.cli.psirt.run_tests", side_effect=run_tests_with_success):
        result = click_runner.invoke(anta, ["psirt", "--hide", "success", "md-report", "--md-output", str(output)])

    assert result.exit_code == ExitCode.OK
    content = output.read_text(encoding="utf-8")
    assert "Run Overview" in content
    assert "| **Security Advisories Tested** | 1 |" in content
    assert "Advisory Exposure Summary" not in content
    assert "Security Advisory Details" not in content
    assert "| **Total Devices In Inventory** | 1 |" in content
    assert "| **Devices Assessed** | 1 |" in content


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
