# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.debug.commands
"""
from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, Literal
from unittest.mock import MagicMock, patch

import click
import pytest

from anta.cli import anta
from anta.cli.debug.commands import get_device
from anta.device import AntaDevice
from anta.models import AntaCommand
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner

    from anta.inventory import AntaInventory


@pytest.mark.parametrize(
    "device_name, expected_raise",
    [
        pytest.param("dummy", nullcontext(), id="existing device"),
        pytest.param("other", pytest.raises(click.exceptions.UsageError), id="non existing device"),
    ],
)
def test_get_device(test_inventory: AntaInventory, device_name: str, expected_raise: Any) -> None:
    """
    Test get_device

    test_inventory is a fixture that returns an AntaInventory using the content of tests/data/test_inventory.yml
    """
    # build click Context
    ctx = click.Context(command=MagicMock())
    ctx.ensure_object(dict)
    ctx.obj["inventory"] = test_inventory

    with expected_raise:
        result = get_device(ctx, MagicMock(auto_spec=click.Option), device_name)
        assert isinstance(result, AntaDevice)


# TODO complete test cases
@pytest.mark.parametrize(
    "command, ofmt, version, revision, device, failed",
    [
        pytest.param("show version", "json", None, None, "dummy", False, id="json command"),
        pytest.param("show version", "text", None, None, "dummy", False, id="text command"),
        pytest.param("show version", None, "1", None, "dummy", False, id="version"),
        pytest.param("show version", None, None, 3, "dummy", False, id="revision"),
        pytest.param("show version", None, None, None, "dummy", True, id="command fails"),
    ],
)
def test_run_cmd(
    click_runner: CliRunner, command: str, ofmt: Literal["json", "text"], version: Literal["1", "latest"] | None, revision: int | None, device: str, failed: bool
) -> None:
    """
    Test `anta debug run-cmd`
    """
    # pylint: disable=too-many-arguments
    env = default_anta_env()
    cli_args = ["debug", "run-cmd", "--command", command, "--device", device]

    # ofmt
    expected_ofmt = ofmt
    if ofmt is None:
        expected_ofmt = "json"
    else:
        cli_args.extend(["--ofmt", ofmt])

    # version
    expected_version: Literal["latest", 1]
    if version is None:
        expected_version = "latest"
    else:
        # Need to copy ugly hack here..
        expected_version = "latest" if version == "latest" else 1
        cli_args.extend(["--version", version])

    # revision
    if revision is not None:
        cli_args.extend(["--revision", str(revision)])

    # errors
    expected_errors = []
    if failed:
        expected_errors = ["Command failed to run"]

    # exit code
    expected_exit_code = 1 if failed else 0

    def expected_result() -> Any:
        """
        Helper to return some dummy payload for collect depending on outformat
        """
        if failed:
            return None
        if expected_ofmt == "json":
            return {"dummy": 42}
        if expected_ofmt == "text":
            return "dummy"
        raise ValueError("Unknown format")

    async def dummy_collect(c: AntaCommand) -> None:
        """
        mocking collect coroutine
        """
        c.output = expected_result()
        if c.output is None:
            c.errors = expected_errors

    with patch("anta.device.AsyncEOSDevice.collect") as mocked_collect:
        mocked_collect.side_effect = dummy_collect
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")

    mocked_collect.assert_awaited_with(
        AntaCommand(
            command=command,
            version=expected_version,
            revision=revision,
            ofmt=expected_ofmt,
            output=expected_result(),
            errors=expected_errors,
        )
    )
    assert result.exit_code == expected_exit_code
