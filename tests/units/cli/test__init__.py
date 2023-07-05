"""
Tests for anta.cli.__init__.py
"""

from __future__ import annotations

from click.testing import CliRunner

from anta.cli import anta


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
