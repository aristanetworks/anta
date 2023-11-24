# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.get.commands
"""
from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import ANY, patch

import pytest
from cvprac.cvp_client import CvpClient
from cvprac.cvp_client_errors import CvpApiError

from anta.cli import anta
from anta.cli.get.commands import from_cvp

if TYPE_CHECKING:
    from click.testing import CliRunner
    from pytest import CaptureFixture, LogCaptureFixture

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"
INIT_ANTA_INVENTORY = DATA_DIR / "test_inventory.yml"


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

    This test verifies that username and password are NOT mandatory to run this command
    """
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
            result = click_runner.invoke(anta, cli_args, auto_envvar_prefix="ANTA")

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
    "ansible_inventory, ansible_group, expected_exit, expected_log",
    [
        pytest.param("ansible_inventory.yml", None, 0, None, id="no group"),
        pytest.param("ansible_inventory.yml", "ATD_LEAFS", 0, None, id="group found"),
        pytest.param("ansible_inventory.yml", "DUMMY", 4, "Group DUMMY not found in Ansible inventory", id="group not found"),
        pytest.param("empty_ansible_inventory.yml", None, 4, "is empty", id="empty inventory"),
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
    expected_exit: int,
    expected_log: str | None,
) -> None:
    """
    Test `anta get from-ansible`

    This test verifies:
    * the parsing of an ansible-inventory
    * the ansible_group functionaliy

    The output path is ALWAYS set to a non existing file.
    """
    # Create a default directory
    out_inventory: Path = tmp_path / " output.yml"
    # Set --ansible-inventory
    ansible_inventory_path = DATA_DIR / ansible_inventory

    # Init cli_args
    cli_args = ["get", "from-ansible", "--output", str(out_inventory), "--ansible-inventory", str(ansible_inventory_path)]

    # Set --ansible-group
    if ansible_group is not None:
        cli_args.extend(["--ansible-group", ansible_group])

    with capsys.disabled():
        result = click_runner.invoke(anta, cli_args)

    assert result.exit_code == expected_exit

    if expected_exit != 0:
        assert expected_log
        assert expected_log in [rec.message for rec in caplog.records][-1]
        assert len(caplog.records) in {2, 3}
    else:
        assert out_inventory.exists()
        # TODO check size of generated inventory to validate the group functionality!


@pytest.mark.parametrize(
    "set_output, set_anta_inventory, expected_target, expected_exit, expected_log",
    [
        pytest.param(True, False, "output.yml", 0, None, id="output-only"),
        pytest.param(True, True, "output.yml", 0, None, id="output-and-inventory"),
        pytest.param(False, True, "inventory.yml", 0, None, id="inventory-only"),
        pytest.param(
            False,
            False,
            None,
            4,
            "Inventory output is not set. Either `anta --inventory` or `anta get from-ansible --output` MUST be set.",
            id="no-output-no-inventory",
        ),
    ],
)
# pylint: disable-next=too-many-arguments
def test_from_ansible_output(
    tmp_path: Path,
    caplog: LogCaptureFixture,
    capsys: CaptureFixture[str],
    click_runner: CliRunner,
    set_output: bool,
    set_anta_inventory: bool,
    expected_target: str,
    expected_exit: int,
    expected_log: str | None,
) -> None:
    """
    This test verifies the precedence of target inventory file for `anta get from-ansible`:
    1. output
    2. ANTA_INVENTORY or `anta --inventory <TARGET>` if `output` is not set
    3. Raise otherwise

    This test DOES NOT handle overwriting behavior so assuming EMPTY target for now
    """
    # The targeted ansible_inventory is static
    ansible_inventory_path = DATA_DIR / "ansible_inventory.yml"
    cli_args = ["get", "from-ansible", "--ansible-inventory", str(ansible_inventory_path)]

    if set_anta_inventory:
        tmp_inv = tmp_path / "inventory.yml"
        # preprend
        cli_args = ["-i", str(tmp_inv)] + cli_args

    if set_output:
        tmp_inv = tmp_path / "output.yml"
        cli_args.extend(["--output", str(tmp_inv)])

    with capsys.disabled():
        result = click_runner.invoke(anta, cli_args, auto_envvar_prefix="ANTA")

    assert result.exit_code == expected_exit
    if expected_exit != 0:
        assert expected_log in [rec.message for rec in caplog.records]
    else:
        expected_inv = tmp_path / expected_target
        assert expected_inv.exists()


@pytest.mark.parametrize(
    "overwrite, is_tty, init_anta_inventory, prompt, expected_exit, expected_log",
    [
        pytest.param(False, True, INIT_ANTA_INVENTORY, "y", 0, "", id="no-overwrite-tty-init-prompt-yes"),
        pytest.param(False, True, INIT_ANTA_INVENTORY, "N", 1, "Aborted", id="no-overwrite-tty-init-prompt-no"),
        pytest.param(
            False,
            False,
            INIT_ANTA_INVENTORY,
            None,
            4,
            "Conversion aborted since destination file is not empty (not running in interactive TTY)",
            id="no-overwrite-no-tty-init",
        ),
        pytest.param(False, True, None, None, 0, "", id="no-overwrite-tty-no-init"),
        pytest.param(False, False, None, None, 0, "", id="no-overwrite-no-tty-no-init"),
        pytest.param(True, True, INIT_ANTA_INVENTORY, None, 0, "", id="overwrite-tty-init"),
        pytest.param(True, False, INIT_ANTA_INVENTORY, None, 0, "", id="overwrite-no-tty-init"),
        pytest.param(True, True, None, None, 0, "", id="overwrite-tty-no-init"),
        pytest.param(True, False, None, None, 0, "", id="overwrite-no-tty-no-init"),
    ],
)
# pylint: disable-next=too-many-arguments
def test_from_ansible_overwrite(
    tmp_path: Path,
    caplog: LogCaptureFixture,
    capsys: CaptureFixture[str],
    click_runner: CliRunner,
    overwrite: bool,
    is_tty: bool,
    prompt: str | None,
    init_anta_inventory: Path,
    expected_exit: int,
    expected_log: str | None,
) -> None:
    """
    Test `anta get from-ansible` overwrite mechanism

    The test uses a static ansible-inventory and output as these are tested in other functions

    This test verifies:
    * that overwrite is working as expected with or without init data in the target file
    * that when the target file is not empty and a tty is present, the user is prompt with confirmation
    * Check the behavior when the prompt is filled

    The initial content of the ANTA inventory is set using init_anta_inventory, if it is None, no inventory is set.

    * With overwrite True, the expectation is that the from-ansible command succeeds
    * With no init (init_anta_inventory == None), the expectation is also that command succeeds
    """
    # The targeted ansible_inventory is static
    ansible_inventory_path = DATA_DIR / "ansible_inventory.yml"
    expected_anta_inventory_path = DATA_DIR / "expected_anta_inventory.yml"
    tmp_inv = tmp_path / "output.yml"
    cli_args = ["get", "from-ansible", "--ansible-inventory", str(ansible_inventory_path), "--output", str(tmp_inv)]

    if overwrite:
        cli_args.append("--overwrite")

    if init_anta_inventory:
        shutil.copyfile(init_anta_inventory, tmp_inv)

    print(cli_args)
    # Verify initial content is different
    if tmp_inv.exists():
        assert not filecmp.cmp(tmp_inv, expected_anta_inventory_path)

    with capsys.disabled():
        # TODO, handle is_tty
        with patch("anta.cli.get.commands.stdin") as patched_stdin:
            patched_stdin.isatty.return_value = is_tty
            result = click_runner.invoke(anta, cli_args, auto_envvar_prefix="ANTA", input=prompt)

    assert result.exit_code == expected_exit
    if expected_exit == 0:
        assert filecmp.cmp(tmp_inv, expected_anta_inventory_path)
    elif expected_exit == 1:
        assert expected_log
        assert expected_log in result.stdout
    elif expected_exit == 4:
        assert expected_log in [rec.message for rec in caplog.records]
