# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.evpn.py."""

from __future__ import annotations

from typing import Any

from anta.tests.evpn import VerifyEVPNType5Routes
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success-all",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10},
                {"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local"}]},
                {"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]},
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-across-all-rds",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                    "RD: 10.100.1.4:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.4:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-specific-rd",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                            {
                                "nextHop": "10.100.2.4",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local"}]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-specific-nexthop",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-RTs",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-all",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": False,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10},
                {"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local"}]},
                {"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]},
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.100.0.128/31 VNI: 10 - No active and valid path found across all RDs",
                "Prefix: 10.100.0.128/31 VNI: 10 RD: 10.100.1.3:10 - No active and valid path found",
                "Prefix: 10.100.4.0/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 - No active and valid path found",
                "Prefix: 10.100.4.1/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 RTs: 10:10 - No active and valid path found",
            ],
        },
    },
    {
        "name": "failure-not-configured",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {"vrf": "default", "routerId": "10.100.1.5", "asn": 65102, "evpnRoutes": {}},
            {"vrf": "default", "routerId": "10.100.1.5", "asn": 65102, "evpnRoutes": {}},
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10},
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.100.0.128/31 VNI: 10 - No EVPN Type-5 routes found",
                "Prefix: 10.100.4.1/31 VNI: 10 - No EVPN Type-5 routes found",
            ],
        },
    },
    {
        "name": "failure-route-not-found-with-specified-rd-domain",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "remote", "rd": "10.100.1.4:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                            {
                                "nextHop": "10.100.2.4",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local"}]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.100.0.128/31 VNI: 10 RD: 10.100.1.3:10 - Route not found",
            ],
        },
    },
    {
        "name": "failiure-specific-nexthop-path-not-found",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.4",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.100.4.0/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 - Path not found",
            ],
        },
    },
    {
        "name": "failiure-specific-nexthop-RTs-path-not-found",
        "test": VerifyEVPNType5Routes,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.4.0/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.4.0/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                                "routeDetail": {
                                    "extCommunities": ["Route-Target-AS:20:20", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"],
                                },
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "prefixes": [
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.100.4.1/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 RTs: 10:10 - Path not found",
            ],
        },
    },
]
