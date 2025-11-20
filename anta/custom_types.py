# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module that provides predefined types for AntaTest.Input instances."""

import re
from typing import Annotated, Literal

from pydantic import Field
from pydantic.functional_validators import AfterValidator, BeforeValidator

# Regular Expression definition
REGEXP_PATH_MARKERS = r"[\\\/\s]"
"""Match directory path from string."""
REGEXP_INTERFACE_ID = r"\d+(\/\d+)*(\.\d+)?"
"""Match Interface ID lilke 1/1.1."""
REGEXP_TYPE_EOS_INTERFACE = r"^(Dps|Ethernet|Fabric|Loopback|Management|Port-Channel|Recirc-Channel|Tunnel|Vlan|Vxlan)[0-9]+(\/[0-9]+)*(\.[0-9]+)?$"
"""Match EOS interface types like Ethernet1/1, Vlan1, Loopback1, etc."""
REGEXP_TYPE_VXLAN_SRC_INTERFACE = r"^(Dps1|Loopback(0|[1-9]\d{0,2}|[1-7]\d{3}|80[0-9]{2}|81[0-8]\d|819[01]))$"
"""Match Vxlan source interface like Loopback10/Dps1."""
REGEX_TYPE_PORTCHANNEL = r"^Port-Channel[0-9]{1,6}$"
"""Match Port Channel interface like Port-Channel5."""
REGEXP_EOS_INTERFACE_TYPE = r"^(Dps|Ethernet|Fabric|Loopback|Management|Port-Channel|Recirc-Channel|Tunnel|Vlan|Vxlan)$"
"""Match an EOS interface type like Ethernet or Loopback."""
REGEXP_TYPE_HOSTNAME = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
"""Match hostname like `my-hostname`, `my-hostname-1`, `my-hostname-1-2`."""


# Regular expression for BGP redistributed routes
REGEX_IPV4_UNICAST = r"ipv4[-_ ]?unicast$"
REGEX_IPV4_MULTICAST = r"ipv4[-_ ]?multicast$"
REGEX_IPV6_UNICAST = r"ipv6[-_ ]?unicast$"
REGEX_IPV6_MULTICAST = r"ipv6[-_ ]?multicast$"


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

    alias_map = {"et": "Ethernet", "eth": "Ethernet", "po": "Port-Channel", "lo": "Loopback", "vl": "Vlan"}

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

    Handles different separators (hyphen, underscore, space) and case sensitivity.

    Examples
    --------
    ```python
    >>> bgp_multiprotocol_capabilities_abbreviations("IPv4 Unicast")
    'ipv4Unicast'
    >>> bgp_multiprotocol_capabilities_abbreviations("ipv4-Flow_Spec Vpn")
    'ipv4FlowSpecVpn'
     >>> bgp_multiprotocol_capabilities_abbreviations("ipv6_labeled-unicast")
    'ipv6MplsLabels'
     >>> bgp_multiprotocol_capabilities_abbreviations("ipv4_mpls_vpn")
    'ipv4MplsVpn'
     >>> bgp_multiprotocol_capabilities_abbreviations("ipv4 mpls labels")
    'ipv4MplsLabels'
    >>> bgp_multiprotocol_capabilities_abbreviations("rt-membership")
    'rtMembership'
     >>> bgp_multiprotocol_capabilities_abbreviations("dynamic-path-selection")
    'dps'
    ```
    """
    patterns = {
        f"{r'dynamic[-_ ]?path[-_ ]?selection$'}": "dps",
        f"{r'dps$'}": "dps",
        f"{REGEX_IPV4_UNICAST}": "ipv4Unicast",
        f"{REGEX_IPV6_UNICAST}": "ipv6Unicast",
        f"{REGEX_IPV4_MULTICAST}": "ipv4Multicast",
        f"{REGEX_IPV6_MULTICAST}": "ipv6Multicast",
        f"{r'ipv4[-_ ]?labeled[-_ ]?Unicast$'}": "ipv4MplsLabels",
        f"{r'ipv4[-_ ]?mpls[-_ ]?labels$'}": "ipv4MplsLabels",
        f"{r'ipv6[-_ ]?labeled[-_ ]?Unicast$'}": "ipv6MplsLabels",
        f"{r'ipv6[-_ ]?mpls[-_ ]?labels$'}": "ipv6MplsLabels",
        f"{r'ipv4[-_ ]?sr[-_ ]?te$'}": "ipv4SrTe",  # codespell:ignore
        f"{r'ipv6[-_ ]?sr[-_ ]?te$'}": "ipv6SrTe",  # codespell:ignore
        f"{r'ipv4[-_ ]?mpls[-_ ]?vpn$'}": "ipv4MplsVpn",
        f"{r'ipv6[-_ ]?mpls[-_ ]?vpn$'}": "ipv6MplsVpn",
        f"{r'ipv4[-_ ]?Flow[-_ ]?spec$'}": "ipv4FlowSpec",
        f"{r'ipv6[-_ ]?Flow[-_ ]?spec$'}": "ipv6FlowSpec",
        f"{r'ipv4[-_ ]?Flow[-_ ]?spec[-_ ]?vpn$'}": "ipv4FlowSpecVpn",
        f"{r'ipv6[-_ ]?Flow[-_ ]?spec[-_ ]?vpn$'}": "ipv6FlowSpecVpn",
        f"{r'l2[-_ ]?vpn[-_ ]?vpls$'}": "l2VpnVpls",
        f"{r'l2[-_ ]?vpn[-_ ]?evpn$'}": "l2VpnEvpn",
        f"{r'link[-_ ]?state$'}": "linkState",
        f"{r'rt[-_ ]?membership$'}": "rtMembership",
        f"{r'ipv4[-_ ]?rt[-_ ]?membership$'}": "rtMembership",
        f"{r'ipv4[-_ ]?mvpn$'}": "ipv4Mvpn",
    }
    for pattern, replacement in patterns.items():
        match = re.match(pattern, value, re.IGNORECASE)
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


def bgp_redistributed_route_proto_abbreviations(value: str) -> str:
    """Abbreviations for different BGP redistributed route protocols.

    Handles different separators (hyphen, underscore, space) and case sensitivity.

    Examples
    --------
    ```python
    >>> bgp_redistributed_route_proto_abbreviations("IPv4 Unicast")
    'v4u'
    >>> bgp_redistributed_route_proto_abbreviations("IPv4-multicast")
    'v4m'
    >>> bgp_redistributed_route_proto_abbreviations("IPv6_multicast")
    'v6m'
    >>> bgp_redistributed_route_proto_abbreviations("ipv6unicast")
    'v6u'
    ```
    """
    patterns = {REGEX_IPV4_UNICAST: "v4u", REGEX_IPV4_MULTICAST: "v4m", REGEX_IPV6_UNICAST: "v6u", REGEX_IPV6_MULTICAST: "v6m"}

    for pattern, replacement in patterns.items():
        match = re.match(pattern, value, re.IGNORECASE)
        if match:
            return replacement

    return value


def update_bgp_redistributed_proto_user(value: str) -> str:
    """Update BGP redistributed route `User` proto with EOS SDK.

    Examples
    --------
    ```python
    >>> update_bgp_redistributed_proto_user("User")
    'EOS SDK'
    >>> update_bgp_redistributed_proto_user("Bgp")
    'Bgp'
    >>> update_bgp_redistributed_proto_user("RIP")
    'RIP'
    ```
    """
    if value == "User":
        value = "EOS SDK"

    return value


def convert_reload_cause(value: str) -> str:
    """Convert a reload cause abbreviation into its full descriptive string.

    Examples
    --------
    ```python
    >>> convert_reload_cause("ZTP")
    'System reloaded due to Zero Touch Provisioning'
    ```
    """
    reload_causes = {
        "ZTP": "System reloaded due to Zero Touch Provisioning",
        "USER": "Reload requested by the user.",
        "FPGA": "Reload requested after FPGA upgrade",
        "USER_HITLESS": "Hitless reload requested by the user.",
    }
    if value in reload_causes.values():
        return value
    if not reload_causes.get(value.upper()):
        msg = f"Invalid reload cause: '{value}' - expected causes are {list(reload_causes)}"
        raise ValueError(msg)
    return reload_causes[value.upper()]


def update_ipv4_route_type(value: str) -> str:
    """Update an IPv4 route type CLI description into the eAPI JSON schema key.

    Examples
    --------
    ```python
    >>> update_ipv4_route_type("OSPF inter area"")
    'ospfInterArea'
    >>> update_ipv4_route_type("BGP Aggregate")
    'bgpAggregate'
    >>> update_ipv4_route_type("connected")
    'connected'
    ```
    """
    route_types = {
        "OSPF inter area": "ospfInterArea",
        "OSPF external type 1": "ospfExternalType1",
        "OSPF external type 2": "ospfExternalType2",
        "OSPF NSSA external type 1": "ospfNssaExternalType1",
        "OSPF NSSA external type2": "ospfNssaExternalType2",
        "Other BGP Routes": "BGP",
        "IS-IS level 1": "ISISLevel1",
        "IS-IS level 2": "ISISLevel2",
        "BGP Aggregate": "bgpAggregate",
        "OSPF Summary": "ospfSummary",
        "Nexthop Group Static Route": "nexthopGroupStaticRoute",
        "VXLAN Control Service": "vcs",
        "Martian": "martian",
        "DHCP client installed default route": "dhcp",
        "Dynamic Policy Route": "dynamicPolicy",
        "gRIBI": "gribi",
        "Route Cache Route": "routeCacheConnected",
        "CBF Leaked Route": "CBFLeaked",
        "Drop Route": "dropRoute",
    }
    if value not in route_types:
        return value

    return route_types[value]


# AntaTest.Input types
AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
VlanId = Annotated[int, Field(ge=0, le=4094)]
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
    Field(pattern=r"^Ethernet\d+(?:/\d+){0,2}$"),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
ManagementInterface = Annotated[
    str,
    Field(pattern=r"^Management\d+(?:/\d+){0,2}$"),
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
InterfaceType = Annotated[
    str,
    Field(pattern=REGEXP_EOS_INTERFACE_TYPE),
    BeforeValidator(interface_case_sensitivity),
]
Afi = Literal["ipv4", "ipv6", "vpn-ipv4", "vpn-ipv6", "evpn", "rt-membership", "path-selection", "link-state"]
Safi = Literal["unicast", "multicast", "labeled-unicast", "sr-te"]
EncryptionAlgorithm = Literal["RSA", "ECDSA"]
RsaKeySize = Literal[2048, 3072, 4096]
EcdsaKeySize = Literal[256, 384, 512]
MultiProtocolCaps = Annotated[
    Literal[
        "dps",
        "ipv4Unicast",
        "ipv6Unicast",
        "ipv4Multicast",
        "ipv6Multicast",
        "ipv4MplsLabels",
        "ipv6MplsLabels",
        "ipv4SrTe",
        "ipv6SrTe",
        "ipv4MplsVpn",
        "ipv6MplsVpn",
        "ipv4FlowSpec",
        "ipv6FlowSpec",
        "ipv4FlowSpecVpn",
        "ipv6FlowSpecVpn",
        "l2VpnVpls",
        "l2VpnEvpn",
        "linkState",
        "rtMembership",
        "ipv4Mvpn",
    ],
    BeforeValidator(bgp_multiprotocol_capabilities_abbreviations),
]
BfdInterval = Annotated[int, Field(ge=50, le=60000)]
BfdMultiplier = Annotated[int, Field(ge=3, le=50)]
ErrDisableReasons = Literal[
    "acl",
    "arp-inspection",
    "bgp-session-tracking",
    "bpduguard",
    "dot1x",
    "dot1x-coa",
    "dot1x-session-replace",
    "evpn-sa-mh",
    "fabric-link-failure",
    "fabric-link-flap",
    "hitless-reload-down",
    "lacp-no-portid",
    "lacp-rate-limit",
    "license-enforce",
    "link-flap",
    "mlagasu",
    "mlagdualprimary",
    "mlagissu",
    "mlagmaintdown",
    "no-internal-vlan",
    "out-of-voqs",
    "portchannelguard",
    "portgroup-disabled",
    "portsec",
    "speed-misconfigured",
    "storm-control",
    "stp-no-portid",
    "stuck-queue",
    "tapagg",
    "uplink-failure-detection",
    "xcvr-misconfigured",
    "xcvr-overheat",
    "xcvr-power-unsupported",
    "xcvr-unsupported",
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
IPv4RouteType = Annotated[
    Literal[
        "connected",
        "static",
        "kernel",
        "OSPF",
        "OSPF inter area",
        "OSPF external type 1",
        "OSPF external type 2",
        "OSPF NSSA external type 1",
        "OSPF NSSA external type2",
        "Other BGP Routes",
        "iBGP",
        "eBGP",
        "RIP",
        "IS-IS level 1",
        "IS-IS level 2",
        "OSPFv3",
        "BGP Aggregate",
        "OSPF Summary",
        "Nexthop Group Static Route",
        "VXLAN Control Service",
        "Martian",
        "DHCP client installed default route",
        "Dynamic Policy Route",
        "gRIBI",
        "Route Cache Route",
        "CBF Leaked Route",
        "dropRoute",
    ],
    AfterValidator(update_ipv4_route_type),
]
DynamicVlanSource = Literal["dmf", "dot1x", "dynvtep", "evpn", "mlag", "mlagsync", "mvpn", "swfwd", "vccbfd"]
LogSeverityLevel = Literal["alerts", "critical", "debugging", "emergencies", "errors", "informational", "notifications", "warnings"]


########################################
# SNMP
########################################
def snmp_v3_prefix(auth_type: Literal["auth", "priv", "noauth"]) -> str:
    """Prefix the SNMP authentication type with 'v3'."""
    if auth_type == "noauth":
        return "v3NoAuth"
    return f"v3{auth_type.title()}"


SnmpVersion = Literal["v1", "v2c", "v3"]
SnmpHashingAlgorithm = Literal["MD5", "SHA", "SHA-224", "SHA-256", "SHA-384", "SHA-512"]
SnmpEncryptionAlgorithm = Literal["AES-128", "AES-192", "AES-256", "DES"]
SnmpPdu = Literal["inGetPdus", "inGetNextPdus", "inSetPdus", "outGetResponsePdus", "outTrapPdus"]
SnmpErrorCounter = Literal[
    "inVersionErrs", "inBadCommunityNames", "inBadCommunityUses", "inParseErrs", "outTooBigErrs", "outNoSuchNameErrs", "outBadValueErrs", "outGeneralErrs"
]
SnmpVersionV3AuthType = Annotated[Literal["auth", "priv", "noauth"], AfterValidator(snmp_v3_prefix)]
RedistributedProtocol = Annotated[
    Literal[
        "AttachedHost",
        "Bgp",
        "Connected",
        "DHCP",
        "Dynamic",
        "IS-IS",
        "OSPF Internal",
        "OSPF External",
        "OSPF Nssa-External",
        "OSPFv3 Internal",
        "OSPFv3 External",
        "OSPFv3 Nssa-External",
        "RIP",
        "Static",
        "User",
    ],
    AfterValidator(update_bgp_redistributed_proto_user),
]
RedistributedAfiSafi = Annotated[Literal["v4u", "v4m", "v6u", "v6m"], BeforeValidator(bgp_redistributed_route_proto_abbreviations)]
NTPStratumLevel = Annotated[int, Field(ge=0, le=16)]
PowerSupplyFanStatus = Literal["failed", "ok", "unknownHwStatus", "powerLoss", "unsupported"]
PowerSupplyStatus = Literal["ok", "unknown", "powerLoss", "failed"]
ReloadCause = Annotated[
    Literal[
        "System reloaded due to Zero Touch Provisioning",
        "Reload requested by the user.",
        "Reload requested after FPGA upgrade",
        "Hitless reload requested by the user.",
        "USER",
        "FPGA",
        "ZTP",
        "USER_HITLESS",
    ],
    BeforeValidator(convert_reload_cause),
]
BgpCommunity = Literal["standard", "extended", "large"]
DropPrecedence = Literal["DP0", "DP1", "DP2"]
ModuleStatus = Literal["failed", "disabledUntilSystemUpgrade", "ok", "poweredOff", "active", "disabled", "upgradingFpga", "poweringOn", "unknown", "standby"]
