# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for path-selection tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict


class DpsPath(BaseModel):
    """Model for a list of DPS path entries."""

    model_config = ConfigDict(extra="forbid")
    peer: IPv4Address
    """Static peer IPv4 address."""
    path_group: str
    """Router path group name."""
    source_address: IPv4Address
    """Source IPv4 address of path."""
    destination_address: IPv4Address
    """Destination IPv4 address of path."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the DpsPath for reporting."""
        return f"Peer: {self.peer}, PathGroup: {self.path_group}, Source: {self.source_address}, Destination: {self.destination_address}"
