# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Module that provides predefined types for AntaTest.Input instances
"""
from typing import Literal

from pydantic import Field
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


def aaa_group_prefix(v: str) -> str:
    """Prefix the AAA method with 'group' if it is known"""
    built_in_methods = ["local", "none", "logging"]
    return f"group {v}" if v not in built_in_methods and not v.startswith("group ") else v


AAAAuthMethod = Annotated[str, AfterValidator(aaa_group_prefix)]
Vlan = Annotated[int, Field(ge=0, le=4094)]
TestStatus = Literal["unset", "success", "failure", "error", "skipped"]
Interface = Annotated[str, Field(pattern=r"^(Ethernet|Fabric|Loopback|Management|Port-Channel|Tunnel|Vlan|Vxlan)[0-9]+(\/[0-9]+)*(\.[0-9]+)?$")]
Afi = Literal["ipv4", "ipv6", "vpn-ipv4", "vpn-ipv6", "evpn", "rt-membership"]
Safi = Literal["unicast", "multicast", "labeled-unicast"]
