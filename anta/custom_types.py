# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Module that provides predefined types for AntaTest.Input instances
"""
import re
from typing import Literal

from pydantic import Field
from pydantic.functional_validators import AfterValidator, BeforeValidator
from typing_extensions import Annotated


def aaa_group_prefix(v: str) -> str:
    """Prefix the AAA method with 'group' if it is known"""
    built_in_methods = ["local", "none", "logging"]
    return f"group {v}" if v not in built_in_methods and not v.startswith("group ") else v


def interface_autocomplete(v: str) -> str:
    """Allow the user to only provide the beginning of an interface name.

    Supported alias:
         - `et`, `eth` will be changed to `Ethernet`
         - `po` will be changed to `Port-Channel`"""
    intf_id_re = re.compile(r"[0-9]+(\/[0-9]+)*(\.[0-9]+)?")
    m = intf_id_re.search(v)
    if m is None:
        raise ValueError(f"Could not parse interface ID in interface '{v}'")
    intf_id = m[0]
    if any(v.lower().startswith(p) for p in ["et", "eth"]):
        return f"Ethernet{intf_id}"
    if v.lower().startswith("po"):
        return f"Port-Channel{intf_id}"
    return v


def interface_case_sensitivity(v: str) -> str:
    """Reformat interface name to match expected case sensitivity.

    Examples:
         - ethernet -> Ethernet
         - vlan -> Vlan
    """
    if isinstance(v, str) and len(v) > 0 and not v[0].isupper():
        return f"{v[0].upper()}{v[1:]}"
    return v


# ANTA framework
TestStatus = Literal["unset", "success", "failure", "error", "skipped"]

# AntaTest.Input types
AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan = Annotated[int, Field(ge=0, le=4094)]
Vni = Annotated[int, Field(ge=1, le=16777215)]
Interface = Annotated[
    str,
    Field(pattern=r"^(Dps|Ethernet|Fabric|Loopback|Management|Port-Channel|Tunnel|Vlan|Vxlan)[0-9]+(\/[0-9]+)*(\.[0-9]+)?$"),
    BeforeValidator(interface_autocomplete),
    BeforeValidator(interface_case_sensitivity),
]
Afi = Literal["ipv4", "ipv6", "vpn-ipv4", "vpn-ipv6", "evpn", "rt-membership"]
Safi = Literal["unicast", "multicast", "labeled-unicast"]
