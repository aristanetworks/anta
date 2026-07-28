# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for interface tests."""

from __future__ import annotations

import re
from ipaddress import IPv4Interface
from typing import Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from anta.custom_types import Interface, PortChannelInterface, expand_interface_abbreviation


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


class InterfacesTransceiverType(BaseModel):
    """Interface pattern with expected transceiver media type; validates and pre-expands at catalog-load."""

    model_config = ConfigDict(extra="forbid")

    name: str
    """Interface pattern (e.g., 'Ethernet1-3', 'et1-3', 'Ethernet4,6'). Expanded via range expansion and abbreviations."""
    media_type: str
    """Expected transceiver media type (e.g., '100GBASE-SR4', '40GBASE-SR4', '25GBASE-LR')."""
    expanded_names: list[str] = Field(default_factory=list, init=False)
    """Pre-expanded interface names from pattern; populated after validation."""

    @field_validator("name", mode="before")
    @classmethod
    def expand_interface_abbreviation(cls, interface_name: str) -> str:
        """Expand abbreviations (et→Ethernet, po→Port-Channel, lo→Loopback, vl→Vlan, eth→Ethernet)."""
        return expand_interface_abbreviation(interface_name)

    @model_validator(mode="after")
    def validate_and_expand_pattern(self) -> InterfacesTransceiverType:
        """Validate pattern syntax (no reverse ranges, oversized ranges >1000) and expand ranges to individual interfaces."""
        range_pattern = re.compile(r"^([\d/]*?)(\d+)-(\d+)$")
        max_range_size = 1000
        current_prefix = None
        expanded = []

        for part in self.name.split(","):
            part_str = part.strip()
            if not part_str:
                continue

            # Extract prefix (Ethernet, Port-Channel, etc)
            match = re.match(r"^([a-zA-Z]+(?:-[a-zA-Z]+)*)", part_str)
            if match:
                current_prefix = match.group(1)
                remainder = part_str[len(current_prefix) :]
            else:
                if current_prefix is None:
                    msg = f"Invalid interface pattern: {self.name}"
                    raise ValueError(msg)
                remainder = part_str

            if not remainder or not remainder[0].isdigit():
                msg = f"Invalid interface pattern: {self.name}"
                raise ValueError(msg)

            # Single port or range
            if "-" not in remainder:
                expanded.append(f"{current_prefix}{remainder}")
            else:
                range_match = range_pattern.match(remainder)
                if not range_match:
                    msg = f"Invalid interface range: {self.name}"
                    raise ValueError(msg)

                prefix_part, start_str, end_str = range_match.groups()
                start, end = int(start_str), int(end_str)

                if start > end:
                    msg = f"Reverse range not supported: {self.name} (start {start} > end {end})"
                    raise ValueError(msg)

                if (end - start + 1) > max_range_size:
                    msg = f"Range too large (>{max_range_size}): {self.name} ({end - start + 1} items)"
                    raise ValueError(msg)

                expanded.extend(f"{current_prefix}{prefix_part}{i}" for i in range(start, end + 1))

        self.expanded_names = expanded
        return self
