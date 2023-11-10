# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.get.commands
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import ANY, patch

import pytest
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError

from anta.cli import anta
from anta.cli.get.commands import from_ansible, from_cvp
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest import CaptureFixture, LogCaptureFixture

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


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
    capsys: CaptureFixture[str],
    click_runner: CliRunner,
    cvp_container: str | None,
    inventory_directory: str | None,
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
        # Get inventory-directory default
        default_dir: Path = cast(Path, from_cvp.params[4].default)
        out_dir = Path() / default_dir

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


@pytest.mark.parametrize(
    "ansible_inventory, ansible_group, output, expected_exit",
    [
        pytest.param("ansible_inventory.yml", None, None, 0, id="no group"),
        pytest.param("ansible_inventory.yml", "ATD_LEAFS", None, 0, id="group found"),
        pytest.param("ansible_inventory.yml", "DUMMY", None, 4, id="group not found"),
        pytest.param("empty_ansible_inventory.yml", None, None, 4, id="empty inventory"),
    ],
)
# pylint: disable-next=too-many-arguments
def test_from_ansible(
    tmp_path: Path,
    caplog: LogCaptureFixture,
    capsys: CaptureFixture[str],
    click_runner: CliRunner,
    ansible_inventory: Path,
    ansible_group: str | None,
    output: Path | None,
    expected_exit: int,
) -> None:
    """
    Test `anta get from-ansible`
    """
    env = default_anta_env()
    cli_args = ["get", "from-ansible"]

    os.chdir(tmp_path)
    if output is not None:
        cli_args.extend(["--output", str(output)])
        out_dir = Path() / output
    else:
        # Get inventory-directory default
        default_dir: Path = cast(Path, from_ansible.params[2].default)
        out_dir = Path() / default_dir

    if ansible_inventory is not None:
        ansible_inventory_path = DATA_DIR / ansible_inventory
        cli_args.extend(["--ansible-inventory", str(ansible_inventory_path)])

    if ansible_group is not None:
        cli_args.extend(["--ansible-group", ansible_group])

    with capsys.disabled():
        print(cli_args)
        result = click_runner.invoke(anta, cli_args, env=env, auto_envvar_prefix="ANTA")

        print(result)

    assert result.exit_code == expected_exit
    print(caplog.records)
    if expected_exit != 0:
        assert len(caplog.records) == 2
    else:
        assert out_dir.exists()
