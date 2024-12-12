# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing ISIS tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Interface


class ISISInstance(BaseModel):
    """Model for a ISIS instance."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """The name of the IS-IS instance."""
    vrf: str = "default"
    """VRF context where the IS-IS instance is configured. Defaults to `default`."""
    dataplane: Literal["MPLS", "mpls", "unset"] = "MPLS"
    """Configured dataplane for the IS-IS instance."""
    segments: list[Segment] | None = None
    """A list of IS-IS segments associated with the instance. Required field in the `VerifyISISSegmentRoutingDataplane` test"""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInstance for reporting."""
        return f"Instance: {self.name} VRF: {self.vrf}"


class Segment(BaseModel):
    """Segment model definition."""

    model_config = ConfigDict(extra="forbid")
    interface: Interface
    """Interface name to check."""
    level: Literal[1, 2] = 2
    """ISIS level configured for interface. Default is 2."""
    sid_origin: Literal["dynamic"] = "dynamic"
    "Specifies the origin of the Segment ID."
    address: IPv4Address
    """IP address of the remote end of the segment(segment endpoint)."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Segment for reporting."""
        return f"Interface: {self.interface} Endpoint: {self.address}"


class ISISInterface(BaseModel):
    """Model for a ISIS Interface."""

    model_config = ConfigDict(extra="forbid")
    name: Interface
    """Interface name to check."""
    vrf: str = "default"
    """VRF name where ISIS instance is configured."""
    level: Literal[1, 2] = 2
    """ISIS level (1 or 2) configured for the interface. Default is 2."""
    count: int | None = None
    """The total number of IS-IS neighbors associated with interface."""
    mode: Literal["point-to-point", "broadcast", "passive"] | None = None
    """The operational mode of the IS-IS interface."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInterface for reporting."""
        return f"Interface: {self.name} VRF: {self.vrf} Level: {self.level if self.level else 'IS Type(1-2)'}"


class InterfaceCount(ISISInterface):  # pragma: no cover
    """Alias for the ISISInterface model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the ISISInterface model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the ISISInterface class, emitting a deprecation warning."""
        warn(
            message="InterfaceCount model is deprecated and will be removed in ANTA v2.0.0. Use the ISISInterface model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class InterfaceState(ISISInterface):  # pragma: no cover
    """Alias for the ISISInterface model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the ISISInterface model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the ISISInterface class, emitting a deprecation warning."""
        warn(
            message="InterfaceState model is deprecated and will be removed in ANTA v2.0.0. Use the ISISInterface model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class IsisInstance(ISISInstance):  # pragma: no cover
    """Alias for the ISISInstance model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the ISISInstance model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the ISISInstance class, emitting a deprecation warning."""
        warn(
            message="IsisInstance model is deprecated and will be removed in ANTA v2.0.0. Use the ISISInstance model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
