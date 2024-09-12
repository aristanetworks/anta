# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Inventory unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import yaml
from pydantic import ValidationError

from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchemaError, InventoryRootKeyError
from tests.lib.utils import generate_test_ids_dict

if TYPE_CHECKING:
    from pathlib import Path


ANTA_INVENTORY_TESTS_VALID = [
    {
        "name": "ValidInventory_with_host_only",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2"}, {"host": "my.awesome.host.com"}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_networks_only",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.0.0/24"}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.1",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 256,
        },
    },
    {
        "name": "ValidInventory_with_ranges_only",
        "input": {
            "anta_inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11"},
                    {"start": "10.0.0.101", "end": "10.0.0.111"},
                ],
            },
        },
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "10.0.0.10",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 22,
        },
    },
    {
        "name": "ValidInventory_with_host_port",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "port": 443}, {"host": "192.168.0.2", "port": 80}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_host_tags",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "tags": ["leaf"]}, {"host": "192.168.0.2", "tags": ["spine"]}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.17",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 2,
        },
    },
    {
        "name": "ValidInventory_with_networks_tags",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.0.0/24", "tags": ["leaf"]}]}},
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "192.168.0.1",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 256,
        },
    },
    {
        "name": "ValidInventory_with_ranges_tags",
        "input": {
            "anta_inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11", "tags": ["leaf"]},
                    {"start": "10.0.0.101", "end": "10.0.0.111", "tags": ["spine"]},
                ],
            },
        },
        "expected_result": "valid",
        "parameters": {
            "ipaddress_in_scope": "10.0.0.10",
            "ipaddress_out_of_scope": "192.168.1.1",
            "nb_hosts": 22,
        },
    },
]


ANTA_INVENTORY_TESTS_INVALID = [
    {
        "name": "InvalidInventory_with_host_only",
        "input": {"anta_inventory": {"hosts": [{"host": "192.168.0.17/32"}, {"host": "192.168.0.2"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_network_bits",
        "input": {"anta_inventory": {"networks": [{"network": "192.168.42.0/8"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_network",
        "input": {"anta_inventory": {"networks": [{"network": "toto"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_range",
        "input": {"anta_inventory": {"ranges": [{"start": "toto", "end": "192.168.42.42"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "InvalidInventory_wrong_range_type_mismatch",
        "input": {"anta_inventory": {"ranges": [{"start": "fe80::cafe", "end": "192.168.42.42"}]}},
        "expected_result": "invalid",
    },
    {
        "name": "Invalid_Root_Key",
        "input": {
            "inventory": {
                "ranges": [
                    {"start": "10.0.0.1", "end": "10.0.0.11"},
                    {"start": "10.0.0.100", "end": "10.0.0.111"},
                ],
            },
        },
        "expected_result": "invalid",
    },
]


class TestAntaInventory:
    """Test AntaInventory class."""

    def create_inventory(self, content: str, tmp_path: Path) -> str:
        """Create fakefs inventory file."""
        tmp_inventory = tmp_path / "mydir/myfile"
        tmp_inventory.parent.mkdir()
        tmp_inventory.touch()
        tmp_inventory.write_text(yaml.dump(content, allow_unicode=True))
        return str(tmp_inventory)

    def check_parameter(self, parameter: str, test_definition: dict[Any, Any]) -> bool:
        """Check if parameter is configured in testbed."""
        return "parameters" in test_definition and parameter in test_definition["parameters"]

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS_VALID, ids=generate_test_ids_dict)
    def test_init_valid(self, test_definition: dict[str, Any], tmp_path: Path) -> None:
        """Test class constructor with valid data.

        Test structure:
        ---------------

        {
            'name': 'ValidInventory_with_host_only',
            'input': {"anta_inventory":{"hosts":[{"host":"192.168.0.17"},{"host":"192.168.0.2"}]}},
            'expected_result': 'valid',
            'parameters': {
                'ipaddress_in_scope': '192.168.0.17',
                'ipaddress_out_of_scope': '192.168.1.1',
            }
        }

        """
        inventory_file = self.create_inventory(content=test_definition["input"], tmp_path=tmp_path)
        try:
            AntaInventory.parse(filename=inventory_file, username="arista", password="arista123")
        except ValidationError as exc:
            raise AssertionError from exc

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS_INVALID, ids=generate_test_ids_dict)
    def test_init_invalid(self, test_definition: dict[str, Any], tmp_path: Path) -> None:
        """Test class constructor with invalid data.

        Test structure:
        ---------------

        {
            'name': 'ValidInventory_with_host_only',
            'input': {"anta_inventory":{"hosts":[{"host":"192.168.0.17"},{"host":"192.168.0.2"}]}},
            'expected_result': 'invalid',
            'parameters': {
                'ipaddress_in_scope': '192.168.0.17',
                'ipaddress_out_of_scope': '192.168.1.1',
            }
        }

        """
        inventory_file = self.create_inventory(content=test_definition["input"], tmp_path=tmp_path)
        with pytest.raises((InventoryIncorrectSchemaError, InventoryRootKeyError, ValidationError)):
            AntaInventory.parse(filename=inventory_file, username="arista", password="arista123")
