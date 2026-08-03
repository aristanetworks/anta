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

    # pylint: disable=too-few-public-methods

    @pytest.mark.parametrize(
        ("name", "portchannel", "expected"),
        [
            pytest.param("Ethernet1", "Port-Channel42", "Interface: Ethernet1 Port-Channel: Port-Channel42", id="with port-channel"),
            pytest.param("Ethernet1", None, "Interface: Ethernet1", id="no port-channel"),
        ],
    )
    def test_valid__str__(self, name: Interface, portchannel: PortChannelInterface | None, expected: str) -> None:
        """Test InterfaceState __str__."""
        assert str(InterfaceState(name=name, portchannel=portchannel)) == expected

    @pytest.mark.parametrize(
        "model_params",
        [
            pytest.param({"name": "Ethernet1"}, id="name-only"),
            pytest.param(
                {"interface_range": "Ethernet1-3", "media_type": "100GBASE-SR4"},
                id="interface-range-with-media-type",
            ),
            pytest.param(
                {"interface_range": "et1,po2", "media_type": "40GBASE-SR4"},
                id="interface-range-abbreviation-with-media-type",
            ),
        ],
    )
    def test_valid(self, model_params: dict) -> None:
        """Test InterfaceState valid inputs with name or interface_range."""
        InterfaceState.model_validate(model_params)

    @pytest.mark.parametrize(
        ("model_params", "error_match"),
        [
            pytest.param(
                {"name": None, "interface_range": None},
                r"Either 'name' or 'interface_range' must be provided",
                id="neither-name-nor-range",
            ),
            pytest.param(
                {"name": "Ethernet1", "interface_range": "Ethernet2-3", "media_type": "100GBASE-SR4"},
                r"Only one of 'name' or 'interface_range' can be provided, not both",
                id="both-name-and-range",
            ),
        ],
    )
    def test_invalid(self, model_params: dict, error_match: str) -> None:
        """Test InterfaceState invalid inputs with proper error messages."""
        with pytest.raises(ValidationError, match=error_match):
            InterfaceState.model_validate(model_params)

    @pytest.mark.parametrize(
        ("interface_range", "media_type"),
        [
            pytest.param("Ethernet1", "100GBASE-SR4", id="single-interface-range"),
            pytest.param("Ethernet1-5", "100GBASE-SR4", id="range-5-items"),
            pytest.param("Ethernet1/1-3", "25GBASE-LR", id="multi-level-range"),
            pytest.param("po1-2", "40GBASE-SR4", id="portchannel-range"),
        ],
    )
    def test_valid_complex(self, interface_range: str, media_type: str) -> None:
        """Test various valid interface_range scenarios."""
        interface_state = InterfaceState.model_validate({"interface_range": interface_range, "media_type": media_type})
        assert interface_state.interface_range is not None
        assert len(interface_state.interface_range) > 0

    @pytest.mark.parametrize(
        ("interface_range", "media_type", "error_match"),
        [
            pytest.param("1-3", "100GBASE-SR4", r"Invalid interface pattern", id="no-prefix"),
            pytest.param("Ethernet3-1", "100GBASE-SR4", r"Reverse range not supported", id="reverse-range"),
        ],
    )
    def test_invalid_complex(self, interface_range: str, media_type: str, error_match: str) -> None:
        """Test invalid interface_range patterns."""
        with pytest.raises(ValidationError, match=error_match):
            InterfaceState.model_validate({"interface_range": interface_range, "media_type": media_type})


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
            pytest.param(["Ethernet1"], ["Ethernet1"], 10, id="invalid-overlap"),
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
            pytest.param(["Ethernet1"], ["Ethernet1"], id="invalid-overlap"),
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
            pytest.param(["Ethernet1"], ["Ethernet1"], id="invalid-overlap"),
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
            pytest.param(["Ethernet1"], ["Ethernet1"], id="invalid-overlap"),
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
            pytest.param(["Ethernet1"], ["Ethernet1"], 10.00, id="invalid-overlap"),
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


class TestVerifyInterfacesTransceiverTypeInput:  # pylint: disable=too-few-public-methods
    """Test anta.tests.interfaces.VerifyInterfacesTransceiverType.Input."""

    @pytest.mark.parametrize(
        "interfaces",
        [
            pytest.param(
                [{"name": "Ethernet7", "media_type": "25GBASE-SR"}],
                id="single-interface",
            ),
            pytest.param(
                [{"interface_range": "et1-3", "media_type": "100GBASE-SR4"}],
                id="interface-range",
            ),
            pytest.param(
                [
                    {"interface_range": "Ethernet1-2", "media_type": "100GBASE-SR4"},
                    {"name": "Ethernet3", "media_type": "40GBASE-SR4"},
                ],
                id="range-and-single-interface",
            ),
        ],
    )
    def test_valid(self, interfaces: list[dict[str, str]]) -> None:
        """Test VerifyInterfacesTransceiverType.Input valid inputs."""
        VerifyInterfacesTransceiverType.Input.model_validate({"interfaces": interfaces})

    @pytest.mark.parametrize(
        ("interfaces", "error_match"),
        [
            pytest.param(
                [{"name": "Ethernet1", "media_type": "100GBASE-SR4"}, {"name": "Ethernet2"}],
                r"'media_type' must be provided for all interfaces in VerifyInterfacesTransceiverType",
                id="missing-media-type",
            ),
            pytest.param(
                [{"interface_range": "Ethernet1-2,po3", "media_type": "40GBASE-SR4"}],
                r"VerifyInterfacesTransceiverType only supports Ethernet interfaces. Got: Port-Channel3",
                id="non-ethernet-in-range",
            ),
            pytest.param(
                [{"name": "Port-Channel3", "media_type": "40GBASE-SR4"}],
                r"VerifyInterfacesTransceiverType only supports Ethernet interfaces. Got: Port-Channel3",
                id="non-ethernet-interface",
            ),
        ],
    )
    def test_invalid(self, interfaces: list[dict[str, str]], error_match: str) -> None:
        """Test VerifyInterfacesTransceiverType.Input invalid inputs."""
        with pytest.raises(ValidationError, match=error_match):
            VerifyInterfacesTransceiverType.Input.model_validate({"interfaces": interfaces})
