# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.get.utils."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from anta.cli.get.utils import create_inventory_from_ansible, create_inventory_from_cvp, get_cv_token
from anta.inventory import AntaInventory

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


def test_get_cv_token() -> None:
    """Test anta.get.utils.get_cv_token."""
    ip = "42.42.42.42"
    username = "ant"
    password = "formica"

    with patch("anta.cli.get.utils.requests.request") as patched_request:
        mocked_ret = MagicMock(autospec=requests.Response)
        mocked_ret.json.return_value = {"sessionId": "simple"}
        patched_request.return_value = mocked_ret
        res = get_cv_token(ip, username, password)
    patched_request.assert_called_once_with(
        "POST",
        "https://42.42.42.42/cvpservice/login/authenticate.do",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        data='{"userId": "ant", "password": "formica"}',
        verify=False,
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
    ("inventory_filename", "ansible_group", "expected_raise", "expected_inv_length"),
    [
        pytest.param("ansible_inventory.yml", None, nullcontext(), 7, id="no group"),
        pytest.param("ansible_inventory.yml", "ATD_LEAFS", nullcontext(), 4, id="group found"),
        pytest.param(
            "ansible_inventory.yml",
            "DUMMY",
            pytest.raises(ValueError, match="Group DUMMY not found in Ansible inventory"),
            0,
            id="group not found",
        ),
        pytest.param(
            "empty_ansible_inventory.yml",
            None,
            pytest.raises(ValueError, match="Ansible inventory .* is empty"),
            0,
            id="empty inventory",
        ),
        pytest.param(
            "wrong_ansible_inventory.yml",
            None,
            pytest.raises(ValueError, match="Could not parse"),
            0,
            id="os error inventory",
        ),
    ],
)
def test_create_inventory_from_ansible(
    tmp_path: Path,
    inventory_filename: Path,
    ansible_group: str | None,
    expected_raise: AbstractContextManager[Exception],
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
