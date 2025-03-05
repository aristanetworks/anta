# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Inventory models unit tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError
from yaml import safe_load

from anta.inventory.models import AntaInventoryHost, AntaInventoryInput, AntaInventoryNetwork, AntaInventoryRange

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

FILE_DIR: Path = Path(__file__).parents[2] / "data"

INVENTORY_HOST_VALID_PARAMS: list[ParameterSet] = [
    pytest.param(None, "1.1.1.1", None, None, None, id="IPv4"),
    pytest.param(None, "fe80::cc62:a9ff:feef:932a", None, None, None, id="IPv6"),
    pytest.param(None, "1.1.1.1", 666, None, None, id="IPv4_with_port"),
    pytest.param(None, "1.1.1.1", None, None, True, id="cache_enabled"),
    pytest.param(None, "1.1.1.1", None, None, False, id="cache_disabled"),
]

INVENTORY_HOST_INVALID_PARAMS: list[ParameterSet] = [
    pytest.param(None, "1.1.1.1/32", None, None, False, id="IPv4_with_netmask"),
    pytest.param(None, "1.1.1.1", 66666, None, False, id="IPv4_with_wrong_port"),
    pytest.param(None, "fe80::cc62:a9ff:feef:932a/128", None, None, False, id="IPv6_with_netmask"),
    pytest.param(None, "fe80::cc62:a9ff:feef:", None, None, False, id="invalid_IPv6"),
    pytest.param(None, "@", None, None, False, id="special_char"),
    pytest.param(None, "1.1.1.1", None, None, None, id="cache_is_None"),
]

INVENTORY_NETWORK_VALID_PARAMS: list[ParameterSet] = [
    pytest.param("1.1.1.0/24", None, None, id="IPv4_subnet"),
    pytest.param("2001:db8::/32", None, None, id="IPv6_subnet"),
    pytest.param("1.1.1.0/24", None, False, id="cache_enabled"),
    pytest.param("1.1.1.0/24", None, True, id="cache_disabled"),
]

INVENTORY_NETWORK_INVALID_PARAMS: list[ParameterSet] = [
    pytest.param("1.1.1.0/17", None, False, id="IPv4_subnet"),
    pytest.param("2001:db8::/16", None, False, id="IPv6_subnet"),
    pytest.param("1.1.1.0/24", None, None, id="cache_is_None"),
]

INVENTORY_RANGE_VALID_PARAMS: list[ParameterSet] = [
    pytest.param("10.1.0.1", "10.1.0.10", None, None, id="IPv4_range"),
    pytest.param("10.1.0.1", "10.1.0.10", None, True, id="cache_enabled"),
    pytest.param("10.1.0.1", "10.1.0.10", None, False, id="cache_disabled"),
]

INVENTORY_RANGE_INVALID_PARAMS: list[ParameterSet] = [
    pytest.param("toto", "10.1.0.10", None, False, id="IPv4_range"),
    pytest.param("10.1.0.1", "10.1.0.10", None, None, id="cache_is_None"),
]

INVENTORY_MODEL_VALID = [
    {
        "name": "Valid_Host_Only",
        "input": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2"}]},
        "expected_result": "valid",
    },
    {
        "name": "Valid_Networks_Only",
        "input": {"networks": [{"network": "192.168.0.0/16"}, {"network": "192.168.1.0/24"}]},
        "expected_result": "valid",
    },
    {
        "name": "Valid_Ranges_Only",
        "input": {
            "ranges": [
                {"start": "10.1.0.1", "end": "10.1.0.10"},
                {"start": "10.2.0.1", "end": "10.2.1.10"},
            ],
        },
        "expected_result": "valid",
    },
]

INVENTORY_MODEL_INVALID = [
    {
        "name": "Host_with_Invalid_entry",
        "input": {"hosts": [{"host": "192.168.0.17"}, {"host": "192.168.0.2/32"}]},
        "expected_result": "invalid",
    },
]


class TestAntaInventoryHost:
    """Test anta.inventory.models.AntaInventoryHost."""

    @pytest.mark.parametrize(("name", "host", "port", "tags", "disable_cache"), INVENTORY_HOST_VALID_PARAMS)
    def test_valid(self, name: str, host: str, port: int, tags: set[str], disable_cache: bool | None) -> None:
        """Valid model parameters."""
        params: dict[str, Any] = {"name": name, "host": host, "port": port, "tags": tags}
        if disable_cache is not None:
            params = params | {"disable_cache": disable_cache}
        inventory_host = AntaInventoryHost.model_validate(params)
        assert host == str(inventory_host.host)
        assert port == inventory_host.port
        assert name == inventory_host.name
        assert tags == inventory_host.tags
        if disable_cache is None:
            # Check cache default value
            assert inventory_host.disable_cache is False
        else:
            assert inventory_host.disable_cache == disable_cache

    @pytest.mark.parametrize(("name", "host", "port", "tags", "disable_cache"), INVENTORY_HOST_INVALID_PARAMS)
    def test_invalid(self, name: str, host: str, port: int, tags: set[str], disable_cache: bool | None) -> None:
        """Invalid model parameters."""
        with pytest.raises(ValidationError):
            AntaInventoryHost.model_validate({"name": name, "host": host, "port": port, "tags": tags, "disable_cache": disable_cache})


class TestAntaInventoryNetwork:
    """Test anta.inventory.models.AntaInventoryNetwork."""

    @pytest.mark.parametrize(("network", "tags", "disable_cache"), INVENTORY_NETWORK_VALID_PARAMS)
    def test_valid(self, network: str, tags: set[str], disable_cache: bool | None) -> None:
        """Valid model parameters."""
        params: dict[str, Any] = {"network": network, "tags": tags}
        if disable_cache is not None:
            params = params | {"disable_cache": disable_cache}
        inventory_network = AntaInventoryNetwork.model_validate(params)
        assert network == str(inventory_network.network)
        assert tags == inventory_network.tags
        if disable_cache is None:
            # Check cache default value
            assert inventory_network.disable_cache is False
        else:
            assert inventory_network.disable_cache == disable_cache

    @pytest.mark.parametrize(("network", "tags", "disable_cache"), INVENTORY_NETWORK_INVALID_PARAMS)
    def test_invalid(self, network: str, tags: set[str], disable_cache: bool | None) -> None:
        """Invalid model parameters."""
        with pytest.raises(ValidationError):
            AntaInventoryNetwork.model_validate({"network": network, "tags": tags, "disable_cache": disable_cache})


class TestAntaInventoryRange:
    """Test anta.inventory.models.AntaInventoryRange."""

    @pytest.mark.parametrize(("start", "end", "tags", "disable_cache"), INVENTORY_RANGE_VALID_PARAMS)
    def test_valid(self, start: str, end: str, tags: set[str], disable_cache: bool | None) -> None:
        """Valid model parameters."""
        params: dict[str, Any] = {"start": start, "end": end, "tags": tags}
        if disable_cache is not None:
            params = params | {"disable_cache": disable_cache}
        inventory_range = AntaInventoryRange.model_validate(params)
        assert start == str(inventory_range.start)
        assert end == str(inventory_range.end)
        assert tags == inventory_range.tags
        if disable_cache is None:
            # Check cache default value
            assert inventory_range.disable_cache is False
        else:
            assert inventory_range.disable_cache == disable_cache

    @pytest.mark.parametrize(("start", "end", "tags", "disable_cache"), INVENTORY_RANGE_INVALID_PARAMS)
    def test_invalid(self, start: str, end: str, tags: set[str], disable_cache: bool | None) -> None:
        """Invalid model parameters."""
        with pytest.raises(ValidationError):
            AntaInventoryRange.model_validate({"start": start, "end": end, "tags": tags, "disable_cache": disable_cache})


class TestAntaInventoryInputs:
    """Test anta.inventory.models.AntaInventoryInputs."""

    def test_dump_to_json(self):
        """Load a YAML file, dump it to JSON and verify it works."""
        input_yml_path = FILE_DIR / "test_inventory_with_tags.yml"
        expected_json_path = FILE_DIR / "test_inventory_with_tags.json"
        with input_yml_path.open("r") as f:
            data = safe_load(f)
        anta_inventory_input = AntaInventoryInput(**data["anta_inventory"])

        with expected_json_path.open("r") as f:
            expected_data = json.load(f)

        assert json.loads(anta_inventory_input.to_json()) == expected_data["anta_inventory"]

    def test_dump_to_yaml(self):
        """Load a JSON file, dump it to YAML and verify it works."""
        input_json_path = FILE_DIR / "test_inventory_medium.json"
        expected_yml_path = FILE_DIR / "test_inventory_medium.yml"
        with input_json_path.open("r") as f:
            data = json.load(f)
        anta_inventory_input = AntaInventoryInput(**data["anta_inventory"])

        with expected_yml_path.open("r") as f:
            expected_data = safe_load(f)

        assert safe_load(anta_inventory_input.yaml()) == expected_data["anta_inventory"]
