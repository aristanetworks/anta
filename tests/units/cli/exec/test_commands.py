# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.exec.commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from anta.cli._main import anta
from anta.cli.exec.commands import clear_counters, collect_tech_support, snapshot
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_clear_counters_help(click_runner: CliRunner) -> None:
    """Test `anta exec clear-counters --help`."""
    result = click_runner.invoke(clear_counters, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_snapshot_help(click_runner: CliRunner) -> None:
    """Test `anta exec snapshot --help`."""
    result = click_runner.invoke(snapshot, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_collect_tech_support_help(click_runner: CliRunner) -> None:
    """Test `anta exec collect-tech-support --help`."""
    result = click_runner.invoke(collect_tech_support, ["--help"])
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
    """Test `anta exec clear-counters`."""
    cli_args = ["exec", "clear-counters"]
    if tags is not None:
        cli_args.extend(["--tags", tags])
    result = click_runner.invoke(anta, cli_args)
    assert result.exit_code == ExitCode.OK


COMMAND_LIST_PATH_FILE = Path(__file__).parent.parent.parent.parent / "data" / "test_snapshot_commands.yml"


@pytest.mark.parametrize(
    ("commands_path", "tags"),
    [
        pytest.param(None, None, id="missing command list"),
        pytest.param(Path("/I/do/not/exist"), None, id="wrong path for command_list"),
        pytest.param(COMMAND_LIST_PATH_FILE, None, id="command-list only"),
        pytest.param(COMMAND_LIST_PATH_FILE, "leaf,spine", id="with tags"),
    ],
)
def test_snapshot(tmp_path: Path, click_runner: CliRunner, commands_path: Path | None, tags: str | None) -> None:
    """Test `anta exec snapshot`."""
    cli_args = ["exec", "snapshot", "--output", str(tmp_path)]
    # Need to mock datetetime
    if commands_path is not None:
        cli_args.extend(["--commands-list", str(commands_path)])
    if tags is not None:
        cli_args.extend(["--tags", tags])
    result = click_runner.invoke(anta, cli_args)
    # Failure scenarios
    if commands_path is None:
        assert result.exit_code == ExitCode.USAGE_ERROR
        return
    if not Path.exists(Path(commands_path)):
        assert result.exit_code == ExitCode.USAGE_ERROR
        return
    assert result.exit_code == ExitCode.OK


@pytest.mark.parametrize(
    ("output", "latest", "configure", "tags"),
    [
        pytest.param(None, None, False, None, id="no params"),
        pytest.param("/tmp/dummy", None, False, None, id="with output"),
        pytest.param(None, 1, False, None, id="only last show tech"),
        pytest.param(None, None, True, None, id="configure"),
        pytest.param(None, None, False, "leaf,spine", id="with tags"),
    ],
)
def test_collect_tech_support(click_runner: CliRunner, output: str | None, latest: str | None, configure: bool | None, tags: str | None) -> None:
    """Test `anta exec collect-tech-support`."""
    cli_args = ["exec", "collect-tech-support"]
    if output is not None:
        cli_args.extend(["--output", output])
    if latest is not None:
        cli_args.extend(["--latest", latest])
    if configure is True:
        cli_args.extend(["--configure"])
    if tags is not None:
        cli_args.extend(["--tags", tags])
    result = click_runner.invoke(anta, cli_args)
    assert result.exit_code == ExitCode.OK
