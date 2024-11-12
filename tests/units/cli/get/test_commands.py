# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.get.commands."""

from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, patch

import pytest
import requests
from cvprac.cvp_client_errors import CvpApiError

from anta.cli._main import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner
    from cvprac.cvp_client import CvpClient

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


@pytest.mark.parametrize(
    ("cvp_container", "verify_cert", "cv_token_failure", "cvp_connect_failure"),
    [
        pytest.param(None, True, False, False, id="all devices - verify cert"),
        pytest.param(None, True, True, False, id="all devices - fail SSL check"),
        pytest.param(None, False, False, False, id="all devices - do not verify cert"),
        pytest.param("custom_container", False, False, False, id="custom container"),
        pytest.param(None, False, False, True, id="cvp connect failure"),
    ],
)
def test_from_cvp(
    tmp_path: Path,
    click_runner: CliRunner,
    cvp_container: str | None,
    verify_cert: bool,
    cv_token_failure: bool,
    cvp_connect_failure: bool,
) -> None:
    # ruff: noqa: C901
    """Test `anta get from-cvp`.

    This test verifies that username and password are NOT mandatory to run this command
    """
    output: Path = tmp_path / "output.yml"
    cli_args = [
        "get",
        "from-cvp",
        "--output",
        str(output),
        "--host",
        "42.42.42.42",
        "--username",
        "anta",
        "--password",
        "anta",
    ]

    if cvp_container is not None:
        cli_args.extend(["--container", cvp_container])
    if not verify_cert:
        cli_args.extend(["--ignore-cert"])

    def mock_get_cv_token(*_args: str, **_kwargs: str) -> None:
        if cv_token_failure:
            raise requests.exceptions.SSLError

    def mock_cvp_connect(_self: CvpClient, *_args: str, **_kwargs: str) -> None:
        if cvp_connect_failure:
            raise CvpApiError(msg="mocked CvpApiError")

    # always get a token
    with (
        patch("anta.cli.get.commands.get_cv_token", autospec=True, side_effect=mock_get_cv_token),
        patch(
            "cvprac.cvp_client.CvpClient.connect",
            autospec=True,
            side_effect=mock_cvp_connect,
        ) as mocked_cvp_connect,
        patch("cvprac.cvp_client.CvpApi.get_inventory", autospec=True, return_value=[]) as mocked_get_inventory,
        patch(
            "cvprac.cvp_client.CvpApi.get_devices_in_container",
            autospec=True,
            return_value=[],
        ) as mocked_get_devices_in_container,
    ):
        result = click_runner.invoke(anta, cli_args)

    if not cvp_connect_failure and not cv_token_failure:
        assert output.exists()

    if cv_token_failure:
        assert "Authentication to CloudVison failed" in result.output
        assert result.exit_code == ExitCode.USAGE_ERROR
        return

    mocked_cvp_connect.assert_called_once()

    if cvp_connect_failure:
        assert "Error connecting to CloudVision" in result.output
        assert result.exit_code == ExitCode.USAGE_ERROR
        return

    assert "Connected to CloudVision" in result.output
    if cvp_container is not None:
        mocked_get_devices_in_container.assert_called_once_with(ANY, cvp_container)
    else:
        mocked_get_inventory.assert_called_once()
    assert result.exit_code == ExitCode.OK


@pytest.mark.parametrize(
    ("ansible_inventory", "ansible_group", "expected_exit", "expected_log"),
    [
        pytest.param("ansible_inventory.yml", None, ExitCode.OK, None, id="no group"),
        pytest.param("ansible_inventory.yml", "ATD_LEAFS", ExitCode.OK, None, id="group found"),
        pytest.param(
            "ansible_inventory.yml",
            "DUMMY",
            ExitCode.USAGE_ERROR,
            "Group DUMMY not found in Ansible inventory",
            id="group not found",
        ),
        pytest.param(
            "empty_ansible_inventory.yml",
            None,
            ExitCode.USAGE_ERROR,
            "is empty",
            id="empty inventory",
        ),
    ],
)
def test_from_ansible(
    tmp_path: Path,
    click_runner: CliRunner,
    ansible_inventory: Path,
    ansible_group: str | None,
    expected_exit: int,
    expected_log: str | None,
) -> None:
    """Test `anta get from-ansible`.

    This test verifies:
    * the parsing of an ansible-inventory
    * the ansible_group functionaliy

    The output path is ALWAYS set to a non existing file.
    """
    output: Path = tmp_path / "output.yml"
    ansible_inventory_path = DATA_DIR / ansible_inventory
    # Init cli_args
    cli_args = [
        "get",
        "from-ansible",
        "--output",
        str(output),
        "--ansible-inventory",
        str(ansible_inventory_path),
    ]

    # Set --ansible-group
    if ansible_group is not None:
        cli_args.extend(["--ansible-group", ansible_group])

    result = click_runner.invoke(anta, cli_args)

    assert result.exit_code == expected_exit

    if expected_exit != ExitCode.OK:
        assert expected_log
        assert expected_log in result.output
    else:
        assert output.exists()
        # TODO: check size of generated inventory to validate the group functionality!


@pytest.mark.parametrize(
    ("env_set", "overwrite", "is_tty", "prompt", "expected_exit", "expected_log"),
    [
        pytest.param(
            True,
            False,
            True,
            "y",
            ExitCode.OK,
            "",
            id="no-overwrite-tty-init-prompt-yes",
        ),
        pytest.param(
            True,
            False,
            True,
            "N",
            ExitCode.INTERNAL_ERROR,
            "Aborted",
            id="no-overwrite-tty-init-prompt-no",
        ),
        pytest.param(
            True,
            False,
            False,
            None,
            ExitCode.USAGE_ERROR,
            "Conversion aborted since destination file is not empty (not running in interactive TTY)",
            id="no-overwrite-no-tty-init",
        ),
        pytest.param(False, False, True, None, ExitCode.OK, "", id="no-overwrite-tty-no-init"),
        pytest.param(False, False, False, None, ExitCode.OK, "", id="no-overwrite-no-tty-no-init"),
        pytest.param(True, True, True, None, ExitCode.OK, "", id="overwrite-tty-init"),
        pytest.param(True, True, False, None, ExitCode.OK, "", id="overwrite-no-tty-init"),
        pytest.param(False, True, True, None, ExitCode.OK, "", id="overwrite-tty-no-init"),
        pytest.param(False, True, False, None, ExitCode.OK, "", id="overwrite-no-tty-no-init"),
    ],
)
def test_from_ansible_overwrite(
    tmp_path: Path,
    click_runner: CliRunner,
    temp_env: dict[str, str | None],
    env_set: bool,
    overwrite: bool,
    is_tty: bool,
    prompt: str | None,
    expected_exit: int,
    expected_log: str | None,
) -> None:
    """Test `anta get from-ansible` overwrite mechanism.

    The test uses a static ansible-inventory and output as these are tested in other functions

    This test verifies:
    * that overwrite is working as expected with or without init data in the target file
    * that when the target file is not empty and a tty is present, the user is prompt with confirmation
    * Check the behavior when the prompt is filled

    The initial content of the ANTA inventory is set using init_anta_inventory, if it is None, no inventory is set.

    * With overwrite True, the expectation is that the from-ansible command succeeds
    * With no init (init_anta_inventory == None), the expectation is also that command succeeds
    """
    ansible_inventory_path = DATA_DIR / "ansible_inventory.yml"
    expected_anta_inventory_path = DATA_DIR / "expected_anta_inventory.yml"
    tmp_output = tmp_path / "output.yml"
    cli_args = [
        "get",
        "from-ansible",
        "--ansible-inventory",
        str(ansible_inventory_path),
    ]

    if env_set:
        tmp_inv = Path(str(temp_env["ANTA_INVENTORY"]))
    else:
        temp_env["ANTA_INVENTORY"] = None
        tmp_inv = tmp_output
        cli_args.extend(["--output", str(tmp_output)])

    if overwrite:
        cli_args.append("--overwrite")

    # Verify initial content is different
    if tmp_inv.exists():
        assert not filecmp.cmp(tmp_inv, expected_anta_inventory_path)

    with patch("sys.stdin.isatty", return_value=is_tty):
        result = click_runner.invoke(anta, cli_args, env=temp_env, input=prompt)

    assert result.exit_code == expected_exit
    if expected_exit == ExitCode.OK:
        assert filecmp.cmp(tmp_inv, expected_anta_inventory_path)
    elif expected_exit == ExitCode.INTERNAL_ERROR:
        assert expected_log
        assert expected_log in result.output


@pytest.mark.parametrize(
    ("module", "test_name", "short", "expected_output"),
    [
        pytest.param(
            None,
            None,
            False,
            "VerifyAcctConsoleMethods",
            id="Get all tests",
        ),
        pytest.param(
            "anta.tests.aaa",
            None,
            False,
            "VerifyAcctConsoleMethods",
            id="Get tests, filter on module",
        ),
        pytest.param(
            None,
            "VerifyNTPAssociations",
            False,
            "VerifyNTPAssociations",
            id="Get tests, filter on exact test name",
        ),
        pytest.param(
            None,
            "VerifyNTP",
            False,
            "anta.tests.system",
            id="Get tests, filter on included test name",
        ),
        pytest.param(
            None,
            "VerifyNTP",
            True,
            "VerifyNTPAssociations",
            id="Get tests --short",
        ),
        pytest.param(
            "unknown_module",
            None,
            True,
            "",
            id="Get tests wrong module",
        ),
        pytest.param(
            None,
            "VerifySomething",
            True,
            "",
            id="Get tests wrong test name",
        ),
        pytest.param(
            "anta.tests.aaa",
            "VerifyNTP",
            True,
            "",
            id="Get tests test exists but not in module",
        ),
    ],
)
def test_get_tests(click_runner: CliRunner, module: str | None, test_name: str | None, *, short: bool, expected_output: str) -> None:
    """Test `anta get tests`.

    The test uses a static ansible-inventory and output as these are tested in other functions

    This test verifies:
    * that overwrite is working as expected with or without init data in the target file
    * that when the target file is not empty and a tty is present, the user is prompt with confirmation
    * Check the behavior when the prompt is filled

    The initial content of the ANTA inventory is set using init_anta_inventory, if it is None, no inventory is set.

    * With overwrite True, the expectation is that the from-ansible command succeeds
    * With no init (init_anta_inventory == None), the expectation is also that command succeeds
    """
    cli_args = [
        "get",
        "tests",
    ]
    if module is not None:
        cli_args.extend(["--module", module])

    if test_name is not None:
        cli_args.extend(["--test", test_name])

    if short:
        cli_args.append("--short")

    result = click_runner.invoke(anta, cli_args)

    assert result.exit_code == ExitCode.OK
    assert expected_output in result.output
