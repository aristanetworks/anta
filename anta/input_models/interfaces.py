# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for interface tests."""

from __future__ import annotations

from ipaddress import IPv4Interface
from typing import Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field

from anta.custom_types import Interface, PortChannelInterface


class InterfaceState(BaseModel):
    """Model for an interface state.

    TODO: Need to review this class name in ANTA v2.0.0.
    """

    model_config = ConfigDict(extra="forbid")
    name: Interface
    """Interface to validate."""
    description: str | None = None
    """Optional metadata describing the interface. Used for reporting."""
    status: Literal["up", "down", "adminDown"] | None = None
    """Expected status of the interface. Required field in the `VerifyInterfacesStatus` test."""
    line_protocol_status: Literal["up", "down", "testing", "unknown", "dormant", "notPresent", "lowerLayerDown"] | None = None
    """Expected line protocol status of the interface. Optional field in the `VerifyInterfacesStatus` test."""
    portchannel: PortChannelInterface | None = None
    """Port-Channel in which the interface is bundled. Required field in the `VerifyLACPInterfacesStatus` test."""
    lacp_rate_fast: bool = False
    """Specifies the LACP timeout mode for the link aggregation group.

    Options:
    - True: Also referred to as fast mode.
    - False: The default mode, also known as slow mode.

    Can be enabled in the `VerifyLACPInterfacesStatus` tests.
    """
    lacp_churn_state: bool = False
    """Flag to validate LACP churn state. Can be enabled in the `VerifyLACPInterfacesStatus` test."""
    primary_ip: IPv4Interface | None = None
    """Primary IPv4 address in CIDR notation. Required field in the `VerifyInterfaceIPv4` test."""
    secondary_ips: list[IPv4Interface] | None = None
    """List of secondary IPv4 addresses in CIDR notation. Can be provided in the `VerifyInterfaceIPv4` test."""
    auto: bool = False
    """The auto-negotiation status of the interface. Can be provided in the `VerifyInterfacesSpeed` test."""
    speed: float | None = Field(default=None, ge=1, le=1000)
    """The speed of the interface in Gigabits per second. Valid range is 1 to 1000. Required field in the `VerifyInterfacesSpeed` test."""
    lanes: int | None = Field(default=None, ge=1, le=8)
    """The number of lanes in the interface. Valid range is 1 to 8. Can be provided in the `VerifyInterfacesSpeed` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the InterfaceState for reporting.

        Examples
        --------
        - Interface: Ethernet1 Port-Channel: Port-Channel100
        - Interface: Ethernet1
        """
        base_string = f"Interface: {self.name}"
        if self.description is not None:
            base_string += f" ({self.description})"
        if self.portchannel is not None:
            base_string += f" Port-Channel: {self.portchannel}"
        return base_string


class InterfaceDetail(InterfaceState):  # pragma: no cover
    """Alias for the InterfaceState model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the InterfaceState model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the InterfaceState class, emitting a depreciation warning."""
        warn(
            message="InterfaceDetail model is deprecated and will be removed in ANTA v2.0.0. Use the InterfaceState model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
