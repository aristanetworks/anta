# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for AVT tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict


class AVTPath(BaseModel):
    """AVT (Adaptive Virtual Topology) model representing path details and associated information."""

    model_config = ConfigDict(extra="forbid")
    vrf: str = "default"
    """VRF context. Defaults to `default`."""
    avt_name: str
    """The name of the Adaptive Virtual Topology (AVT)."""
    description: str | None = None
    """Optional metadata describing the AVT path. Used for reporting."""
    destination: IPv4Address
    """The IPv4 address of the destination peer in the AVT."""
    next_hop: IPv4Address
    """The IPv4 address of the next hop used to reach the AVT peer."""
    path_type: str | None = None
    """Specifies the type of path for the AVT. If not specified, both types 'direct' and 'multihop' are considered."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the AVTPath for reporting.

        Examples
        --------
        AVT: CONTROL-PLANE-PROFILE VRF: default Destination: 10.101.255.2 Next-hop: 10.101.255.1

        """
        base_string = f"AVT: {self.avt_name}"
        if self.description:
            base_string += f" ({self.description})"
        base_string += f" VRF: {self.vrf} Destination: {self.destination} Next-hop: {self.next_hop}"
        if self.path_type:
            base_string += f" Path Type: {self.path_type}"

        return base_string
