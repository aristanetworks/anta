"""
Tests for anta.cli.debug.commands
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, Optional, Literal
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import click
import pytest

from anta.cli import anta
from anta.cli.debug.commands import get_device
from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.models import AntaCommand
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.mark.parametrize(
    "device_name, expected_raise",
    [
        pytest.param("dummy", nullcontext(), id="existing device"),
        pytest.param("mocked_device", pytest.raises(click.exceptions.UsageError), id="non existing device"),
    ],
)
def test_get_device(device_name: str, expected_raise: Any) -> None:
    """
    Test get_device
    """
    env = default_anta_env()
    # TODO see if this should be a fixture instead
    inventory = AntaInventory.parse(
        inventory_file=env["ANTA_INVENTORY"],
        username=env["ANTA_USERNAME"],
        password=env["ANTA_PASSWORD"],
    )
    # build click Context
    ctx = click.Context(command=MagicMock())
    ctx.ensure_object(dict)
    ctx.obj["inventory"] = inventory

    with expected_raise:
        result = get_device(ctx, None, device_name)
        assert isinstance(result, AntaDevice)


# TODO complete test cases
@pytest.mark.parametrize(
    "command, ofmt, version, revision, device",
    [
        pytest.param("show version", "json", None, None, "dummy", id="json command"),
        pytest.param("show version", "text", None, None, "dummy", id="text command"),
        pytest.param("show version", None, "1", None, "dummy", id="version"),
        pytest.param("show version", None, None, 3, "dummy", id="revision"),
        #    pytest.param("show version", None, None, 3, "mocked_device", id="non existing device"),
    ],
)
def test_run_cmd(click_runner: CliRunner, command: str, ofmt: str, version: Optional[Literal["1", "latest"]], revision: Optional[int], device: str) -> None:
    """
    Test `anta debug run-cmd`
    """
    env = default_anta_env()
    cli_args = ["debug", "run-cmd", "--command", command, "--device", device]

    # ofmt
    expected_ofmt = ofmt
    if ofmt is None:
        expected_ofmt = "json"
    else:
        cli_args.extend(["--ofmt", ofmt])

    # version
    expected_version = version
    if version is None:
        expected_version = "latest"
    else:
        # Need to copy ugly hack here..
        expected_version = "latest" if version == "latest" else 1
        cli_args.extend(["--version", version])

    # revision
    if revision is not None:
        cli_args.extend(["--revision", revision])

    def expected_result() -> Any:
        """
        Helper to return some dummy payload for collect depending on outformat
        """
        if expected_ofmt == "json":
            return {"dummy": 42}
        elif expected_ofmt == "text":
            return "dummy"

    async def dummy_collect(c: AntaCommand) -> None:
        """
        mocking collect coroutine
        """
        c.output = expected_result()

    with patch("anta.device.AsyncEOSDevice.collect") as mocked_collect:
        mocked_collect.side_effect = dummy_collect
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")

    mocked_collect.assert_awaited_with(
        AntaCommand(
            command=command, version=expected_version, revision=revision, ofmt=expected_ofmt, output=expected_result(), template=None, failed=None, params=None
        )
    )
    assert result.exit_code == 0
