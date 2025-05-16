# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.evpn.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.evpn import VerifyEVPNType5Routes
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyEVPNType5Routes, "success-all"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": True, "valid": True}}],
                    }
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": True, "valid": True}}],
                    }
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "success-ipv6"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.21",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.21:500 ip-prefix fd00:dc:5::1/128": {
                        "totalPaths": 1,
                        "routeKeyDetail": {"ipGenPrefix": "fd00:dc:5::1/128", "domain": "local", "rd": "10.1.0.21:500", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "",
                                "asPathEntry": {"asPathType": "Local", "asPath": "i"},
                                "reasonNotBestpath": "noReason",
                                "routeType": {"active": True, "valid": True},
                            }
                        ],
                    },
                    "RD: 10.1.0.21:500 ip-prefix fd00:dc:5::1/128 remote": {
                        "totalPaths": 1,
                        "routeKeyDetail": {"ipGenPrefix": "fd00:dc:5::1/128", "domain": "remote", "rd": "10.1.0.21:500", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "",
                                "asPathEntry": {"asPathType": "Local", "asPath": "i"},
                                "reasonNotBestpath": "noReason",
                                "routeType": {"active": True, "valid": True},
                            }
                        ],
                    },
                },
            }
        ],
        "inputs": {"prefixes": [{"address": "fd00:dc:5::1/128", "vni": 500}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "success-across-all-rds"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": True, "valid": True}}],
                    },
                    "RD: 10.100.1.4:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.4:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": False, "valid": False}}],
                    },
                },
            }
        ],
        "inputs": {"prefixes": [{"address": "10.100.0.128/31", "vni": 10}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "success-specific-rd"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {"nextHop": "10.100.2.3", "routeType": {"active": False, "valid": False}},
                            {"nextHop": "10.100.2.4", "routeType": {"active": True, "valid": True}},
                        ],
                    }
                },
            }
        ],
        "inputs": {"prefixes": [{"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local"}]}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "success-specific-nexthop"): {
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            },
                            {
                                "nextHop": "10.100.2.3",
                                "routeType": {"active": False, "valid": False},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            },
                        ],
                    }
                },
            }
        ],
        "inputs": {
            "prefixes": [{"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]}]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "success-RTs"): {
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
                },
            }
        ],
        "inputs": {
            "prefixes": [
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                }
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEVPNType5Routes, "failure-all"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": False, "valid": True}}],
                    }
                },
            },
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "local", "rd": "10.100.1.3:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [{"nextHop": "10.100.2.3", "routeType": {"active": False, "valid": True}}],
                    }
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
                                "routeType": {"active": True, "valid": False},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
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
                                "routeType": {"active": False, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Prefix: 10.100.0.128/31 VNI: 10 - No active and valid path found across all RDs",
                "Prefix: 10.100.0.128/31 VNI: 10 RD: 10.100.1.3:10 - No active and valid path found",
                "Prefix: 10.100.4.0/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 - No active and valid path found",
                "Prefix: 10.100.4.1/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 RTs: 10:10 - No active and valid path found",
            ],
        },
    },
    (VerifyEVPNType5Routes, "failure-not-configured"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": ["Prefix: 10.100.0.128/31 VNI: 10 - No EVPN Type-5 routes found", "Prefix: 10.100.4.1/31 VNI: 10 - No EVPN Type-5 routes found"],
        },
    },
    (VerifyEVPNType5Routes, "failure-route-not-found-with-specified-rd-domain"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.100.1.5",
                "asn": 65102,
                "evpnRoutes": {
                    "RD: 10.100.1.3:10 ip-prefix 10.100.0.128/31": {
                        "routeKeyDetail": {"ipGenPrefix": "10.100.0.128/31", "domain": "remote", "rd": "10.100.1.4:10", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {"nextHop": "10.100.2.3", "routeType": {"active": False, "valid": False}},
                            {"nextHop": "10.100.2.4", "routeType": {"active": True, "valid": True}},
                        ],
                    }
                },
            }
        ],
        "inputs": {"prefixes": [{"address": "10.100.0.128/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "remote"}]}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: 10.100.0.128/31 VNI: 10 RD: 10.100.1.3:10 Domain: remote - Route not found"]},
    },
    (VerifyEVPNType5Routes, "failiure-specific-nexthop-path-not-found"): {
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:10:10", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
                },
            }
        ],
        "inputs": {
            "prefixes": [{"address": "10.100.4.0/31", "vni": 10, "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3"}]}]}]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: 10.100.4.0/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 - Path not found"]},
    },
    (VerifyEVPNType5Routes, "failiure-specific-nexthop-RTs-path-not-found"): {
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
                                "routeType": {"active": True, "valid": True},
                                "routeDetail": {"extCommunities": ["Route-Target-AS:20:20", "TunnelEncap:tunnelTypeVxlan", "EvpnRouterMac:02:1c:73:71:73:45"]},
                            }
                        ],
                    }
                },
            }
        ],
        "inputs": {
            "prefixes": [
                {
                    "address": "10.100.4.1/31",
                    "vni": 10,
                    "routes": [{"rd": "10.100.1.3:10", "domain": "local", "paths": [{"nexthop": "10.100.2.3", "route_targets": ["10:10"]}]}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Prefix: 10.100.4.1/31 VNI: 10 RD: 10.100.1.3:10 Nexthop: 10.100.2.3 RTs: 10:10 - Path not found"],
        },
    },
    (VerifyEVPNType5Routes, "failure-ipv6"): {
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.21",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.21:500 ip-prefix fd00:dc:5::1/128": {
                        "totalPaths": 1,
                        "routeKeyDetail": {"ipGenPrefix": "fd00:dc:5::1/128", "domain": "local", "rd": "10.1.0.21:500", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "",
                                "asPathEntry": {"asPathType": "Local", "asPath": "i"},
                                "reasonNotBestpath": "noReason",
                                "routeType": {"active": True, "valid": False},
                            }
                        ],
                    },
                    "RD: 10.1.0.21:500 ip-prefix fd00:dc:5::1/128 remote": {
                        "totalPaths": 1,
                        "routeKeyDetail": {"ipGenPrefix": "fd00:dc:5::1/128", "domain": "remote", "rd": "10.1.0.21:500", "nlriType": "ip-prefix"},
                        "evpnRoutePaths": [
                            {
                                "nextHop": "",
                                "asPathEntry": {"asPathType": "Local", "asPath": "i"},
                                "reasonNotBestpath": "noReason",
                                "routeType": {"active": False, "valid": True},
                            }
                        ],
                    },
                },
            }
        ],
        "inputs": {"prefixes": [{"address": "fd00:dc:5::1/128", "vni": 500}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Prefix: fd00:dc:5::1/128 VNI: 500 - No active and valid path found across all RDs"]},
    },
}
