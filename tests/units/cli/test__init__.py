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
    # Somehow not managing to make the environment work..
    # result = click_runner.invoke(anta, ["--enable", "--enable-password", "blah", "get", "tags"], env=env)
    args: list[str] = []
    args.append("--username")
    args.append(env["ANTA_USERNAME"])
    args.append("--password")
    args.append(env["ANTA_PASSWORD"])
    args.append("--inventory")
    args.append(env["ANTA_INVENTORY"])
    args.extend(["--enable", "--enable-password", "blah", "get"])
    result = click_runner.invoke(anta, args)
    assert result.exit_code == 0
