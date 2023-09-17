# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.exec.commands
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, patch

import pytest

from anta.cli import anta
from anta.cli.exec.commands import clear_counters, collect_tech_support, snapshot
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_clear_counters_help(click_runner: CliRunner) -> None:
    """
    Test `anta exec clear-counters --help`
    """
    result = click_runner.invoke(clear_counters, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


@pytest.mark.parametrize(
    "tags",
    [
        pytest.param(None, id="no tags"),
        pytest.param("leaf,spine", id="with tags"),
    ],
)
def test_clear_counters(click_runner: CliRunner, tags: str | None) -> None:
    """
    Test `anta exec clear-counters`
    """
    env = default_anta_env()
    cli_args = ["exec", "clear-counters"]
    expected_tags = None
    if tags is not None:
        cli_args.extend(["--tags", tags])
        expected_tags = tags.split(",")
    with patch("anta.cli.exec.commands.clear_counters_utils") as mocked_subcommand:
        mocked_subcommand.return_value = None
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")
    mocked_subcommand.assert_called_once_with(ANY, tags=expected_tags)
    assert result.exit_code == 0


def test_snapshot_help(click_runner: CliRunner) -> None:
    """
    Test `anta exec snapshot --help`
    """
    result = click_runner.invoke(snapshot, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


COMMAND_LIST_PATH_FILE = Path(__file__).parent.parent.parent.parent / "data" / "test_snapshot_commands.yml"


@pytest.mark.parametrize(
    "output, commands_path, tags",
    [
        pytest.param(None, None, None, id="missing command list"),
        pytest.param(None, Path("/I/do/not/exist"), None, id="wrong path for command_list"),
        pytest.param(None, COMMAND_LIST_PATH_FILE, None, id="command-list only"),
        pytest.param("/tmp/dummy", COMMAND_LIST_PATH_FILE, None, id="with output"),
        pytest.param(None, COMMAND_LIST_PATH_FILE, "leaf,spine", id="with tags"),
    ],
)
def test_snapshot(click_runner: CliRunner, output: str | None, commands_path: Path | None, tags: str | None) -> None:
    """
    Test `anta exec snapshot`
    """
    env = default_anta_env()
    cli_args = ["exec", "snapshot"]

    # Need to mock datetetime
    expected_path = Path("")
    if output is not None:
        cli_args.extend(["--output", output])
        expected_path = Path(f"{output}")
    expected_commands = None
    if commands_path is not None:
        cli_args.extend(["--commands-list", str(commands_path)])
        expected_commands = {"json_format": ["show version"], "text_format": ["show version"]}
    expected_tags = None
    if tags is not None:
        cli_args.extend(["--tags", tags])
        expected_tags = tags.split(",")
    with patch("anta.cli.exec.commands.collect_commands") as mocked_subcommand:
        mocked_subcommand.return_value = None
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")
    # Failure scenarios
    if commands_path is None:
        assert result.exit_code == 2
        return
    if not Path.exists(Path(commands_path)):
        assert result.exit_code == 2
        return
    # Successful scenarios
    if output is not None:
        mocked_subcommand.assert_called_once_with(ANY, expected_commands, expected_path, tags=expected_tags)
    else:
        mocked_subcommand.assert_called_once_with(ANY, expected_commands, ANY, tags=expected_tags)
        # TODO should add check that path starts with "anta_snapshot_"
    assert result.exit_code == 0


def test_collect_tech_support_help(click_runner: CliRunner) -> None:
    """
    Test `anta exec collect-tech-support --help`
    """
    result = click_runner.invoke(collect_tech_support, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


@pytest.mark.parametrize(
    "output, latest, configure, tags",
    [
        pytest.param(None, None, False, None, id="no params"),
        pytest.param("/tmp/dummy", None, False, None, id="with output"),
        pytest.param(None, 1, False, None, id="only last show tech"),
        pytest.param(None, None, True, None, id="configure"),
        pytest.param(None, None, False, "leaf,spine", id="with tags"),
    ],
)
def test_collect_tech_support(click_runner: CliRunner, output: str | None, latest: str | None, configure: bool | None, tags: str | None) -> None:
    """
    Test `anta exec collect-tech-support`
    """
    env = default_anta_env()
    cli_args = ["exec", "collect-tech-support"]
    expected_path = Path("tech-support")
    if output is not None:
        cli_args.extend(["--output", output])
        expected_path = Path(output)
    if latest is not None:
        cli_args.extend(["--latest", latest])
    if configure is True:
        cli_args.extend(["--configure"])
    expected_tags = None
    if tags is not None:
        cli_args.extend(["--tags", tags])
        expected_tags = tags.split(",")
    with patch("anta.cli.exec.commands.collect_scheduled_show_tech") as mocked_subcommand:
        mocked_subcommand.return_value = None
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")
    mocked_subcommand.assert_called_once_with(ANY, expected_path, configure, tags=expected_tags, latest=latest)
    assert result.exit_code == 0
