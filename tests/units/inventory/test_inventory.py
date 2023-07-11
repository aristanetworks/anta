"""ANTA Inventory unit tests."""

import logging
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from pydantic import ValidationError

from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyError
from tests.data.json_data import ANTA_INVENTORY_TESTS_INVALID, ANTA_INVENTORY_TESTS_VALID
from tests.lib.utils import generate_test_ids_dict


class Test_AntaInventory:
    """Test AntaInventory class."""

    def create_inventory(self, content: str, tmp_path: Path) -> str:
        """Create fakefs inventory file."""
        tmp_inventory = tmp_path / "mydir/myfile"
        tmp_inventory.parent.mkdir()
        tmp_inventory.touch()
        tmp_inventory.write_text(yaml.dump(content, allow_unicode=True))
        return str(tmp_inventory)

    def check_parameter(self, parameter: str, test_definition: Dict[Any, Any]) -> bool:
        """Check if parameter is configured in testbed."""
        return "parameters" in test_definition and parameter in test_definition["parameters"].keys()

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS_VALID, ids=generate_test_ids_dict)
    def test_init_valid(self, test_definition: Dict[str, Any], tmp_path: Path) -> None:
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
            AntaInventory.parse(inventory_file=inventory_file, username="arista", password="arista123")
        except ValidationError as exc:
            logging.error("Exceptions is: %s", str(exc))
            assert False

    @pytest.mark.parametrize("test_definition", ANTA_INVENTORY_TESTS_INVALID, ids=generate_test_ids_dict)
    def test_init_invalid(self, test_definition: Dict[str, Any], tmp_path: Path) -> None:
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
        try:
            AntaInventory.parse(inventory_file=inventory_file, username="arista", password="arista123")
        except InventoryIncorrectSchema as exc:
            logging.warning("Exception is: %s", exc)
        except InventoryRootKeyError as exc:
            logging.warning("Exception is: %s", exc)
        else:
            assert False
