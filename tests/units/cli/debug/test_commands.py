# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.debug.commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest

from anta.cli import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.mark.parametrize(
    ("command", "ofmt", "version", "revision", "device", "failed"),
    [
        pytest.param("show version", "json", None, None, "leaf1", False, id="json command"),
        pytest.param("show version", "text", None, None, "leaf1", False, id="text command"),
        pytest.param("show version", None, "latest", None, "leaf1", False, id="version-latest"),
        pytest.param("show version", None, "1", None, "leaf1", False, id="version"),
        pytest.param("show version", None, None, 3, "leaf1", False, id="revision"),
        pytest.param("undefined", None, None, None, "leaf1", True, id="command fails"),
        pytest.param("undefined", None, None, None, "doesnotexist", True, id="Device does not exist"),
    ],
)
def test_run_cmd(
    click_runner: CliRunner,
    command: str,
    ofmt: Literal["json", "text"],
    version: Literal["1", "latest"] | None,
    revision: int | None,
    device: str,
    failed: bool,
) -> None:
    """Test `anta debug run-cmd`."""
    cli_args = ["-l", "debug", "debug", "run-cmd", "--command", command, "--device", device]

    # ofmt
    if ofmt is not None:
        cli_args.extend(["--ofmt", ofmt])

    # version
    if version is not None:
        cli_args.extend(["--version", version])

    # revision
    if revision is not None:
        cli_args.extend(["--revision", str(revision)])

    result = click_runner.invoke(anta, cli_args)
    if failed:
        assert result.exit_code == ExitCode.USAGE_ERROR
    else:
        assert result.exit_code == ExitCode.OK
        if revision is not None:
            assert f"revision={revision}" in result.output
        if version is not None:
            assert (f"version='{version}'" if version == "latest" else f"version={version}") in result.output
