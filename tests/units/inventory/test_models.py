"""ANTA Inventory models unit tests."""

import logging
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from anta.inventory.models import AntaInventoryHost, AntaInventoryInput, AntaInventoryNetwork, AntaInventoryRange, InventoryDeviceAioeapi, InventoryDevices
from tests.data.json_data import INVENTORY_DEVICE_MODEL, INVENTORY_MODEL, INVENTORY_MODEL_HOST, INVENTORY_MODEL_NETWORK, INVENTORY_MODEL_RANGE
from tests.lib.utils import generate_test_ids_dict


class Test_InventoryUnitModels:
    """Test components of AntaInventoryInput model."""

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_HOST, ids=generate_test_ids_dict)
    def test_anta_inventory_host_valid(self, test_definition: Dict[str, Any]) -> None:
        """Test host input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Host',
            'input': '1.1.1.1',
            'expected_result': 'valid'
         }

        """
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        try:
            host_inventory = AntaInventoryHost(host=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            assert False
        else:
            assert test_definition["input"] == str(host_inventory.host)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_HOST, ids=generate_test_ids_dict)
    def test_anta_inventory_host_invalid(self, test_definition: Dict[str, Any]) -> None:
        """Test host input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Host',
            'input': '1.1.1.1/32',
            'expected_result': 'invalid'
         }

        """
        if test_definition["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        with pytest.raises(ValidationError):
            AntaInventoryHost(host=test_definition["input"])

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_NETWORK, ids=generate_test_ids_dict)
    def test_anta_inventory_network_valid(self, test_definition: Dict[str, Any]) -> None:
        """Test Network input model with valid data.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Subnet',
            'input': '1.1.1.0/24',
            'expected_result': 'valid'
         }

        """
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        try:
            network_inventory = AntaInventoryNetwork(network=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            assert False
        else:
            assert test_definition["input"] == str(network_inventory.network)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_NETWORK, ids=generate_test_ids_dict)
    def test_anta_inventory_network_invalid(self, test_definition: Dict[str, Any]) -> None:
        """Test Network input model with invalid data.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Subnet',
            'input': '1.1.1.0/16',
            'expected_result': 'invalid'
         }

        """
        if test_definition["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        try:
            AntaInventoryNetwork(network=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            assert False

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_RANGE, ids=generate_test_ids_dict)
    def test_anta_inventory_range_valid(self, test_definition: Dict[str, Any]) -> None:
        """Test range input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Range',
            'input': {'start':'10.1.0.1', 'end':'10.1.0.10'},
            'expected_result': 'valid'
         }

        """
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        try:
            range_inventory = AntaInventoryRange(
                start=test_definition["input"]["start"],
                end=test_definition["input"]["end"],
            )
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            assert False
        else:
            assert test_definition["input"]["start"] == str(range_inventory.start)
            assert test_definition["input"]["end"] == str(range_inventory.end)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_RANGE, ids=generate_test_ids_dict)
    def test_anta_inventory_range_invalid(self, test_definition: Dict[str, Any]) -> None:
        """Test range input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Range',
            'input': {'start':'10.1.0.1', 'end':'10.1.0.10/32'},
            'expected_result': 'invalid'
         }

        """
        if test_definition["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        try:
            AntaInventoryRange(
                start=test_definition["input"]["start"],
                end=test_definition["input"]["end"],
            )
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            assert False


class Test_AntaInventoryInputModel:
    """Unit test of AntaInventoryInput model."""

    def test_inventory_input_structure(self) -> None:
        """Test inventory keys are those expected."""

        inventory = AntaInventoryInput()
        logging.info("Inventory keys are: %s", str(inventory.dict().keys()))
        assert all(elem in inventory.dict().keys() for elem in ["hosts", "networks", "ranges"])

    @pytest.mark.parametrize("inventory_def", INVENTORY_MODEL, ids=generate_test_ids_dict)
    def test_anta_inventory_intput_valid(self, inventory_def: Dict[str, Any]) -> None:
        """Test loading valid data to inventory class.

        Test structure:
        ---------------

        {
            "name": "Valid_Host_Only",
            "input": {
                "hosts": [
                    {
                        "host": "192.168.0.17"
                    },
                    {
                        "host": "192.168.0.2"
                    }
                ]
            },
            "expected_result": "valid"
        }

        """

        if inventory_def["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        inventory = AntaInventoryInput()
        try:
            if "hosts" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput hosts section",
                    str(inventory_def["input"]["hosts"]),
                )
                inventory.hosts = inventory_def["input"]["hosts"]
            if "networks" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput networks section",
                    str(inventory_def["input"]["networks"]),
                )
                inventory.hosts = inventory_def["input"]["networks"]
            if "ranges" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput ranges section",
                    str(inventory_def["input"]["ranges"]),
                )
                inventory.hosts = inventory_def["input"]["ranges"]
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            assert False
        else:
            logging.info("Checking if all root keys are correctly lodaded")
            assert all(elem in inventory.dict().keys() for elem in inventory_def["input"].keys())

    @pytest.mark.parametrize("inventory_def", INVENTORY_MODEL, ids=generate_test_ids_dict)
    def test_anta_inventory_intput_invalid(self, inventory_def: Dict[str, Any]) -> None:
        """Test loading invalid data to inventory class.

        Test structure:
        ---------------

        {
            "name": "Valid_Host_Only",
            "input": {
                "hosts": [
                    {
                        "host": "192.168.0.17"
                    },
                    {
                        "host": "192.168.0.2/32"
                    }
                ]
            },
            "expected_result": "invalid"
        }

        """

        if inventory_def["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        # inventory_file = self.create_inventory(content=inventory_def['input'], tmp_path=tmp_path)
        try:
            if "hosts" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput hosts section",
                    str(inventory_def["input"]["hosts"]),
                )
                AntaInventoryInput(hosts=inventory_def["input"]["hosts"])
            if "networks" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput networks section",
                    str(inventory_def["input"]["networks"]),
                )
                AntaInventoryInput(networks=inventory_def["input"]["networks"])
            if "ranges" in inventory_def["input"].keys():
                logging.info(
                    "Loading %s into AntaInventoryInput ranges section",
                    str(inventory_def["input"]["ranges"]),
                )
                AntaInventoryInput(ranges=inventory_def["input"]["ranges"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            assert False


class Test_InventoryDeviceModel:
    """Unit test of InventoryDeviceAioeapi model."""

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL, ids=generate_test_ids_dict)
    def test_inventory_device_valid(self, test_definition: Dict[str, Any]) -> None:
        """Test loading valid data to InventoryDeviceAioeapi class.

         Test structure:
         ---------------

        {
             "name": "Valid_Inventory",
             "input": [
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 },
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 }
             ],
             "expected_result": "valid"
         }

        """
        if test_definition["expected_result"] == "invalid":
            pytest.skip("Not concerned by the test")

        for entity in test_definition["input"]:
            try:
                InventoryDeviceAioeapi(**entity)
            except ValidationError as exc:
                logging.warning("Error: %s", str(exc))
                assert False

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL, ids=generate_test_ids_dict)
    def test_inventory_device_invalid(self, test_definition: Dict[str, Any]) -> None:
        """Test loading invalid data to InventoryDeviceAioeapi class.

         Test structure:
         ---------------

        {
             "name": "Valid_Inventory",
             "input": [
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 },
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 }
             ],
             "expected_result": "valid"
         }

        """
        if test_definition["expected_result"] == "valid":
            pytest.skip("Not concerned by the test")

        for entity in test_definition["input"]:
            try:
                InventoryDeviceAioeapi(**entity)
            except ValidationError as exc:
                logging.info("Error: %s", str(exc))
            else:
                assert False

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL, ids=generate_test_ids_dict)
    def test_inventory_devices_len(self, test_definition: Dict[str, Any]) -> None:
        """Test len & append methods for InventoryDeviceAioeapi class.

         Test structure:
         ---------------

        {
             "name": "Invalid_Inventory",
             "input": [
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 },
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 }
             ],
             "expected_result": "valid"
         }

        """
        if test_definition["expected_result"] != "valid":
            pytest.skip("Not concerned by the test")
        inventory_devices = InventoryDevices()
        for entry in test_definition["input"]:
            inventory_devices.append(InventoryDeviceAioeapi(**entry))
        assert len(test_definition["input"]) == len(inventory_devices)

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL, ids=generate_test_ids_dict)
    def test_inventory_devices_get_item(self, test_definition: Dict[str, Any]) -> None:
        """Test __iter__ method for InventoryDeviceAioeapi class.

         Test structure:
         ---------------

        {
             "name": "Invalid_Inventory",
             "input": [
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 },
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 }
             ],
             "expected_result": "valid"
         }

        """
        if test_definition["expected_result"] != "valid":
            pytest.skip("Not concerned by the test")
        inventory_devices = InventoryDevices()
        for entry in test_definition["input"]:
            inventory_devices.append(InventoryDeviceAioeapi(**entry))
        if str(inventory_devices[0].session.host) == test_definition["input"][0]["host"]:
            logging.info("__getitem__ function is valid")
        else:
            logging.error("__getitem__ is not working as expected")
            assert False

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL, ids=generate_test_ids_dict)
    def test_inventory_devices_iter(self, test_definition: Dict[str, Any]) -> None:
        """Test __getitem__ method for InventoryDeviceAioeapi class.

         Test structure:
         ---------------

        {
             "name": "Invalid_Inventory",
             "input": [
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 },
                 {
                     'host': '1.1.1.1',
                     'username': 'arista',
                     'password': 'arista123!'
                 }
             ],
             "expected_result": "valid"
         }

        """
        if test_definition["expected_result"] != "valid":
            pytest.skip("Not concerned by the test")
        inventory_devices = InventoryDevices()
        for entry in test_definition["input"]:
            inventory_devices.append(InventoryDeviceAioeapi(**entry))
        for idx, device in enumerate(inventory_devices):
            if str(device.host) == test_definition["input"][idx].get("host", "localhost"):
                logging.info("__iter__ function is valid")
            else:
                logging.error("__iter__ is not working as expected")
                assert False
