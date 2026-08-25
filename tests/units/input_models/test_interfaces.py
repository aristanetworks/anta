# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.interfaces.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.interfaces import InterfaceState
from anta.tests.interfaces import (
    VerifyInterfaceIPv4,
    VerifyInterfacesBER,
    VerifyInterfacesCounterDetails,
    VerifyInterfacesEgressQueueDrops,
    VerifyInterfacesOpticsReceivePower,
    VerifyInterfacesOpticsTemperature,
    VerifyInterfacesSpeed,
    VerifyInterfacesStatus,
    VerifyInterfacesTransceiverType,
    VerifyLACPInterfacesStatus,
)

if TYPE_CHECKING:
    from anta.custom_types import EthernetInterface, Interface, ManagementInterface, PortChannelInterface, PositiveInteger


class TestInterfaceState:
    """Test anta.input_models.interfaces.InterfaceState."""

    @pytest.mark.parametrize(
        ("name", "portchannel", "description", "expected"),
        [
            pytest.param("Ethernet1", "Port-Channel42", None, "Interface: Ethernet1 Port-Channel: Port-Channel42", id="with-port-channel"),
            pytest.param("Ethernet1", None, None, "Interface: Ethernet1", id="name-only"),
            pytest.param("Ethernet1", None, "uplink", "Interface: Ethernet1 (uplink)", id="with-description"),
            pytest.param(
                "Ethernet1", "Port-Channel42", "uplink", "Interface: Ethernet1 (uplink) Port-Channel: Port-Channel42", id="with-description-and-port-channel"
            ),
        ],
    )
    def test_valid__str__(self, name: Interface, portchannel: PortChannelInterface | None, description: str | None, expected: str) -> None:
        """Test InterfaceState __str__ covers all optional field combinations."""
        assert str(InterfaceState(name=name, portchannel=portchannel, description=description)) == expected

    @pytest.mark.parametrize(
        "model_params",
        [
            pytest.param({"name": "Ethernet1"}, id="single-interface"),
            pytest.param({"name": "et1"}, id="single-abbreviation"),
            pytest.param({"name": "Ethernet1-3", "media_type": "100GBASE-SR4"}, id="range"),
            pytest.param({"name": "et1-3", "media_type": "100GBASE-SR4"}, id="abbreviated-range"),
            pytest.param({"name": "et1,po2", "media_type": "40GBASE-SR4"}, id="comma-separated-abbreviations"),
            pytest.param({"name": ["Ethernet1", "Ethernet2"]}, id="pre-expanded-list"),
        ],
    )
    def test_valid(self, model_params: dict) -> None:
        """Test InterfaceState valid inputs — single names, abbreviations, range patterns, and pre-expanded lists."""
        InterfaceState.model_validate(model_params)

    @pytest.mark.parametrize(
        ("model_params", "error_match"),
        [
            pytest.param(
                {},
                r"Field required",
                id="missing-name",
            ),
            pytest.param(
                {"name": "Ethernet1", "interface_range": "Ethernet2-3", "media_type": "100GBASE-SR4"},
                r"Extra inputs are not permitted",
                id="extra-interface-range-field",
            ),
            pytest.param(
                {"name": "GigabitEthernet1-3", "media_type": "100GBASE-SR4"},
                r"String should match pattern",
                id="range-with-unsupported-interface-type",
            ),
            pytest.param(
                {"name": "abc"},
                r"Could not parse interface ID in interface",
                id="non-parseable-string",
            ),
        ],
    )
    def test_invalid(self, model_params: dict, error_match: str) -> None:
        """Test InterfaceState rejects missing required fields, unknown extra fields, and invalid EOS interface types."""
        with pytest.raises(ValidationError, match=error_match):
            InterfaceState.model_validate(model_params)

    @pytest.mark.parametrize(
        ("model_params", "expected_names"),
        [
            pytest.param({"name": "Ethernet1"}, ["Ethernet1"], id="single-returns-self"),
            pytest.param({"name": "Ethernet1-3"}, ["Ethernet1", "Ethernet2", "Ethernet3"], id="range-expands"),
            pytest.param({"name": "et1-2"}, ["Ethernet1", "Ethernet2"], id="abbreviated-range-expands-and-normalizes"),
            pytest.param({"name": "Ethernet1,et2"}, ["Ethernet1", "Ethernet2"], id="comma-separated-expands"),
        ],
    )
    def test_expand(self, model_params: dict, expected_names: list[str]) -> None:
        """Test InterfaceState.expand() yields individual str-named entries for every input shape."""
        interface = InterfaceState.model_validate(model_params)
        expanded = interface.expand()
        assert [e.name for e in expanded] == expected_names
        assert all(isinstance(e.name, str) for e in expanded), "Every expanded entry must have a str name"


class TestVerifyInterfacesStatusInput:
    """Test anta.tests.interfaces.VerifyInterfacesStatus.Input."""

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1", "status": "up"}], id="valid"),
        ],
    )
    def test_valid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfacesStatus.Input valid inputs."""
        VerifyInterfacesStatus.Input(interfaces=interfaces)

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1"}], id="invalid"),
        ],
    )
    def test_invalid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfacesStatus.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesStatus.Input(interfaces=interfaces)


class TestVerifyLACPInterfacesStatusInput:
    """Test anta.tests.interfaces.VerifyLACPInterfacesStatus.Input."""

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1", "portchannel": "Port-Channel100"}], id="valid"),
        ],
    )
    def test_valid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyLACPInterfacesStatus.Input valid inputs."""
        VerifyLACPInterfacesStatus.Input(interfaces=interfaces)

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1"}], id="invalid"),
        ],
    )
    def test_invalid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyLACPInterfacesStatus.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyLACPInterfacesStatus.Input(interfaces=interfaces)


class TestVerifyInterfaceIPv4Input:
    """Test anta.tests.interfaces.VerifyInterfaceIPv4.Input."""

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1", "primary_ip": "172.30.11.1/31"}], id="valid"),
        ],
    )
    def test_valid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfaceIPv4.Input valid inputs."""
        VerifyInterfaceIPv4.Input(interfaces=interfaces)

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1"}], id="invalid-no-primary-ip"),
        ],
    )
    def test_invalid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfaceIPv4.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfaceIPv4.Input(interfaces=interfaces)


class TestVerifyInterfacesSpeedInput:
    """Test anta.tests.interfaces.VerifyInterfacesSpeed.Input."""

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1", "speed": 10}], id="valid-speed-is-given"),
        ],
    )
    def test_valid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfacesSpeed.Input valid inputs."""
        VerifyInterfacesSpeed.Input(interfaces=interfaces)

    @pytest.mark.parametrize(
        ("interfaces"),
        [
            pytest.param([{"name": "Ethernet1"}], id="invalid-speed-is-not-given"),
        ],
    )
    def test_invalid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfacesSpeed.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesSpeed.Input(interfaces=interfaces)


class TestVerifyPhysicalInterfacesCounterDetailsInput:
    """Test anta.tests.interfaces.VerifyInterfacesCounterDetails.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces", "link_status_changes_threshold"),
        [
            pytest.param(["Ethernet1"], ["Management1/1"], 10, id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(
        self,
        interfaces: list[EthernetInterface | ManagementInterface],
        ignored_interfaces: list[EthernetInterface | ManagementInterface],
        link_status_changes_threshold: PositiveInteger,
    ) -> None:
        """Test VerifyInterfacesCounterDetails.Input valid inputs."""
        VerifyInterfacesCounterDetails.Input(
            interfaces=interfaces, ignored_interfaces=ignored_interfaces, link_status_changes_threshold=link_status_changes_threshold
        )

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces", "link_status_changes_threshold"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1"], 10, id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], 10, id="invalid-interfaces"),
        ],
    )
    def test_invalid(
        self,
        interfaces: list[EthernetInterface | ManagementInterface],
        ignored_interfaces: list[EthernetInterface | ManagementInterface],
        link_status_changes_threshold: PositiveInteger,
    ) -> None:
        """Test VerifyInterfacesCounterDetails.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesCounterDetails.Input(
                interfaces=interfaces, ignored_interfaces=ignored_interfaces, link_status_changes_threshold=link_status_changes_threshold
            )


class TestVerifytInterfacesBERInput:
    """Test anta.tests.interfaces.VerifyInterfacesBER.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1/1"], id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesBER.Input valid inputs."""
        VerifyInterfacesBER.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1/1"], ["Ethernet1/1"], id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], id="invalid-interfaces"),
        ],
    )
    def test_invalid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesBER.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesBER.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)


class TestVerifyInterfacesOpticalReceivePowerInput:
    """Test anta.tests.interfaces.VerifyInterfacesOpticsReceivePower.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1/1"], id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesOpticsReceivePower.Input valid inputs."""
        VerifyInterfacesOpticsReceivePower.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1/1"], ["Ethernet1/1"], id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], id="invalid-interfaces"),
        ],
    )
    def test_invalid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesOpticsReceivePower.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesOpticsReceivePower.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)


class TestVerifyInterfacesEgressQueueDropsInput:
    """Test anta.tests.interfaces.VerifyInterfacesEgressQueueDrops.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1"], ["Ethernet2"], id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(
        self,
        interfaces: list[EthernetInterface],
        ignored_interfaces: list[EthernetInterface],
    ) -> None:
        """Test VerifyInterfacesEgressQueueDrops.Input valid inputs."""
        VerifyInterfacesEgressQueueDrops.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1"], id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], id="invalid-interfaces"),
        ],
    )
    def test_invalid(
        self,
        interfaces: list[EthernetInterface],
        ignored_interfaces: list[EthernetInterface],
    ) -> None:
        """Test VerifyInterfacesEgressQueueDrops.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesEgressQueueDrops.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)


class TestVerifyInterfacesTransceiverTypeInput:
    """Test anta.tests.interfaces.VerifyInterfacesTransceiverType.Input."""

    @pytest.mark.parametrize(
        "interfaces",
        [
            pytest.param([{"name": "Ethernet1", "media_type": "100GBASE-SR4"}], id="single-interface"),
            pytest.param([{"name": "Ethernet1-3", "media_type": "100GBASE-SR4"}], id="range"),
            pytest.param([{"name": "et1-3", "media_type": "100GBASE-SR4"}], id="abbreviated-range"),
            pytest.param([{"name": "Ethernet1,et2", "media_type": "100GBASE-SR4"}], id="comma-separated"),
        ],
    )
    def test_valid(self, interfaces: list[InterfaceState]) -> None:
        """Test VerifyInterfacesTransceiverType.Input accepts single names, ranges, and comma-separated patterns."""
        VerifyInterfacesTransceiverType.Input(interfaces=interfaces)

    @pytest.mark.parametrize(
        ("interfaces", "error_match"),
        [
            pytest.param(
                [{"name": "Ethernet1"}],
                r"Interface: Ethernet1 'media_type' field missing in the input",
                id="missing-media-type",
            ),
            pytest.param(
                [{"name": "Loopback1", "media_type": "100GBASE-SR4"}],
                r"VerifyInterfacesTransceiverType only supports Ethernet interfaces\. Got: Loopback1",
                id="non-ethernet-single",
            ),
            pytest.param(
                [{"name": "Loopback1-3", "media_type": "100GBASE-SR4"}],
                r"VerifyInterfacesTransceiverType only supports Ethernet interfaces\. Got: Loopback1, Loopback2, Loopback3",
                id="non-ethernet-range",
            ),
        ],
    )
    def test_invalid(self, interfaces: list[InterfaceState], error_match: str) -> None:
        """Test VerifyInterfacesTransceiverType.Input rejects missing media_type and non-Ethernet interfaces."""
        with pytest.raises(ValidationError, match=error_match):
            VerifyInterfacesTransceiverType.Input(interfaces=interfaces)


class TestVerifyInterfacesOpticsTemperatureInput:
    """Test anta.tests.interfaces.VerifyInterfacesOpticsTemperature.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces", "max_transceiver_temperature"),
        [
            pytest.param(["Ethernet1"], ["Ethernet2"], 10.00, id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(
        self,
        interfaces: list[EthernetInterface],
        ignored_interfaces: list[EthernetInterface],
        max_transceiver_temperature: float,
    ) -> None:
        """Test VerifyInterfacesOpticsTemperature.Input valid inputs."""
        VerifyInterfacesOpticsTemperature.Input(
            interfaces=interfaces, ignored_interfaces=ignored_interfaces, max_transceiver_temperature=max_transceiver_temperature
        )

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces", "max_transceiver_temperature"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1"], 10.00, id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], 10, id="invalid-interfaces"),
        ],
    )
    def test_invalid(
        self,
        interfaces: list[EthernetInterface],
        ignored_interfaces: list[EthernetInterface],
        max_transceiver_temperature: float,
    ) -> None:
        """Test VerifyInterfacesOpticsTemperature.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesOpticsTemperature.Input(
                interfaces=interfaces, ignored_interfaces=ignored_interfaces, max_transceiver_temperature=max_transceiver_temperature
            )
