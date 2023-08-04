"""
Tests for anta.cli.get.commands
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from unittest.mock import ANY, patch

import pytest
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError
from pathlib import Path

from anta.cli import anta
from anta.cli.get.commands import from_cvp
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest import CapsysFixture, LogCaptureFixture


# Not testing for required parameter, click does this well.
@pytest.mark.parametrize(
    "cvp_container, inventory_directory, cvp_connect_failure",
    [
        pytest.param(None, None, True, id="cvp connect failure"),
        pytest.param(None, None, False, id="default_directory"),
        pytest.param(None, "custom", False, id="custom_directory"),
        pytest.param("custom_container", None, False, id="custom_container"),
    ],
)
# pylint: disable-next=too-many-arguments
def test_from_cvp(
    caplog: LogCaptureFixture,
    capsys: CapsysFixture,
    click_runner: CliRunner,
    cvp_container: Optional[str],
    inventory_directory: Optional[str],
    cvp_connect_failure: bool,
) -> None:
    """
    Test `anta get from-cvp`
    """
    env = default_anta_env()
    cli_args = ["get", "from-cvp", "--cvp-ip", "42.42.42.42", "--cvp-username", "anta", "--cvp-password", "anta"]

    if inventory_directory is not None:
        cli_args.extend(["--inventory-directory", inventory_directory])
        out_dir = Path() / inventory_directory
    else:
        out_dir = Path() / from_cvp.params[4].default

    if cvp_container is not None:
        cli_args.extend(["--cvp-container", cvp_container])
        out_file = out_dir / f"inventory-{cvp_container}.yml"
    else:
        out_file = out_dir / "inventory.yml"

    def mock_cvp_connect(self: CvpClient, *args: str, **kwargs: str) -> None:
        # pylint: disable=unused-argument
        if cvp_connect_failure:
            raise CvpApiError(msg="mocked CvpApiError")

    # always get a token
    with patch("anta.cli.get.commands.get_cv_token", return_value="dummy_token"), patch(
        "anta.cli.get.commands.CvpClient.connect", autospec=True, side_effect=mock_cvp_connect
    ) as mocked_cvp_connect, patch("cvprac.cvp_client.CvpApi.get_inventory", autospec=True, return_value=[]) as mocked_get_inventory, patch(
        "cvprac.cvp_client.CvpApi.get_devices_in_container", autospec=True, return_value=[]
    ) as mocked_get_devices_in_container:
        # https://github.com/pallets/click/issues/824#issuecomment-1583293065
        with capsys.disabled():
            result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")

    if not cvp_connect_failure:
        assert out_file.exists()
        # Remove generated inventory file and directory
        out_file.unlink()
        out_dir.rmdir()

    mocked_cvp_connect.assert_called_once()
    if not cvp_connect_failure:
        assert "Connected to CVP" in caplog.text
        if cvp_container is not None:
            mocked_get_devices_in_container.assert_called_once_with(ANY, cvp_container)
        else:
            mocked_get_inventory.assert_called_once()
        assert result.exit_code == 0
    else:
        assert "Error connecting to cvp" in caplog.text
        assert result.exit_code == 1
