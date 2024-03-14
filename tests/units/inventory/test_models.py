# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Inventory models unit tests."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from pydantic import ValidationError

from anta.device import AsyncEOSDevice
from anta.inventory.models import AntaInventoryHost, AntaInventoryInput, AntaInventoryNetwork, AntaInventoryRange
from tests.data.json_data import (
    INVENTORY_DEVICE_MODEL_INVALID,
    INVENTORY_DEVICE_MODEL_VALID,
    INVENTORY_MODEL_HOST_CACHE,
    INVENTORY_MODEL_HOST_INVALID,
    INVENTORY_MODEL_HOST_VALID,
    INVENTORY_MODEL_INVALID,
    INVENTORY_MODEL_NETWORK_CACHE,
    INVENTORY_MODEL_NETWORK_INVALID,
    INVENTORY_MODEL_NETWORK_VALID,
    INVENTORY_MODEL_RANGE_CACHE,
    INVENTORY_MODEL_RANGE_INVALID,
    INVENTORY_MODEL_RANGE_VALID,
    INVENTORY_MODEL_VALID,
)
from tests.lib.utils import generate_test_ids_dict


class TestInventoryUnitModels:
    """Test components of AntaInventoryInput model."""

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_HOST_VALID, ids=generate_test_ids_dict)
    def test_anta_inventory_host_valid(self, test_definition: dict[str, Any]) -> None:
        """Test host input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Host',
            'input': '1.1.1.1',
            'expected_result': 'valid'
         }

        """
        try:
            host_inventory = AntaInventoryHost(host=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            raise AssertionError from exc
        assert test_definition["input"] == str(host_inventory.host)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_HOST_INVALID, ids=generate_test_ids_dict)
    def test_anta_inventory_host_invalid(self, test_definition: dict[str, Any]) -> None:
        """Test host input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Host',
            'input': '1.1.1.1/32',
            'expected_result': 'invalid'
         }

        """
        with pytest.raises(ValidationError):
            AntaInventoryHost(host=test_definition["input"])

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_HOST_CACHE, ids=generate_test_ids_dict)
    def test_anta_inventory_host_cache(self, test_definition: dict[str, Any]) -> None:
        """Test host disable_cache.

        Test structure:
        ---------------

        {
            'name': 'Cache',
            'input': {"host": '1.1.1.1', "disable_cache": True},
            'expected_result': True
         }

        """
        if "disable_cache" in test_definition["input"]:
            host_inventory = AntaInventoryHost(host=test_definition["input"]["host"], disable_cache=test_definition["input"]["disable_cache"])
        else:
            host_inventory = AntaInventoryHost(host=test_definition["input"]["host"])
        assert test_definition["expected_result"] == host_inventory.disable_cache

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_NETWORK_VALID, ids=generate_test_ids_dict)
    def test_anta_inventory_network_valid(self, test_definition: dict[str, Any]) -> None:
        """Test Network input model with valid data.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Subnet',
            'input': '1.1.1.0/24',
            'expected_result': 'valid'
         }

        """
        try:
            network_inventory = AntaInventoryNetwork(network=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            raise AssertionError from exc
        assert test_definition["input"] == str(network_inventory.network)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_NETWORK_INVALID, ids=generate_test_ids_dict)
    def test_anta_inventory_network_invalid(self, test_definition: dict[str, Any]) -> None:
        """Test Network input model with invalid data.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Subnet',
            'input': '1.1.1.0/16',
            'expected_result': 'invalid'
         }

        """
        try:
            AntaInventoryNetwork(network=test_definition["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            raise AssertionError

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_NETWORK_CACHE, ids=generate_test_ids_dict)
    def test_anta_inventory_network_cache(self, test_definition: dict[str, Any]) -> None:
        """Test network disable_cache.

        Test structure:
        ---------------

        {
            'name': 'Cache',
            'input': {"network": '1.1.1.1/24', "disable_cache": True},
            'expected_result': True
         }

        """
        if "disable_cache" in test_definition["input"]:
            network_inventory = AntaInventoryNetwork(network=test_definition["input"]["network"], disable_cache=test_definition["input"]["disable_cache"])
        else:
            network_inventory = AntaInventoryNetwork(network=test_definition["input"]["network"])
        assert test_definition["expected_result"] == network_inventory.disable_cache

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_RANGE_VALID, ids=generate_test_ids_dict)
    def test_anta_inventory_range_valid(self, test_definition: dict[str, Any]) -> None:
        """Test range input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Range',
            'input': {'start':'10.1.0.1', 'end':'10.1.0.10'},
            'expected_result': 'valid'
         }

        """
        try:
            range_inventory = AntaInventoryRange(
                start=test_definition["input"]["start"],
                end=test_definition["input"]["end"],
            )
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            raise AssertionError from exc
        assert test_definition["input"]["start"] == str(range_inventory.start)
        assert test_definition["input"]["end"] == str(range_inventory.end)

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_RANGE_INVALID, ids=generate_test_ids_dict)
    def test_anta_inventory_range_invalid(self, test_definition: dict[str, Any]) -> None:
        """Test range input model.

        Test structure:
        ---------------

        {
            'name': 'ValidIPv4_Range',
            'input': {'start':'10.1.0.1', 'end':'10.1.0.10/32'},
            'expected_result': 'invalid'
         }

        """
        try:
            AntaInventoryRange(
                start=test_definition["input"]["start"],
                end=test_definition["input"]["end"],
            )
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            raise AssertionError

    @pytest.mark.parametrize("test_definition", INVENTORY_MODEL_RANGE_CACHE, ids=generate_test_ids_dict)
    def test_anta_inventory_range_cache(self, test_definition: dict[str, Any]) -> None:
        """Test range disable_cache.

        Test structure:
        ---------------

        {
            'name': 'Cache',
            'input': {"start": '1.1.1.1', "end": "1.1.1.10", "disable_cache": True},
            'expected_result': True
         }

        """
        if "disable_cache" in test_definition["input"]:
            range_inventory = AntaInventoryRange(
                start=test_definition["input"]["start"],
                end=test_definition["input"]["end"],
                disable_cache=test_definition["input"]["disable_cache"],
            )
        else:
            range_inventory = AntaInventoryRange(start=test_definition["input"]["start"], end=test_definition["input"]["end"])
        assert test_definition["expected_result"] == range_inventory.disable_cache


class TestAntaInventoryInputModel:
    """Unit test of AntaInventoryInput model."""

    def test_inventory_input_structure(self) -> None:
        """Test inventory keys are those expected."""
        inventory = AntaInventoryInput()
        logging.info("Inventory keys are: %s", str(inventory.model_dump().keys()))
        assert all(elem in inventory.model_dump() for elem in ["hosts", "networks", "ranges"])

    @pytest.mark.parametrize("inventory_def", INVENTORY_MODEL_VALID, ids=generate_test_ids_dict)
    def test_anta_inventory_intput_valid(self, inventory_def: dict[str, Any]) -> None:
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
        try:
            inventory = AntaInventoryInput(**inventory_def["input"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
            raise AssertionError from exc
        logging.info("Checking if all root keys are correctly lodaded")
        assert all(elem in inventory.model_dump() for elem in inventory_def["input"])

    @pytest.mark.parametrize("inventory_def", INVENTORY_MODEL_INVALID, ids=generate_test_ids_dict)
    def test_anta_inventory_intput_invalid(self, inventory_def: dict[str, Any]) -> None:
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
        try:
            if "hosts" in inventory_def["input"]:
                logging.info(
                    "Loading %s into AntaInventoryInput hosts section",
                    str(inventory_def["input"]["hosts"]),
                )
                AntaInventoryInput(hosts=inventory_def["input"]["hosts"])
            if "networks" in inventory_def["input"]:
                logging.info(
                    "Loading %s into AntaInventoryInput networks section",
                    str(inventory_def["input"]["networks"]),
                )
                AntaInventoryInput(networks=inventory_def["input"]["networks"])
            if "ranges" in inventory_def["input"]:
                logging.info(
                    "Loading %s into AntaInventoryInput ranges section",
                    str(inventory_def["input"]["ranges"]),
                )
                AntaInventoryInput(ranges=inventory_def["input"]["ranges"])
        except ValidationError as exc:
            logging.warning("Error: %s", str(exc))
        else:
            raise AssertionError


class TestInventoryDeviceModel:
    """Unit test of InventoryDevice model."""

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL_VALID, ids=generate_test_ids_dict)
    def test_inventory_device_valid(self, test_definition: dict[str, Any]) -> None:
        """Test loading valid data to InventoryDevice class.

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

        try:
            for entity in test_definition["input"]:
                AsyncEOSDevice(**entity)
        except TypeError as exc:
            logging.warning("Error: %s", str(exc))
            raise AssertionError from exc

    @pytest.mark.parametrize("test_definition", INVENTORY_DEVICE_MODEL_INVALID, ids=generate_test_ids_dict)
    def test_inventory_device_invalid(self, test_definition: dict[str, Any]) -> None:
        """Test loading invalid data to InventoryDevice class.

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

        try:
            for entity in test_definition["input"]:
                AsyncEOSDevice(**entity)
        except TypeError as exc:
            logging.info("Error: %s", str(exc))
        else:
            raise AssertionError
