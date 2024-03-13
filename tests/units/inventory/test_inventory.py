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
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError
from tests.data.json_data import ANTA_INVENTORY_TESTS_INVALID, ANTA_INVENTORY_TESTS_VALID
from tests.lib.utils import generate_test_ids_dict

if TYPE_CHECKING:
    from pathlib import Path


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
        return (
            "parameters" in test_definition
            and parameter in test_definition["parameters"]
        )

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS_VALID, ids=generate_test_ids_dict
    )
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
        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        try:
            AntaInventory.parse(
                filename=inventory_file, username="arista", password="arista123"
            )
        except ValidationError as exc:
            raise AssertionError from exc

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS_INVALID, ids=generate_test_ids_dict
    )
    def test_init_invalid(
        self, test_definition: dict[str, Any], tmp_path: Path
    ) -> None:
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
        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        with pytest.raises(
            (InventoryIncorrectSchema, InventoryRootKeyError, ValidationError)
        ):
            AntaInventory.parse(
                filename=inventory_file, username="arista", password="arista123"
            )
