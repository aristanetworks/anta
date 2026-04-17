# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Inventory unit tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchemaError, InventoryRootKeyError

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.mark.structures import ParameterSet

    from anta.device import AntaDevice, AsyncEOSDevice


INIT_VALID_PARAMS: list[ParameterSet] = [
    pytest.param(
        {"anta_inventory": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2"}, {"host": "my.awesome.host.com"}]}},
        id="Inventory_with_host_only",
    ),
    pytest.param({"anta_inventory": {"networks": [{"network": "192.168.0.0/24"}]}}, id="ValidInventory_with_networks_only"),
    pytest.param(
        {"anta_inventory": {"ranges": [{"start": "10.0.0.1", "end": "10.0.0.11"}, {"start": "10.0.0.101", "end": "10.0.0.111"}]}},
        id="Inventory_with_ranges_only",
    ),
    pytest.param(
        {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "port": 443}, {"host": "192.168.0.2", "port": 80}]}},
        id="Inventory_with_host_port",
    ),
    pytest.param(
        {"anta_inventory": {"hosts": [{"host": "192.168.0.17", "tags": ["leaf"]}, {"host": "192.168.0.2", "tags": ["spine"]}]}},
        id="Inventory_with_host_tags",
    ),
    pytest.param({"anta_inventory": {"networks": [{"network": "192.168.0.0/24", "tags": ["leaf"]}]}}, id="ValidInventory_with_networks_tags"),
    pytest.param(
        {
            "anta_inventory": {
                "ranges": [{"start": "10.0.0.1", "end": "10.0.0.11", "tags": ["leaf"]}, {"start": "10.0.0.101", "end": "10.0.0.111", "tags": ["spine"]}]
            }
        },
        id="Inventory_with_ranges_tags",
    ),
]


INIT_INVALID_PARAMS = [
    pytest.param({"anta_inventory": {"hosts": [{"host": "192.168.0.17/32"}, {"host": "192.168.0.2"}]}}, id="Inventory_with_host_only"),
    pytest.param({"anta_inventory": {"networks": [{"network": "192.168.42.0/8"}]}}, id="Inventory_wrong_network_bits"),
    pytest.param({"anta_inventory": {"networks": [{"network": "toto"}]}}, id="Inventory_wrong_network"),
    pytest.param({"anta_inventory": {"ranges": [{"start": "toto", "end": "192.168.42.42"}]}}, id="Inventory_wrong_range"),
    pytest.param({"anta_inventory": {"ranges": [{"start": "fe80::cafe", "end": "192.168.42.42"}]}}, id="Inventory_wrong_range_type_mismatch"),
    pytest.param(
        {"inventory": {"ranges": [{"start": "10.0.0.1", "end": "10.0.0.11"}, {"start": "10.0.0.100", "end": "10.0.0.111"}]}},
        id="Invalid_Root_Key",
    ),
]


class TestAntaInventory:
    """Tests for anta.inventory.AntaInventory."""

    @pytest.mark.parametrize("yaml_file", INIT_VALID_PARAMS, indirect=["yaml_file"])
    def test_parse_valid(self, yaml_file: Path) -> None:
        """Parse valid YAML file to create ANTA inventory."""
        AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")

    @pytest.mark.parametrize("yaml_file", INIT_INVALID_PARAMS, indirect=["yaml_file"])
    def test_parse_invalid(self, yaml_file: Path) -> None:
        """Parse invalid YAML file to create ANTA inventory."""
        with pytest.raises((InventoryIncorrectSchemaError, InventoryRootKeyError, ValidationError)):
            AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")

    def test_parse_wrong_format(self) -> None:
        """Use wrong file format to parse the ANTA inventory."""
        with pytest.raises(ValueError, match=r" is not a valid format for an AntaInventory file. Only 'yaml' and 'json' are supported."):
            AntaInventory.parse(filename="dummy.yml", username="arista", password="arista123", file_format="wrong")  # type: ignore[arg-type]

    def test_parse_os_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Use wrong file name to parse the ANTA inventory."""
        caplog.set_level(logging.INFO)
        with pytest.raises(OSError, match=r"No such file or directory"):
            _ = AntaInventory.parse(filename="dummy.yml", username="arista", password="arista123")
        assert "Unable to parse ANTA Device Inventory file" in caplog.records[0].message

    @pytest.mark.parametrize(("inventory"), [{"count": 3}], indirect=True)
    def test_max_potential_connections(self, inventory: AntaInventory) -> None:
        """Test max_potential_connections property with regular AsyncEOSDevice objects in the inventory."""
        # Each AsyncEOSDevice has a max_connections of 100
        assert inventory.max_potential_connections == 300

    @pytest.mark.parametrize(("device"), [{"name": "anta_device"}], indirect=True)
    def test_get_potential_connections_custom_anta_device(self, caplog: pytest.LogCaptureFixture, async_device: AsyncEOSDevice, device: AntaDevice) -> None:
        """Test max_potential_connections property with an AntaDevice with no max_connections in the inventory."""
        caplog.set_level(logging.DEBUG)

        inventory = AntaInventory()
        inventory.add_device(async_device)
        inventory.add_device(device)

        assert len(inventory) == 2
        assert inventory.max_potential_connections is None
        assert "Device anta_device 'max_connections' is not available" in caplog.messages
