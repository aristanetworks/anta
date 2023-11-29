# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.nrfu.commands
"""
from __future__ import annotations

from click.testing import CliRunner

from anta.cli import anta
from anta.cli.utils import ExitCode
from tests.lib.utils import default_anta_env


def test_anta_nrfu(click_runner: CliRunner) -> None:
    """
    Test anta nrfu, catalog is given via env
    """
    env = default_anta_env()
    result = click_runner.invoke(anta, ["nrfu", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.OK
    assert "ANTA Inventory contains 3 devices" in result.output
    # assert "Tests catalog contains 4 tests" in result.output
    print(result.output)


def test_anta_password_required(click_runner: CliRunner) -> None:
    """
    Test that password is provided
    """
    env = default_anta_env()
    env.pop("ANTA_PASSWORD")
    result = click_runner.invoke(anta, ["nrfu", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "EOS password needs to be provided by using either the '--password' option or the '--prompt' option." in result.output


def test_anta_password(click_runner: CliRunner) -> None:
    """
    Test that password can be provided either via --password or --prompt
    """
    env = default_anta_env()
    env.pop("ANTA_PASSWORD")
    result = click_runner.invoke(anta, ["nrfu", "--password", "secret", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.OK
    result = click_runner.invoke(anta, ["nrfu", "--prompt", "text"], input="password\npassword\n", env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.OK


def test_anta_enable_password(click_runner: CliRunner) -> None:
    """
    Test that enable password can be provided either via --enable-password or --prompt
    """
    env = default_anta_env()

    # Both enable and enable-password
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--enable-password", "secret", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.OK

    # enable and prompt y
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--prompt", "text"], input="y\npassword\npassword\n", env=env, auto_envvar_prefix="ANTA")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" in result.output
    assert result.exit_code == ExitCode.OK

    # enable and prompt N
    result = click_runner.invoke(anta, ["nrfu", "--enable", "--prompt", "text"], input="N\n", env=env, auto_envvar_prefix="ANTA")
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == ExitCode.OK

    # enable and enable-password and prompt (redundant)
    result = click_runner.invoke(
        anta, ["nrfu", "--enable", "--enable-password", "blah", "--prompt", "text"], input="y\npassword\npassword\n", env=env, auto_envvar_prefix="ANTA"
    )
    assert "Is a password required to enter EOS privileged EXEC mode? [y/N]:" not in result.output
    assert "Please enter a password to enter EOS privileged EXEC mode" not in result.output
    assert result.exit_code == ExitCode.OK

    # enabled-password without enable
    result = click_runner.invoke(anta, ["nrfu", "--enable-password", "blah", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert "Providing a password to access EOS Privileged EXEC mode requires '--enable' option." in result.output


def test_anta_enable_alone(click_runner: CliRunner) -> None:
    """
    Test that enable can be provided either without enable-password
    """
    env = default_anta_env()
    result = click_runner.invoke(anta, ["nrfu", "--enable", "text"], env=env, auto_envvar_prefix="ANTA")
    assert result.exit_code == ExitCode.OK


def test_disable_cache(click_runner: CliRunner) -> None:
    """
    Test that disable_cache is working on inventory
    """
    env = default_anta_env()
    result = click_runner.invoke(anta, ["nrfu", "--disable-cache", "text"], env=env, auto_envvar_prefix="ANTA")
    stdout_lines = result.stdout.split("\n")
    # All caches should be disabled from the inventory
    for line in stdout_lines:
        if "disable_cache" in line:
            assert "True" in line
    assert result.exit_code == ExitCode.OK
