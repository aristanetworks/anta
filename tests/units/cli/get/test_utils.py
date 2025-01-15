# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.get.utils."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest
import requests

from anta.cli.get.utils import create_inventory_from_ansible, create_inventory_from_cvp, extract_examples, find_tests_examples, get_cv_token, print_test
from anta.inventory import AntaInventory
from anta.models import AntaCommand, AntaTemplate, AntaTest

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


@pytest.mark.parametrize(
    "verify_cert",
    [
        pytest.param(True, id="Verify cert enabled"),
        pytest.param(False, id="Verify cert disabled"),
    ],
)
def test_get_cv_token(verify_cert: bool) -> None:
    """Test anta.get.utils.get_cv_token."""
    ip_addr = "42.42.42.42"
    username = "ant"
    password = "formica"

    with patch("anta.cli.get.utils.requests.request") as patched_request:
        mocked_ret = MagicMock(autospec=requests.Response)
        mocked_ret.json.return_value = {"sessionId": "simple"}
        patched_request.return_value = mocked_ret
        res = get_cv_token(ip_addr, username, password, verify_cert=verify_cert)
    patched_request.assert_called_once_with(
        "POST",
        "https://42.42.42.42/cvpservice/login/authenticate.do",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        data='{"userId": "ant", "password": "formica"}',
        verify=verify_cert,
        timeout=10,
    )
    assert res == "simple"


# truncated inventories
CVP_INVENTORY = [
    {
        "hostname": "device1",
        "containerName": "DC1",
        "ipAddress": "10.20.20.97",
    },
    {
        "hostname": "device2",
        "containerName": "DC2",
        "ipAddress": "10.20.20.98",
    },
    {
        "hostname": "device3",
        "containerName": "",
        "ipAddress": "10.20.20.99",
    },
]


@pytest.mark.parametrize(
    "inventory",
    [
        pytest.param(CVP_INVENTORY, id="some container"),
        pytest.param([], id="empty_inventory"),
    ],
)
def test_create_inventory_from_cvp(tmp_path: Path, inventory: list[dict[str, Any]]) -> None:
    """Test anta.get.utils.create_inventory_from_cvp."""
    output = tmp_path / "output.yml"

    create_inventory_from_cvp(inventory, output)

    assert output.exists()
    # This validate the file structure ;)
    inv = AntaInventory.parse(str(output), "user", "pass")
    assert len(inv) == len(inventory)


@pytest.mark.parametrize(
    ("inventory_filename", "ansible_group", "expected_raise", "expected_log", "expected_inv_length"),
    [
        pytest.param("ansible_inventory.yml", None, nullcontext(), None, 7, id="no group"),
        pytest.param("ansible_inventory.yml", "ATD_LEAFS", nullcontext(), None, 4, id="group found"),
        pytest.param(
            "ansible_inventory.yml",
            "DUMMY",
            pytest.raises(ValueError, match="Group DUMMY not found in Ansible inventory"),
            None,
            0,
            id="group not found",
        ),
        pytest.param(
            "empty_ansible_inventory.yml",
            None,
            pytest.raises(ValueError, match="Ansible inventory .* is empty"),
            None,
            0,
            id="empty inventory",
        ),
        pytest.param(
            "wrong_ansible_inventory.yml",
            None,
            pytest.raises(ValueError, match="Could not parse"),
            None,
            0,
            id="os error inventory",
        ),
        pytest.param(
            "ansible_inventory_with_vault.yml",
            None,
            pytest.raises(ValueError, match="Could not parse"),
            "`anta get from-ansible` does not support inline vaulted variables",
            0,
            id="Vault variable in inventory",
        ),
        pytest.param(
            "ansible_inventory_unknown_yaml_tag.yml",
            None,
            pytest.raises(ValueError, match="Could not parse"),
            None,
            0,
            id="Unknown YAML tag in inventory",
        ),
    ],
)
def test_create_inventory_from_ansible(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
    inventory_filename: Path,
    ansible_group: str | None,
    expected_raise: AbstractContextManager[Exception],
    expected_log: str | None,
    expected_inv_length: int,
) -> None:
    """Test anta.get.utils.create_inventory_from_ansible."""
    target_file = tmp_path / "inventory.yml"
    inventory_file_path = DATA_DIR / inventory_filename

    with expected_raise:
        if ansible_group:
            create_inventory_from_ansible(inventory_file_path, target_file, ansible_group)
        else:
            create_inventory_from_ansible(inventory_file_path, target_file)

        assert target_file.exists()
        inv = AntaInventory().parse(str(target_file), "user", "pass")
        assert len(inv) == expected_inv_length
    if not isinstance(expected_raise, nullcontext):
        assert not target_file.exists()
        if expected_log:
            assert expected_log in caplog.text


class MissingExampleTest(AntaTest):
    """ANTA test that always succeed but has no Examples section."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class EmptyExampleTest(AntaTest):
    """ANTA test that always succeed but has an empty Examples section.

    Examples
    --------
    """

    # For the test purpose we want am empty section as custom tests could not be using ruff.
    # ruff: noqa:  D414

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


class TypoExampleTest(AntaTest):
    """ANTA test that always succeed but has a Typo in the test name in the example.

    Notice capital P in TyPo below.

    Examples
    --------
    ```yaml
    tests.units.cli.get.test_utils:
      - TyPoExampleTest:
    ```
    """

    # For the test purpose we want am empty section as custom tests could not be using ruff.
    # ruff: noqa:  D414

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []

    @AntaTest.anta_test
    def test(self) -> None:
        """Test function."""
        self.result.is_success()


def test_find_tests_examples() -> None:
    """Test find_tests_examples.

    Only testing the failure scenarii not tested through test_commands.
    TODO: expand
    """
    with pytest.raises(ValueError, match="Error when importing"):
        find_tests_examples("blah", "UnusedTestName")


def test_print_test() -> None:
    """Test print_test."""
    with pytest.raises(ValueError, match="Could not find the name of the test"):
        print_test(TypoExampleTest)
    with pytest.raises(LookupError, match="is missing an Example"):
        print_test(MissingExampleTest)
    with pytest.raises(LookupError, match="is missing an Example"):
        print_test(EmptyExampleTest)


def test_extract_examples() -> None:
    """Test extract_examples.

    Only testing the case where the 'Examples' is missing as everything else
    is covered already in test_commands.py.
    """
    assert MissingExampleTest.__doc__ is not None
    assert EmptyExampleTest.__doc__ is not None
    assert extract_examples(MissingExampleTest.__doc__) is None
    assert extract_examples(EmptyExampleTest.__doc__) is None
