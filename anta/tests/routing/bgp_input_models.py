# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING, Any
from warnings import warn

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator

from anta.custom_types import Afi, Safi

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

AFI_SAFI_EOS_KEY = {
    ("ipv4", "unicast"): "ipv4Unicast",
    ("ipv4", "multicast"): "ipv4Multicast",
    ("ipv4", "labeled-unicast"): "ipv4MplsLabels",
    ("ipv4", "sr-te"): "ipv4SrTe",
    ("ipv6", "unicast"): "ipv6Unicast",
    ("ipv6", "multicast"): "ipv6Multicast",
    ("ipv6", "labeled-unicast"): "ipv6MplsLabels",
    ("ipv6", "sr-te"): "ipv6SrTe",
    ("vpn-ipv4", None): "ipv4MplsVpn",
    ("vpn-ipv6", None): "ipv6MplsVpn",
    ("evpn", None): "l2VpnEvpn",
    ("rt-membership", None): "rtMembership",
    ("path-selection", None): "dps",
    ("link-state", None): "linkState",
}
"""Dictionary mapping AFI/SAFI to EOS key representation."""


class BgpAddressFamily(BaseModel):
    """Model for a BGP address family."""

    model_config = ConfigDict(extra="forbid")
    afi: Afi
    """BGP Address Family Identifier (AFI)."""
    safi: Safi | None = None
    """BGP Subsequent Address Family Identifier (SAFI). Required when `afi` is `ipv4` or `ipv6`."""
    vrf: str = "default"
    """Optional VRF when `afi` is `ipv4` or `ipv6`. Defaults to `default`.

    If the input `afi` is NOT `ipv4` or `ipv6` (e.g. `evpn`, `vpn-ipv4`, etc.), the `vrf` must be `default`.

    These AFIs operate at a global level and do not use the VRF concept in the same way as IPv4/IPv6.
    """
    num_peers: PositiveInt | None = None
    """Number of expected established BGP peers with negotiated AFI/SAFI. Required field in the `VerifyBGPPeerCount` test."""
    peers: list[IPv4Address | IPv6Address] | None = None
    """List of expected IPv4/IPv6 BGP peers supporting the AFI/SAFI. Required field in the `VerifyBGPSpecificPeers` test."""

    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        """Validate the inputs provided to the BgpAddressFamily class.

        If `afi` is either `ipv4` or `ipv6`, `safi` must be provided.

        If `afi` is not `ipv4` or `ipv6`, `safi` must NOT be provided and `vrf` must be `default`.
        """
        if self.afi in ["ipv4", "ipv6"]:
            if self.safi is None:
                msg = "'safi' must be provided when afi is ipv4 or ipv6"
                raise ValueError(msg)
        elif self.safi is not None:
            msg = "'safi' must not be provided when afi is not ipv4 or ipv6"
            raise ValueError(msg)
        elif self.vrf != "default":
            msg = "'vrf' must be default when afi is not ipv4 or ipv6"
            raise ValueError(msg)
        return self

    @property
    def eos_key(self) -> str:
        """AFI/SAFI EOS key representation."""
        return AFI_SAFI_EOS_KEY[(self.afi, self.safi)]

    def __str__(self) -> str:
        """Return a string representation of the BgpAddressFamily model. Used in failure messages."""
        base_string = f"AFI:{self.afi}"
        if self.safi is not None:
            base_string += f" SAFI:{self.safi}"
        if self.afi in ["ipv4", "ipv6"]:
            base_string += f" VRF:{self.vrf}"
        base_string += " -"
        return base_string


class BgpAfi(BgpAddressFamily):
    """Alias for the BgpAddressFamily model to maintain backward compatibility.

    When initialized, it will emit a depreciation warning and call the BgpAddressFamily model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the BgpAfi class, emitting a depreciation warning."""
        warn(
            message="BgpAfi model is deprecated and will be removed in ANTA v2.0.0. Use the BgpAddressFamily model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
