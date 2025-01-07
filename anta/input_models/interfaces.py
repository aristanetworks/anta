# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for interface tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Interface, PortChannelInterface


class InterfaceState(BaseModel):
    """Model for an interface state."""

    model_config = ConfigDict(extra="forbid")
    name: Interface
    """Interface to validate."""
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

    def __str__(self) -> str:
        """Return a human-readable string representation of the InterfaceState for reporting.

        Examples
        --------
        - Interface: Ethernet1 Port-Channel: Port-Channel100
        - Interface: Ethernet1
        """
        base_string = f"Interface: {self.name}"
        if self.portchannel is not None:
            base_string += f" Port-Channel: {self.portchannel}"
        return base_string
