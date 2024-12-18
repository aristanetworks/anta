# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module that provides predefined types for AntaTest.Input instances."""

import re
from typing import Annotated, Literal

from pydantic import Field
from pydantic.functional_validators import AfterValidator, BeforeValidator

# Regular Expression definition
# TODO: make this configurable - with an env var maybe?
REGEXP_EOS_BLACKLIST_CMDS = [r"^reload.*", r"^conf\w*\s*(terminal|session)*", r"^wr\w*\s*\w+"]
"""List of regular expressions to blacklist from eos commands."""
REGEXP_PATH_MARKERS = r"[\\\/\s]"
"""Match directory path from string."""
REGEXP_INTERFACE_ID = r"\d+(\/\d+)*(\.\d+)?"
"""Match Interface ID lilke 1/1.1."""
REGEXP_TYPE_EOS_INTERFACE = r"^(Dps|Ethernet|Fabric|Loopback|Management|Port-Channel|Tunnel|Vlan|Vxlan)[0-9]+(\/[0-9]+)*(\.[0-9]+)?$"
"""Match EOS interface types like Ethernet1/1, Vlan1, Loopback1, etc."""
REGEXP_TYPE_VXLAN_SRC_INTERFACE = r"^(Loopback)([0-9]|[1-9][0-9]{1,2}|[1-7][0-9]{3}|8[01][0-9]{2}|819[01])$"
"""Match Vxlan source interface like Loopback10."""
REGEX_TYPE_PORTCHANNEL = r"^Port-Channel[0-9]{1,6}$"
"""Match Port Channel interface like Port-Channel5."""
REGEXP_TYPE_HOSTNAME = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
"""Match hostname like `my-hostname`, `my-hostname-1`, `my-hostname-1-2`."""

# Regexp BGP AFI/SAFI
REGEXP_BGP_L2VPN_AFI = r"\b(l2[\s\-]?vpn[\s\-]?evpn)\b"
"""Match L2VPN EVPN AFI."""
REGEXP_BGP_IPV4_MPLS_LABELS = r"\b(ipv4[\s\-]?mpls[\s\-]?label(s)?)\b"
"""Match IPv4 MPLS Labels."""
REGEX_BGP_IPV4_MPLS_VPN = r"\b(ipv4[\s\-]?mpls[\s\-]?vpn)\b"
"""Match IPv4 MPLS VPN."""
REGEX_BGP_IPV4_UNICAST = r"\b(ipv4[\s\-]?uni[\s\-]?cast)\b"
"""Match IPv4 Unicast."""


def aaa_group_prefix(v: str) -> str:
    """Prefix the AAA method with 'group' if it is known."""
    built_in_methods = ["local", "none", "logging"]
    return f"group {v}" if v not in built_in_methods and not v.startswith("group ") else v


def interface_autocomplete(v: str) -> str:
    """Allow the user to only provide the beginning of an interface name.

    Supported alias:
         - `et`, `eth` will be changed to `Ethernet`
         - `po` will be changed to `Port-Channel`
    - `lo` will be changed to `Loopback`
    """
    intf_id_re = re.compile(REGEXP_INTERFACE_ID)
    m = intf_id_re.search(v)
    if m is None:
        msg = f"Could not parse interface ID in interface '{v}'"
        raise ValueError(msg)
    intf_id = m[0]

    alias_map = {"et": "Ethernet", "eth": "Ethernet", "po": "Port-Channel", "lo": "Loopback"}

    return next((f"{full_name}{intf_id}" for alias, full_name in alias_map.items() if v.lower().startswith(alias)), v)


def interface_case_sensitivity(v: str) -> str:
    """Reformat interface name to match expected case sensitivity.

    Examples
    --------
    - ethernet -> Ethernet
    - vlan -> Vlan
    - loopback -> Loopback

    """
    if isinstance(v, str) and v != "" and not v[0].isupper():
        return f"{v[0].upper()}{v[1:]}"
    return v


def bgp_multiprotocol_capabilities_abbreviations(value: str) -> str:
    """Abbreviations for different BGP multiprotocol capabilities.

    Examples
    --------
    - IPv4 Unicast
    - L2vpnEVPN
    - ipv4 MPLS Labels
    - ipv4Mplsvpn

    """
    patterns = {
        REGEXP_BGP_L2VPN_AFI: "l2VpnEvpn",
        REGEXP_BGP_IPV4_MPLS_LABELS: "ipv4MplsLabels",
        REGEX_BGP_IPV4_MPLS_VPN: "ipv4MplsVpn",
        REGEX_BGP_IPV4_UNICAST: "ipv4Unicast",
    }

    for pattern, replacement in patterns.items():
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return replacement

    return value


def validate_regex(value: str) -> str:
    """Validate that the input value is a valid regex format."""
    try:
        re.compile(value)
    except re.error as e:
        msg = f"Invalid regex: {e}"
        raise ValueError(msg) from e
    return value


# AntaTest.Input types
AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan = Annotated[int, Field(ge=0, le=4094)]
MlagPriority = Annotated[int, Field(ge=1, le=32767)]
Vni = Annotated[int, Field(ge=1, le=16777215)]
Interface = Annotated[
    str,
    Field(pattern=REGEXP_TYPE_EOS_INTERFACE),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
EthernetInterface = Annotated[
    str,
    Field(pattern=r"^Ethernet[0-9]+(\/[0-9]+)*$"),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
VxlanSrcIntf = Annotated[
    str,
    Field(pattern=REGEXP_TYPE_VXLAN_SRC_INTERFACE),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
PortChannelInterface = Annotated[
    str,
    Field(pattern=REGEX_TYPE_PORTCHANNEL),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
Afi = Literal["ipv4", "ipv6", "vpn-ipv4", "vpn-ipv6", "evpn", "rt-membership", "path-selection", "link-state"]
Safi = Literal["unicast", "multicast", "labeled-unicast", "sr-te"]
EncryptionAlgorithm = Literal["RSA", "ECDSA"]
RsaKeySize = Literal[2048, 3072, 4096]
EcdsaKeySize = Literal[256, 384, 512]
MultiProtocolCaps = Annotated[str, BeforeValidator(bgp_multiprotocol_capabilities_abbreviations)]
BfdInterval = Annotated[int, Field(ge=50, le=60000)]
BfdMultiplier = Annotated[int, Field(ge=3, le=50)]
ErrDisableReasons = Literal[
    "acl",
    "arp-inspection",
    "bpduguard",
    "dot1x-session-replace",
    "hitless-reload-down",
    "lacp-rate-limit",
    "link-flap",
    "no-internal-vlan",
    "portchannelguard",
    "portsec",
    "tapagg",
    "uplink-failure-detection",
]
ErrDisableInterval = Annotated[int, Field(ge=30, le=86400)]
Percent = Annotated[float, Field(ge=0.0, le=100.0)]
PositiveInteger = Annotated[int, Field(ge=0)]
Revision = Annotated[int, Field(ge=1, le=99)]
Hostname = Annotated[str, Field(pattern=REGEXP_TYPE_HOSTNAME)]
Port = Annotated[int, Field(ge=1, le=65535)]
RegexString = Annotated[str, AfterValidator(validate_regex)]
BgpDropStats = Literal[
    "inDropAsloop",
    "inDropClusterIdLoop",
    "inDropMalformedMpbgp",
    "inDropOrigId",
    "inDropNhLocal",
    "inDropNhAfV6",
    "prefixDroppedMartianV4",
    "prefixDroppedMaxRouteLimitViolatedV4",
    "prefixDroppedMartianV6",
    "prefixDroppedMaxRouteLimitViolatedV6",
    "prefixLuDroppedV4",
    "prefixLuDroppedMartianV4",
    "prefixLuDroppedMaxRouteLimitViolatedV4",
    "prefixLuDroppedV6",
    "prefixLuDroppedMartianV6",
    "prefixLuDroppedMaxRouteLimitViolatedV6",
    "prefixEvpnDroppedUnsupportedRouteType",
    "prefixBgpLsDroppedReceptionUnsupported",
    "outDropV4LocalAddr",
    "outDropV6LocalAddr",
    "prefixVpnIpv4DroppedImportMatchFailure",
    "prefixVpnIpv4DroppedMaxRouteLimitViolated",
    "prefixVpnIpv6DroppedImportMatchFailure",
    "prefixVpnIpv6DroppedMaxRouteLimitViolated",
    "prefixEvpnDroppedImportMatchFailure",
    "prefixEvpnDroppedMaxRouteLimitViolated",
    "prefixRtMembershipDroppedLocalAsReject",
    "prefixRtMembershipDroppedMaxRouteLimitViolated",
]
BgpUpdateError = Literal["inUpdErrWithdraw", "inUpdErrIgnore", "inUpdErrDisableAfiSafi", "disabledAfiSafi", "lastUpdErrTime"]
BfdProtocol = Literal["bgp", "isis", "lag", "ospf", "ospfv3", "pim", "route-input", "static-bfd", "static-route", "vrrp", "vxlan"]
SnmpPdu = Literal["inGetPdus", "inGetNextPdus", "inSetPdus", "outGetResponsePdus", "outTrapPdus"]
SnmpErrorCounter = Literal[
    "inVersionErrs", "inBadCommunityNames", "inBadCommunityUses", "inParseErrs", "outTooBigErrs", "outNoSuchNameErrs", "outBadValueErrs", "outGeneralErrs"
]
