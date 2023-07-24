"""
Tests for anta.cli.__init__
"""

from __future__ import annotations

from click.testing import CliRunner

from anta.cli import anta
from tests.lib.utils import default_anta_env


def test_anta(click_runner: CliRunner) -> None:
    """
    Test anta main entrypoint
    """
    result = click_runner.invoke(anta)
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_anta_help(click_runner: CliRunner) -> None:
    """
    Test anta --help
    """
    result = click_runner.invoke(anta, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_anta_nrfu_help(click_runner: CliRunner) -> None:
    """
    Test anta nrfu --help
    """
    result = click_runner.invoke(anta, ["nrfu", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta nrfu" in result.output


def test_anta_exec_help(click_runner: CliRunner) -> None:
    """
    Test anta exec --help
    """
    result = click_runner.invoke(anta, ["exec", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta exec" in result.output


def test_anta_debug_help(click_runner: CliRunner) -> None:
    """
    Test anta debug --help
    """
    result = click_runner.invoke(anta, ["debug", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta debug" in result.output


def test_anta_get_help(click_runner: CliRunner) -> None:
    """
    Test anta get --help
    """
    result = click_runner.invoke(anta, ["get", "--help"])
    assert result.exit_code == 0
    assert "Usage: anta get" in result.output


def test_anta_enable_password_requires_enable_fail(click_runner: CliRunner) -> None:
    """
    Test anta --enable-password blah and verify that it fails
    """
    result = click_runner.invoke(anta, ["--enable-password", "blah"])
    assert result.exit_code == 2
    assert "Invalid value for '--enable-password'" in result.output


def test_anta_enable_password_requires_enable_success(click_runner: CliRunner) -> None:
    """
    Test 'anta --enable --enable-password blah get tags' and verifies that it succeeds
    """
    env = default_anta_env()
    result = click_runner.invoke(anta, ["--enable", "--enable-password", "blah", "get", "tags"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == 0
