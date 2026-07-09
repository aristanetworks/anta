# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Inventory unit tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from anta.device import AntaDeviceCapabilities, AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.inventory.exceptions import InventoryIncorrectSchemaError, InventoryRootKeyError

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.mark.structures import ParameterSet

    from anta.device import AntaDevice


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
    pytest.param(
        {
            "anta_inventory": {
                "hosts": [{"host": "192.168.0.17", "use_session_auth": True}, {"host": "192.168.0.2", "use_session_auth": True}, {"host": "my.awesome.host.com"}],
                "networks": [{"network": "192.168.0.0/24", "use_session_auth": True}],
                "ranges": [{"start": "10.0.0.1", "end": "10.0.0.11", "use_session_auth": True}, {"start": "10.0.0.101", "end": "10.0.0.111"}],
            }
        },
        id="Inventory_with_use_session_auth",
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

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "hosts": [
                        {"host": "192.168.0.1", "use_session_auth": True},
                        {"host": "192.168.0.2"},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_use_session_auth_propagates_to_asynceapi_device(self, yaml_file: Path) -> None:
        """Verify use_session_auth=True in an inventory entry reaches the underlying asynceapi.Device."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")
        devices_by_host = {device._client.host: device for device in inventory.values() if isinstance(device, AsyncEOSDevice)}

        assert devices_by_host["192.168.0.1"]._client._use_session_auth is True
        assert devices_by_host["192.168.0.2"]._client._use_session_auth is False

    @pytest.mark.parametrize(
        ("cli", "inventory", "expected"),
        [
            # CLI unset: inventory value wins, default is False
            pytest.param(None, False, False, id="cli_unset_inventory_false__default"),
            pytest.param(None, True, True, id="cli_unset_inventory_true__inventory"),
            # CLI --use-session-auth: forces True regardless of inventory
            pytest.param(True, False, True, id="cli_enable_inventory_false__cli"),
            pytest.param(True, True, True, id="cli_enable_inventory_true__cli"),
            # CLI --no-session-auth: forces False regardless of inventory
            pytest.param(False, False, False, id="cli_disable_inventory_false__cli"),
            pytest.param(False, True, False, id="cli_disable_inventory_true__cli_override"),
        ],
    )
    def test_resolve_session_auth(self, cli: bool | None, inventory: bool, expected: bool) -> None:
        """Verify _resolve_session_auth truth table with a supporting device."""
        result = AntaInventory._resolve_session_auth("test-device", AsyncEOSDevice.capabilities, use_session_auth_override=cli, inventory_use_session_auth=inventory)
        assert result is expected

    def test_resolve_session_auth_unsupported_device_inventory_raises(self) -> None:
        """Verify ValueError when inventory requests session auth on an unsupported device."""
        caps = AntaDeviceCapabilities(supports_session_auth=False)
        with pytest.raises(ValueError, match="does not support session authentication"):
            AntaInventory._resolve_session_auth("unsupported-device", caps, use_session_auth_override=None, inventory_use_session_auth=True)

    def test_resolve_session_auth_unsupported_device_cli_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify warning (not error) when CLI requests session auth on an unsupported device."""
        caps = AntaDeviceCapabilities(supports_session_auth=False)
        caplog.set_level(logging.WARNING)
        result = AntaInventory._resolve_session_auth("unsupported-device", caps, use_session_auth_override=True, inventory_use_session_auth=False)
        assert result is False
        assert "does not support session authentication" in caplog.text

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "hosts": [
                        {"host": "192.168.0.1", "use_session_auth": False},
                        {"host": "192.168.0.2", "use_session_auth": False},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_use_session_auth_cli_overrides_inventory(self, yaml_file: Path) -> None:
        """Verify that use_session_auth=True passed to parse() overrides per-device inventory values of False."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123", use_session_auth=True)
        devices_by_host = {device._client.host: device for device in inventory.values() if isinstance(device, AsyncEOSDevice)}

        assert devices_by_host["192.168.0.1"]._client._use_session_auth is True
        assert devices_by_host["192.168.0.2"]._client._use_session_auth is True

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "hosts": [
                        {"host": "192.168.0.1", "use_session_auth": True},
                        {"host": "192.168.0.2", "use_session_auth": True},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_no_session_auth_cli_overrides_inventory(self, yaml_file: Path) -> None:
        """Verify that use_session_auth=False (--no-session-auth) disables session auth even when inventory enables it."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123", use_session_auth=False)
        devices_by_host = {device._client.host: device for device in inventory.values() if isinstance(device, AsyncEOSDevice)}

        assert devices_by_host["192.168.0.1"]._client._use_session_auth is False
        assert devices_by_host["192.168.0.2"]._client._use_session_auth is False

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "hosts": [
                        {"host": "192.168.0.1", "use_session_auth": True},
                        {"host": "192.168.0.2", "use_session_auth": False},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_dump_preserves_use_session_auth(self, yaml_file: Path) -> None:
        """Verify that dump() preserves the use_session_auth value for each device."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")
        dumped = inventory.dump()
        hosts_by_name = {str(host.host): host for host in dumped.hosts or []}

        assert hosts_by_name["192.168.0.1"].use_session_auth is True
        assert hosts_by_name["192.168.0.2"].use_session_auth is False

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "networks": [
                        {"network": "192.168.0.0/31", "use_session_auth": True},
                        {"network": "192.168.1.0/31", "use_session_auth": False},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_use_session_auth_propagates_from_networks(self, yaml_file: Path) -> None:
        """Verify use_session_auth propagates from network entries to all generated devices."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")
        devices_by_host = {device._client.host: device for device in inventory.values() if isinstance(device, AsyncEOSDevice)}

        assert devices_by_host["192.168.0.0"]._client._use_session_auth is True
        assert devices_by_host["192.168.0.1"]._client._use_session_auth is True
        assert devices_by_host["192.168.1.0"]._client._use_session_auth is False
        assert devices_by_host["192.168.1.1"]._client._use_session_auth is False

    @pytest.mark.parametrize(
        "yaml_file",
        [
            {
                "anta_inventory": {
                    "ranges": [
                        {"start": "10.0.0.1", "end": "10.0.0.2", "use_session_auth": True},
                        {"start": "10.0.1.1", "end": "10.0.1.2", "use_session_auth": False},
                    ]
                }
            }
        ],
        indirect=["yaml_file"],
    )
    def test_use_session_auth_propagates_from_ranges(self, yaml_file: Path) -> None:
        """Verify use_session_auth propagates from range entries to all generated devices."""
        inventory = AntaInventory.parse(filename=yaml_file, username="arista", password="arista123")
        devices_by_host = {device._client.host: device for device in inventory.values() if isinstance(device, AsyncEOSDevice)}

        assert devices_by_host["10.0.0.1"]._client._use_session_auth is True
        assert devices_by_host["10.0.0.2"]._client._use_session_auth is True
        assert devices_by_host["10.0.1.1"]._client._use_session_auth is False
        assert devices_by_host["10.0.1.2"]._client._use_session_auth is False

    @pytest.mark.parametrize(("device"), [{"name": "base_device"}], indirect=True)
    async def test_disconnect_inventory_logs_exceptions(self, caplog: pytest.LogCaptureFixture, async_device: AsyncEOSDevice, device: AntaDevice) -> None:
        """Test disconnect_inventory attempts every device and logs individual disconnect errors."""
        caplog.set_level(logging.WARNING)
        inventory = AntaInventory()
        inventory.add_device(async_device)
        inventory.add_device(device)

        with (
            patch.object(async_device, "disconnect", new=AsyncMock()) as async_device_disconnect,
            patch.object(device, "disconnect", new=AsyncMock(side_effect=RuntimeError("boom"))) as device_disconnect,
        ):
            await inventory.disconnect_inventory()

        async_device_disconnect.assert_awaited_once()
        device_disconnect.assert_awaited_once()
        assert "Error when disconnecting inventory" in caplog.text
        assert "RuntimeError: boom" in caplog.text
        assert all(record.levelno == logging.WARNING for record in caplog.records)
