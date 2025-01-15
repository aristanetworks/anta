# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing BGP tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, IPv6Address
from typing import TYPE_CHECKING, Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import Afi, BgpDropStats, BgpUpdateError, MultiProtocolCaps, Safi, Vni

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
    check_tcp_queues: bool = True
    """Flag to check if the TCP session queues are empty for a BGP peer. Defaults to `True`.

    Can be disabled in the `VerifyBGPPeersHealth` and `VerifyBGPSpecificPeers` tests.
    """
    check_peer_state: bool = False
    """Flag to check if the peers are established with negotiated AFI/SAFI. Defaults to `False`.

    Can be enabled in the `VerifyBGPPeerCount` tests.
    """

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
        # Pydantic handles the validation of the AFI/SAFI combination, so we can ignore error handling here.
        return AFI_SAFI_EOS_KEY[(self.afi, self.safi)]

    def __str__(self) -> str:
        """Return a human-readable string representation of the BgpAddressFamily for reporting.

        Examples
        --------
        - AFI:ipv4 SAFI:unicast VRF:default
        - AFI:evpn
        """
        base_string = f"AFI: {self.afi}"
        if self.safi is not None:
            base_string += f" SAFI: {self.safi}"
        if self.afi in ["ipv4", "ipv6"]:
            base_string += f" VRF: {self.vrf}"
        return base_string


class BgpAfi(BgpAddressFamily):  # pragma: no cover
    """Alias for the BgpAddressFamily model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the BgpAddressFamily model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the BgpAfi class, emitting a deprecation warning."""
        warn(
            message="BgpAfi model is deprecated and will be removed in ANTA v2.0.0. Use the BgpAddressFamily model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class BgpPeer(BaseModel):
    """Model for a BGP peer.

    Only IPv4 peers are supported for now.
    """

    model_config = ConfigDict(extra="forbid")
    peer_address: IPv4Address
    """IPv4 address of the BGP peer."""
    vrf: str = "default"
    """Optional VRF for the BGP peer. Defaults to `default`."""
    peer_group: str | None = None
    """Peer group of the BGP peer. Required field in the `VerifyBGPPeerGroup` test."""
    advertised_routes: list[IPv4Network] | None = None
    """List of advertised routes in CIDR format. Required field in the `VerifyBGPExchangedRoutes` test."""
    received_routes: list[IPv4Network] | None = None
    """List of received routes in CIDR format. Required field in the `VerifyBGPExchangedRoutes` test."""
    capabilities: list[MultiProtocolCaps] | None = None
    """List of BGP multiprotocol capabilities. Required field in the `VerifyBGPPeerMPCaps`, `VerifyBGPNlriAcceptance` tests."""
    strict: bool = False
    """If True, requires exact match of the provided BGP multiprotocol capabilities.

    Optional field in the `VerifyBGPPeerMPCaps` test. Defaults to False."""
    hold_time: int | None = Field(default=None, ge=3, le=7200)
    """BGP hold time in seconds. Required field in the `VerifyBGPTimers` test."""
    keep_alive_time: int | None = Field(default=None, ge=0, le=3600)
    """BGP keepalive time in seconds. Required field in the `VerifyBGPTimers` test."""
    drop_stats: list[BgpDropStats] | None = None
    """List of drop statistics to be verified.

    Optional field in the `VerifyBGPPeerDropStats` test. If not provided, the test will verifies all drop statistics."""
    update_errors: list[BgpUpdateError] | None = None
    """List of update error counters to be verified.

    Optional field in the `VerifyBGPPeerUpdateErrors` test. If not provided, the test will verifies all the update error counters."""
    inbound_route_map: str | None = None
    """Inbound route map applied, defaults to None. Required field in the `VerifyBgpRouteMaps` test."""
    outbound_route_map: str | None = None
    """Outbound route map applied, defaults to None. Required field in the `VerifyBgpRouteMaps` test."""
    maximum_routes: int | None = Field(default=None, ge=0, le=4294967294)
    """The maximum allowable number of BGP routes. `0` means unlimited. Required field in the `VerifyBGPPeerRouteLimit` test"""
    warning_limit: int | None = Field(default=None, ge=0, le=4294967294)
    """The warning limit for the maximum routes. `0` means no warning.

    Optional field in the `VerifyBGPPeerRouteLimit` test. If not provided, the test will not verify the warning limit."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the BgpPeer for reporting."""
        return f"Peer: {self.peer_address} VRF: {self.vrf}"


class BgpNeighbor(BgpPeer):  # pragma: no cover
    """Alias for the BgpPeer model to maintain backward compatibility.

    When initialised, it will emit a deprecation warning and call the BgpPeer model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the BgpPeer class, emitting a depreciation warning."""
        warn(
            message="BgpNeighbor model is deprecated and will be removed in ANTA v2.0.0. Use the BgpPeer model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class VxlanEndpoint(BaseModel):
    """Model for a VXLAN endpoint."""

    address: IPv4Address | MacAddress
    """IPv4 or MAC address of the VXLAN endpoint."""
    vni: Vni
    """VNI of the VXLAN endpoint."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the VxlanEndpoint for reporting."""
        return f"Address: {self.address} VNI: {self.vni}"


class BgpRoute(BaseModel):
    """Model representing BGP routes.

    Only IPv4 prefixes are supported for now.
    """

    model_config = ConfigDict(extra="forbid")
    prefix: IPv4Network
    """The IPv4 network address."""
    vrf: str = "default"
    """Optional VRF for the BGP peer. Defaults to `default`."""
    paths: list[BgpRoutePath] | None = None
    """A list of paths for the BGP route. Required field in the `VerifyBGPRouteOrigin` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the BgpRoute for reporting.

        Examples
        --------
        - Prefix: 192.168.66.100/24 VRF: default
        """
        return f"Prefix: {self.prefix} VRF: {self.vrf}"


class BgpRoutePath(BaseModel):
    """Model representing a BGP route path."""

    model_config = ConfigDict(extra="forbid")
    nexthop: IPv4Address
    """The next-hop IPv4 address for the path."""
    origin: Literal["Igp", "Egp", "Incomplete"]
    """The BGP origin attribute of the route."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the RoutePath for reporting.

        Examples
        --------
        - Next-hop: 192.168.66.101 Origin: Igp
        """
        return f"Next-hop: {self.nexthop} Origin: {self.origin}"
