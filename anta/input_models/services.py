# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for services tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field

from anta.custom_types import ErrDisableReasons


class DnsServer(BaseModel):
    """Model for a DNS server configuration."""

    model_config = ConfigDict(extra="forbid")
    server_address: IPv4Address | IPv6Address
    """The IPv4 or IPv6 address of the DNS server."""
    vrf: str = "default"
    """The VRF instance in which the DNS server resides. Defaults to 'default'."""
    priority: int = Field(ge=0, le=4)
    """The priority level of the DNS server, ranging from 0 to 4. Lower values indicate a higher priority, with 0 being the highest and 4 the lowest."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the DnsServer for reporting.

        Examples
        --------
        Server 10.0.0.1 (VRF: default, Priority: 1)
        """
        return f"Server {self.server_address} VRF: {self.vrf} Priority: {self.priority}"


class ErrdisableRecovery(BaseModel):
    """Model for the error disable recovery functionality."""

    model_config = ConfigDict(extra="forbid")
    reason: ErrDisableReasons
    """Name of the error disable reason."""
    status: Literal["Enabled", "Disabled"] = "Enabled"
    """Operational status of the reason. Defaults to 'Enabled'."""
    interval: int = Field(ge=30, le=86400)
    """Timer interval of the reason in seconds."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ErrdisableRecovery for reporting.

        Examples
        --------
        Reason: acl Status: Enabled Interval: 300
        """
        return f"Reason: {self.reason} Status: {self.status} Interval: {self.interval}"


class ErrDisableReason(ErrdisableRecovery):  # pragma: no cover
    """Alias for the ErrdisableRecovery model to maintain backward compatibility.

    When initialised, it will emit a deprecation warning and call the ErrdisableRecovery model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the ErrdisableRecovery class, emitting a depreciation warning."""
        warn(
            message="ErrDisableReason model is deprecated and will be removed in ANTA v2.0.0. Use the ErrdisableRecovery model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
