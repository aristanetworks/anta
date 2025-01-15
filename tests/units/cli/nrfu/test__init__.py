# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.nrfu."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    import pytest
    from click.testing import CliRunner

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"

# TODO: write unit tests for ignore-status and ignore-error


def test_anta_nrfu_help(click_runner: CliRunner) -> None:
    """Test anta nrfu --help."""
    result = click_runner.invoke(anta, ["nrfu", "--help"])
    assert result.exit_code == ExitCode.OK
    assert "Usage: anta nrfu" in result.output


def test_anta_nrfu_wrong_subcommand(click_runner: CliRunner) -> None:
    """Test anta nrfu toast."""
    result = click_runner.invoke(anta, ["nrfu", "oook"])
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Usage: anta nrfu" in result.output
    assert "No such command 'oook'." in result.output


def test_anta_nrfu(click_runner: CliRunner) -> None:
    """Test anta nrfu, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu"])
    assert result.exit_code == ExitCode.OK
    assert "ANTA Inventory contains 3 devices" in result.output
    assert "Tests catalog contains 1 tests" in result.output


def test_anta_nrfu_dry_run(click_runner: CliRunner) -> None:
    """Test anta nrfu --dry-run, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "--dry-run"])
    assert result.exit_code == ExitCode.OK
    assert "ANTA Inventory contains 3 devices" in result.output
    assert "Tests catalog contains 1 tests" in result.output
    assert "Dry-run" in result.output


def test_anta_nrfu_wrong_catalog_format(click_runner: CliRunner) -> None:
    """Test anta nrfu --dry-run, catalog is given via env."""
    result = click_runner.invoke(anta, ["nrfu", "--dry-run", "--catalog-format", "toto"])
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Invalid value for '--catalog-format': 'toto' is not one of 'yaml', 'json'." in result.output


def test_anta_password_required(click_runner: CliRunner) -> None:
    """Test that password is provided."""
    env = {"ANTA_PASSWORD": None}
    result = click_runner.invoke(anta, ["nrfu"], env=env)

    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "EOS password needs to be provided by using either the '--password' option or the '--prompt' option." in result.output


def test_anta_password(click_runner: CliRunner) -> None:
    """Test that password can be provided either via --password or --prompt."""
    env = {"ANTA_PASSWORD": None}
    result = click_runner.invoke(anta, ["nrfu", "--password", "secret"], env=env)
    assert result.exit_code == ExitCode.OK
    result = click_runner.invoke(anta, ["nrfu", "--prompt"], input="password\npassword\n", env=env)
    assert result.exit_code == ExitCode.OK


def test_anta_enable_password(click_runner: CliRunner) -> None:
    """Test that enable password can be provided either via --enable-password or --prompt."""
    # Both enable and enable-password
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--enable-password", "secret"])
    assert result.exit_code == ExitCode.OK

    # enable and prompt y
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--prompt"], input="y\npassword\npassword\n")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" in result.output
    assert result.exit_code == ExitCode.OK

    # enable and prompt N
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--prompt"], input="N\n")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == ExitCode.OK

    result = click_runner.invoke(anta, ["nrfu", "--enable", "--enable-password", "blah", "--prompt"], input="y\npassword\npassword\n")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" not in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == ExitCode.OK

    # enabled-password without enable
    result = click_runner.invoke(anta, ["nrfu", "--enable-password", "blah"])
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Providing a password to access EOS Privileged EXEC mode requires '--enable' option." in result.output


def test_anta_enable_alone(click_runner: CliRunner) -> None:
    """Test that enable can be provided either without enable-password."""
    result = click_runner.invoke(anta, ["nrfu", "--enable"])
    assert result.exit_code == ExitCode.OK


def test_disable_cache(click_runner: CliRunner) -> None:
    """Test that disable_cache is working on inventory."""
    result = click_runner.invoke(anta, ["nrfu", "--disable-cache"])
    stdout_lines = result.stdout.split("\n")
    # All caches should be disabled from the inventory
    for line in stdout_lines:
        if "disable_cache" in line:
            assert "True" in line
    assert result.exit_code == ExitCode.OK


def test_hide(click_runner: CliRunner) -> None:
    """Test the `--hide` option of the `anta nrfu` command."""
    result = click_runner.invoke(anta, ["nrfu", "--hide", "success", "text"])
    assert "SUCCESS" not in result.output


def test_invalid_inventory(caplog: pytest.LogCaptureFixture, click_runner: CliRunner) -> None:
    """Test invalid inventory."""
    result = click_runner.invoke(anta, ["nrfu", "--inventory", str(DATA_DIR / "invalid_inventory.yml")])
    assert "CRITICAL" in caplog.text
    assert "Failed to parse the inventory" in caplog.text
    assert result.exit_code == ExitCode.USAGE_ERROR


def test_invalid_catalog(caplog: pytest.LogCaptureFixture, click_runner: CliRunner) -> None:
    """Test invalid catalog."""
    result = click_runner.invoke(anta, ["nrfu", "--catalog", str(DATA_DIR / "test_catalog_not_a_list.yml")])
    assert "CRITICAL" in caplog.text
    assert "Failed to parse the catalog" in caplog.text
    assert result.exit_code == ExitCode.USAGE_ERROR
