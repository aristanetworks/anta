# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""BGP command outputs captured from vEOS and CloudEOS 4.31 through 4.36 for advisory tests."""

from __future__ import annotations

from typing import Any

# `show running-config | section router bgp` rendered identically on every captured release.
BGP_CONFIG = """router bgp 65010
   router-id 192.0.2.10
   bgp transport listen-port 1179
   neighbor PS peer group
   neighbor PS remote-as 65011
   neighbor 192.0.2.1 remote-as 65011
   neighbor 192.0.2.2 peer group PS
   neighbor 192.0.2.3 remote-as 65011
   neighbor 192.0.2.3 shutdown
   neighbor 192.0.2.4 peer group PS
   neighbor 2001:db8::1 remote-as 65011
   !
   address-family ipv4 sr-te
      neighbor 192.0.2.3 activate
   !
   address-family ipv6 sr-te
      neighbor 2001:db8::1 activate
   !
   address-family path-selection
      neighbor PS activate
      neighbor 192.0.2.1 activate
      no neighbor 192.0.2.4 activate
   !
   vrf PROBE
      router-id 192.0.2.11
      bgp transport listen-port 2179
      neighbor 192.0.2.5 remote-as 65012
"""
# `show bgp instance vrf all` text output captured from vEOS-lab 4.31.0F with a zero-peer instance.
BGP_INSTANCE = "BGP instance information for VRF default\nBGP Local AS:   65010, Router ID: 192.0.2.10\nTotal peers:              0\n"


def route_summary(configured: str = "multi-agent", operating: str = "multi-agent") -> dict[str, Any]:
    """Return `show ip route summary` revision 3 output; 4.31.2F reported ribd/multi-agent while awaiting reload."""
    return {
        "protoModelStatus": {"operatingProtoModel": operating, "configuredProtoModel": configured},
        "vrfs": {"default": {"connected": 1, "static": 1, "totalRoutes": 7}},
    }


def bgp_instances(*ports: tuple[str, int, int]) -> dict[str, Any]:
    """Return `show bgp instance vrf all` revision 3 JSON trimmed to its listen-port keys (vEOS 4.31.1F to 4.34.0F), one VRF per (vrf, v4, v6)."""
    return {
        "vrfs": {
            vrf: {"localAs": 65010, "bgpIpv4Listening": True, "bgpIpv4ListenPort": ipv4, "bgpIpv6Listening": True, "bgpIpv6ListenPort": ipv6}
            for vrf, ipv4, ipv6 in (ports or (("default", 179, 179),))
        }
    }
