#!/usr/bin/python
# coding: utf-8 -*-

"""ANTA Inventory unit tests."""

import json
import logging
from typing import Dict, Any
from pathlib import Path

import pytest
import yaml

from pydantic import ValidationError
from anta.inventory import AntaInventory
from anta.inventory.models import InventoryDevice
from anta.inventory.exceptions import InventoryIncorrectSchema, InventoryRootKeyErrors
from tests.data.utils import generate_test_ids_dict
from tests.data.json_data import ANTA_INVENTORY_TESTS


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
        if (
            "parameters" not in test_definition.keys()
            or parameter not in test_definition["parameters"].keys()
        ):
            return False
        return True

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
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

        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        try:
            AntaInventory(
                inventory_file=inventory_file,
                username="arista",
                password="arista123",
                auto_connect=False,
            )
        except ValidationError as exc:
            logging.error("Exceptions is: %s", str(exc))
            assert False
        else:
            assert True

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
    def test_init_invalid(
        self, test_definition: Dict[str, Any], tmp_path: Path
    ) -> None:
        """Test class constructor with invalid data.

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

        if test_definition["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        try:
            AntaInventory(
                inventory_file=inventory_file,
                username="arista",
                password="arista123",
                auto_connect=False,
            )
        except InventoryIncorrectSchema as exc:
            logging.warning("Exception is: %s", exc)
            assert True
        except InventoryRootKeyErrors as exc:
            logging.warning("Exception is: %s", exc)
            assert True
        else:
            assert False

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
    def test_is_ip_exists(
        self, test_definition: Dict[str, Any], tmp_path: Path
    ) -> None:
        """Test _is_ip_exists with valid data.

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

        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        if not self.check_parameter(
            parameter="ipaddress_in_scope", test_definition=test_definition
        ):
            pytest.skip("Test data has no ipaddress parameter configured")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username="arista",
            password="arista123",
            auto_connect=False,
        )
        logging.info(
            "Checking if %s is in inventory",
            str(test_definition["parameters"]["ipaddress_in_scope"]),
        )
        assert inventory_test._is_ip_exist(  # pylint: disable=protected-access
            ip=test_definition["parameters"]["ipaddress_in_scope"]
        )

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
    def test_is_ip_exists_false(
        self, test_definition: Dict[str, Any], tmp_path: Path
    ) -> None:
        """Test _is_ip_exists with invalid data.

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
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        if not self.check_parameter(
            parameter="ipaddress_out_of_scope", test_definition=test_definition
        ):
            pytest.skip("Test data has no ipaddress parameter configured")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username="arista",
            password="arista123",
            auto_connect=False,
        )
        logging.info(
            "Checking if %s is in inventory",
            str(test_definition["parameters"]["ipaddress_out_of_scope"]),
        )
        assert not inventory_test._is_ip_exist(  # pylint: disable=protected-access
            ip=test_definition["parameters"]["ipaddress_out_of_scope"]
        )

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
    def test_device_get(self, test_definition: Dict[str, Any], tmp_path: Path) -> None:
        """Test device_get function.

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
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        if not self.check_parameter(
            parameter="ipaddress_in_scope", test_definition=test_definition
        ):
            pytest.skip("Test data has no ipaddress parameter configured")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username="arista",
            password="arista123",
            auto_connect=False,
        )
        logging.info(
            "Getting if %s from inventory",
            str(test_definition["parameters"]["ipaddress_in_scope"]),
        )
        device = inventory_test.get_device(
            host_ip=str(test_definition["parameters"]["ipaddress_in_scope"])
        )
        assert isinstance(device, InventoryDevice)
        assert str(device.host) == str(
            test_definition["parameters"]["ipaddress_in_scope"]
        )

    @pytest.mark.parametrize(
        "test_definition", ANTA_INVENTORY_TESTS, ids=generate_test_ids_dict
    )
    def test_inventory_get_json(
        self, test_definition: Dict[str, Any], tmp_path: Path
    ) -> None:
        """Test device_get function.

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
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        if not self.check_parameter(
            parameter="ipaddress_in_scope", test_definition=test_definition
        ):
            pytest.skip("Test data has no ipaddress_in_scope parameter configured")

        if not self.check_parameter(
            parameter="nb_hosts", test_definition=test_definition
        ):
            pytest.skip("Test data has no nb_hosts parameter configured")

        inventory_file = self.create_inventory(
            content=test_definition["input"], tmp_path=tmp_path
        )
        inventory_test = AntaInventory(
            inventory_file=inventory_file,
            username="arista",
            password="arista123",
            auto_connect=False,
        )
        inventory_json = json.loads(
            str(inventory_test.get_inventory(format_out="json", established_only=False))
        )
        assert test_definition["parameters"]["ipaddress_in_scope"] in [
            d["host"] for d in inventory_json
        ]
        assert int(test_definition["parameters"]["nb_hosts"]) == len(
            [d["host"] for d in inventory_json]
        )
