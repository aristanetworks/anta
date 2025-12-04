# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing BGP tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import TYPE_CHECKING, Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import Afi, BgpCommunity, BgpDropStats, BgpUpdateError, Interface, MultiProtocolCaps, RedistributedAfiSafi, RedistributedProtocol, Safi, Vni

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
AFI_SAFI_MAPPINGS = {"v4u": "IPv4 Unicast", "v4m": "IPv4 Multicast", "v6u": "IPv6 Unicast", "v6m": "IPv6 Multicast"}
"""Dictionary mapping AFI/SAFI to EOS key representation for BGP redistributed route protocol."""
IPV4_MULTICAST_SUPPORTED_PROTO = [
    "AttachedHost",
    "Connected",
    "IS-IS",
    "OSPF Internal",
    "OSPF External",
    "OSPF Nssa-External",
    "OSPFv3 Internal",
    "OSPFv3 External",
    "OSPFv3 Nssa-External",
    "Static",
]
"""List of BGP redistributed route protocol, supported for IPv4 multicast address family."""
IPV6_MULTICAST_SUPPORTED_PROTO = [proto for proto in IPV4_MULTICAST_SUPPORTED_PROTO if proto != "AttachedHost"]
"""List of BGP redistributed route protocol, supported for IPv6 multicast address family."""


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

    Can be enabled in the `VerifyBGPPeerCount` tests."""

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

    Supports IPv4, IPv6 and IPv6 link-local neighbors.

    Also supports RFC5549 by providing the interface to be used for session establishment.
    """

    model_config = ConfigDict(extra="forbid")
    peer_address: IPv4Address | IPv6Address | None = None
    """IP address of the BGP peer. Optional only if using `interface` for BGP RFC5549."""
    interface: Interface | None = None
    """Interface to be used for BGP RFC5549 session establishment."""
    vrf: str = "default"
    """VRF for the BGP peer."""
    description: str | None = None
    """Optional metadata describing the BGP peer or RFC5549 interface. Used for reporting."""
    peer_group: str | None = None
    """Peer group of the BGP peer. Required field in the `VerifyBGPPeerGroup` test."""
    advertised_routes: list[IPv4Network | IPv6Network] | None = None
    """List of advertised routes in CIDR format. Required field in the `VerifyBGPExchangedRoutes` test."""
    received_routes: list[IPv4Network | IPv6Network] | None = None
    """List of received routes in CIDR format. Required field in the `VerifyBGPExchangedRoutes` test."""
    capabilities: list[MultiProtocolCaps] | None = None
    """List of BGP multiprotocol capabilities. Required field in the `VerifyBGPPeerMPCaps`, `VerifyBGPNlriAcceptance` tests."""
    strict: bool = False
    """If True, requires exact match of the provided BGP multiprotocol capabilities.

    Optional field in the `VerifyBGPPeerMPCaps` test."""
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
    """Inbound route map applied to the peer. Optional field in the `VerifyBgpRouteMaps` test. If not provided, `outbound_route_map` must be provided."""
    outbound_route_map: str | None = None
    """Outbound route map applied to the peer. Optional field in the `VerifyBgpRouteMaps` test. If not provided, `inbound_route_map` must be provided."""
    maximum_routes: int | None = Field(default=None, ge=0, le=4294967294)
    """The maximum allowable number of BGP routes. `0` means unlimited. Required field in the `VerifyBGPPeerRouteLimit` test."""
    warning_limit: int | None = Field(default=None, ge=0, le=4294967294)
    """The warning limit for the maximum routes. `0` means no warning.

    Optional field in the `VerifyBGPPeerRouteLimit` test. If not provided, the test will not verify the warning limit."""
    ttl: int | None = Field(default=None, ge=1, le=255)
    """The Time-To-Live (TTL). Required field in the `VerifyBGPPeerTtlMultiHops` test."""
    max_ttl_hops: int | None = Field(default=None, ge=1, le=255)
    """The Max TTL hops. Required field in the `VerifyBGPPeerTtlMultiHops` test."""
    advertised_communities: list[BgpCommunity] = Field(default=["standard", "extended", "large"])
    """List of advertised communities to be verified.

    Optional field in the `VerifyBGPAdvCommunities` test. If not provided, the test will verify that all communities are advertised."""

    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        """Validate the inputs provided to the BgpPeer class.

        Either `peer_address` or `interface` must be provided, not both.
        """
        if (self.peer_address is None) == (self.interface is None):
            msg = "Exactly one of 'peer_address' or 'interface' must be provided"
            raise ValueError(msg)
        return self

    def __str__(self) -> str:
        """Return a human-readable string representation of the BgpPeer for reporting."""
        identifier = f"Peer: {self.peer_address}" if self.peer_address is not None else f"Interface: {self.interface}"
        description = f" ({self.description})" if self.description else ""
        return f"{identifier}{description} VRF: {self.vrf}"


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
    """A list of paths for the BGP route. Required field in the `VerifyBGPRoutePaths` test."""
    ecmp_count: int | None = None
    """The expected number of ECMP paths for the BGP route. Required field in the `VerifyBGPRouteECMP` test."""

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


class BgpVrf(BaseModel):
    """Model representing a VRF in a BGP instance."""

    vrf: str = "default"
    """VRF context."""
    address_families: list[AddressFamilyConfig]
    """List of address family configuration."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the BgpVrf for reporting.

        Examples
        --------
        - VRF: default
        """
        return f"VRF: {self.vrf}"


class RedistributedRouteConfig(BaseModel):
    """Model representing a BGP redistributed route configuration."""

    proto: RedistributedProtocol
    """The redistributed protocol."""
    include_leaked: bool = False
    """Flag to include leaked routes of the redistributed protocol while redistributing."""
    route_map: str | None = None
    """Optional route map applied to the redistribution."""

    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        """Validate that 'include_leaked' is not set when the redistributed protocol is AttachedHost, User, Dynamic, or RIP."""
        if self.include_leaked and self.proto in ["AttachedHost", "EOS SDK", "Dynamic", "RIP"]:
            msg = f"'include_leaked' field is not supported for redistributed protocol '{self.proto}'"
            raise ValueError(msg)
        return self

    def __str__(self) -> str:
        """Return a human-readable string representation of the RedistributedRouteConfig for reporting.

        Examples
        --------
        - Proto: Connected, Include Leaked: True, Route Map: RM-CONN-2-BGP
        """
        base_string = f"Proto: {self.proto}"
        if self.include_leaked:
            base_string += f", Include Leaked: {self.include_leaked}"
        if self.route_map:
            base_string += f", Route Map: {self.route_map}"
        return base_string


class AddressFamilyConfig(BaseModel):
    """Model representing a BGP address family configuration."""

    afi_safi: RedistributedAfiSafi
    """AFI/SAFI abbreviation per EOS."""
    redistributed_routes: list[RedistributedRouteConfig]
    """List of redistributed route configuration."""

    @model_validator(mode="after")
    def validate_afi_safi_supported_routes(self) -> Self:
        """Validate each address family supported redistributed protocol.

        Following table shows the supported redistributed routes for each address family.

        |    IPv4 Unicast         |    IPv6 Unicast         |   IPv4 Multicast       |   IPv6 Multicast       |
        |-------------------------|-------------------------|------------------------|------------------------|
        |    AttachedHost         |    AttachedHost         |   AttachedHost         |   Connected            |
        |    Bgp                  |    Bgp                  |   Connected            |   IS-IS                |
        |    Connected            |    Connected            |   IS-IS                |   OSPF Internal        |
        |    Dynamic              |    DHCP                 |   OSPF Internal        |   OSPF External        |
        |    IS-IS                |    Dynamic              |   OSPF External        |   OSPF Nssa-External   |
        |    OSPF Internal        |    IS-IS                |   OSPF Nssa-External   |   OSPFv3 Internal      |
        |    OSPF External        |    OSPFv3 Internal      |   OSPFv3 Internal      |   OSPFv3 External      |
        |    OSPF Nssa-External   |    OSPFv3 External      |   OSPFv3 External      |   OSPFv3 Nssa-External |
        |    OSPFv3 Internal      |    OSPFv3 Nssa-External |   OSPFv3 Nssa-External |   Static               |
        |    OSPFv3 External      |    Static               |   Static               |                        |
        |    OSPFv3 Nssa-External |    User                 |                        |                        |
        |    RIP                  |                         |                        |                        |
        |    Static               |                         |                        |                        |
        |    User                 |                         |                        |                        |
        """
        for routes_data in self.redistributed_routes:
            if all([self.afi_safi == "v4u", routes_data.proto == "DHCP"]):
                msg = f"Redistributed protocol 'DHCP' is not supported for address-family '{AFI_SAFI_MAPPINGS[self.afi_safi]}'"
                raise ValueError(msg)

            if self.afi_safi == "v6u" and routes_data.proto in ["OSPF Internal", "OSPF External", "OSPF Nssa-External", "RIP"]:
                msg = f"Redistributed protocol '{routes_data.proto}' is not supported for address-family '{AFI_SAFI_MAPPINGS[self.afi_safi]}'"
                raise ValueError(msg)

            if self.afi_safi == "v4m" and routes_data.proto not in IPV4_MULTICAST_SUPPORTED_PROTO:
                msg = f"Redistributed protocol '{routes_data.proto}' is not supported for address-family '{AFI_SAFI_MAPPINGS[self.afi_safi]}'"
                raise ValueError(msg)

            if self.afi_safi == "v6m" and routes_data.proto not in IPV6_MULTICAST_SUPPORTED_PROTO:
                msg = f"Redistributed protocol '{routes_data.proto}' is not supported for address-family '{AFI_SAFI_MAPPINGS[self.afi_safi]}'"
                raise ValueError(msg)

        return self

    def __str__(self) -> str:
        """Return a human-readable string representation of the AddressFamilyConfig for reporting.

        Examples
        --------
        - AFI-SAFI: IPv4 Unicast
        """
        return f"AFI-SAFI: {AFI_SAFI_MAPPINGS[self.afi_safi]}"
