# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module that provides predefined types for AntaTest.Input instances."""

import re
from typing import Annotated, Literal

from pydantic import Field
from pydantic.functional_validators import AfterValidator, BeforeValidator


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
    intf_id_re = re.compile(r"[0-9]+(\/[0-9]+)*(\.[0-9]+)?")
    m = intf_id_re.search(v)
    if m is None:
        msg = f"Could not parse interface ID in interface '{v}'"
        raise ValueError(msg)
    intf_id = m[0]

    alias_map = {"et": "Ethernet", "eth": "Ethernet", "po": "Port-Channel", "lo": "Loopback"}

    for alias, full_name in alias_map.items():
        if v.lower().startswith(alias):
            return f"{full_name}{intf_id}"

    return v


def interface_case_sensitivity(v: str) -> str:
    """Reformat interface name to match expected case sensitivity.

    Examples
    --------
         - ethernet -> Ethernet
         - vlan -> Vlan
         - loopback -> Loopback

    """
    if isinstance(v, str) and len(v) > 0 and not v[0].isupper():
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
        r"\b(l2[\s\-]?vpn[\s\-]?evpn)\b": "l2VpnEvpn",
        r"\bipv4[\s_-]?mpls[\s_-]?label(s)?\b": "ipv4MplsLabels",
        r"\bipv4[\s_-]?mpls[\s_-]?vpn\b": "ipv4MplsVpn",
        r"\bipv4[\s_-]?uni[\s_-]?cast\b": "ipv4Unicast",
    }

    for pattern, replacement in patterns.items():
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return replacement

    return value


# ANTA framework
TestStatus = Literal["unset", "success", "failure", "error", "skipped"]

# AntaTest.Input types
AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan = Annotated[int, Field(ge=0, le=4094)]
MlagPriority = Annotated[int, Field(ge=1, le=32767)]
Vni = Annotated[int, Field(ge=1, le=16777215)]
Interface = Annotated[
    str,
    Field(pattern=r"^(Dps|Ethernet|Fabric|Loopback|Management|Port-Channel|Tunnel|Vlan|Vxlan)[0-9]+(\/[0-9]+)*(\.[0-9]+)?$"),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
VxlanSrcIntf = Annotated[
    str,
    Field(pattern=r"^(Loopback)([0-9]|[1-9][0-9]{1,2}|[1-7][0-9]{3}|8[01][0-9]{2}|819[01])$"),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
Afi = Literal["ipv4", "ipv6", "vpn-ipv4", "vpn-ipv6", "evpn", "rt-membership", "path-selection", "link-state"]
Safi = Literal["unicast", "multicast", "labeled-unicast", "sr-te"]
EncryptionAlgorithm = Literal["RSA", "ECDSA"]
RsaKeySize = Literal[2048, 3072, 4096]
EcdsaKeySize = Literal[256, 384, 521]
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
Hostname = Annotated[str, Field(pattern=r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")]
Port = Annotated[int, Field(ge=1, le=65535)]
