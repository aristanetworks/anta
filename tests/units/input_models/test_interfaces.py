# Copyright (c) 2023-2025 Arista Networks, Inc.
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
    VerifyInterfacesEgressQueueDrops,
    VerifyInterfacesOpticalReceivePower,
    VerifyInterfacesSpeed,
    VerifyInterfacesStatus,
    VerifyLACPInterfacesStatus,
    VerifyPhysicalInterfacesCounterDetails,
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
    """Test anta.tests.interfaces.VerifyPhysicalInterfacesCounterDetails.Input."""

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
        """Test VerifyPhysicalInterfacesCounterDetails.Input valid inputs."""
        VerifyPhysicalInterfacesCounterDetails.Input(
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
        """Test VerifyPhysicalInterfacesCounterDetails.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyPhysicalInterfacesCounterDetails.Input(
                interfaces=interfaces, ignored_interfaces=ignored_interfaces, link_status_changes_threshold=link_status_changes_threshold
            )


class TestVerifyInterfacesOpticalReceivePowerInput:
    """Test anta.tests.interfaces.VerifyInterfacesOpticalReceivePower.Input."""

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1"], ["Ethernet1/1"], id="valid-interfaces-is-given"),
        ],
    )
    def test_valid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesOpticalReceivePower.Input valid inputs."""
        VerifyInterfacesOpticalReceivePower.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)

    @pytest.mark.parametrize(
        ("interfaces", "ignored_interfaces"),
        [
            pytest.param(["Ethernet1/1"], ["Ethernet1/1"], id="invalid-interfaces"),
            pytest.param(["et1"], ["Ethernet1"], id="invalid-interfaces"),
        ],
    )
    def test_invalid(self, interfaces: list[EthernetInterface], ignored_interfaces: list[EthernetInterface]) -> None:
        """Test VerifyInterfacesOpticalReceivePower.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyInterfacesOpticalReceivePower.Input(interfaces=interfaces, ignored_interfaces=ignored_interfaces)


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
