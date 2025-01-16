# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.generic.py."""

from __future__ import annotations

import sys
from typing import Any

import pytest
from pydantic import ValidationError

from anta.tests.routing.generic import VerifyIPv4RouteType, VerifyRouteEntry, VerifyRoutingProtocolModel, VerifyRoutingTableEntry, VerifyRoutingTableSize
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyRoutingProtocolModel,
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "multi-agent"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-configured-model",
        "test": VerifyRoutingProtocolModel,
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": "ribd"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": "failure", "messages": ["routing model is misconfigured: configured: ribd - operating: ribd - expected: multi-agent"]},
    },
    {
        "name": "failure-mismatch-operating-model",
        "test": VerifyRoutingProtocolModel,
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "ribd"}}],
        "inputs": {"model": "multi-agent"},
        "expected": {"result": "failure", "messages": ["routing model is misconfigured: configured: multi-agent - operating: ribd - expected: multi-agent"]},
    },
    {
        "name": "success",
        "test": VerifyRoutingTableSize,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        # Output truncated
                        "maskLen": {"8": 2},
                        "totalRoutes": 123,
                    },
                },
            },
        ],
        "inputs": {"minimum": 42, "maximum": 666},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRoutingTableSize,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        # Output truncated
                        "maskLen": {"8": 2},
                        "totalRoutes": 1000,
                    },
                },
            },
        ],
        "inputs": {"minimum": 42, "maximum": 666},
        "expected": {"result": "failure", "messages": ["routing-table has 1000 routes and not between min (42) and maximum (666)"]},
    },
    {
        "name": "success",
        "test": VerifyRoutingTableEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                        },
                    },
                },
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-collect-all",
        "test": VerifyRoutingTableEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"], "collect": "all"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-missing-route",
        "test": VerifyRoutingTableEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {},
                    },
                },
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.2/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"]},
        "expected": {"result": "failure", "messages": ["The following route(s) are missing from the routing table of VRF default: ['10.1.0.1']"]},
    },
    {
        "name": "failure-wrong-route",
        "test": VerifyRoutingTableEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                        },
                    },
                },
            },
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.55/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"]},
        "expected": {"result": "failure", "messages": ["The following route(s) are missing from the routing table of VRF default: ['10.1.0.2']"]},
    },
    {
        "name": "failure-wrong-route-collect-all",
        "test": VerifyRoutingTableEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.1.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.4", "interface": "Ethernet1"}],
                            },
                            "10.1.0.55/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 20,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.1.255.6", "interface": "Ethernet2"}],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"], "collect": "all"},
        "expected": {"result": "failure", "messages": ["The following route(s) are missing from the routing table of VRF default: ['10.1.0.2']"]},
    },
    {
        "name": "success-valid-route-type",
        "test": VerifyIPv4RouteType,
        "eos_data": [
            {
                "vrfs": {
                    "default": {"routes": {"10.10.0.1/32": {"routeType": "eBGP"}, "10.100.0.12/31": {"routeType": "connected"}}},
                    "MGMT": {"routes": {"10.100.1.5/32": {"routeType": "iBGP"}}},
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/31", "route_type": "connected"},
                {"vrf": "MGMT", "prefix": "10.100.1.5/32", "route_type": "iBGP"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-route-not-found",
        "test": VerifyIPv4RouteType,
        "eos_data": [{"vrfs": {"default": {"routes": {}}}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"}]},
        "expected": {"result": "failure", "messages": ["Prefix: 10.10.0.1/32 VRF: default - Route not found"]},
    },
    {
        "name": "failure-invalid-route-type",
        "test": VerifyIPv4RouteType,
        "eos_data": [{"vrfs": {"default": {"routes": {"10.10.0.1/32": {"routeType": "eBGP"}}}}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "iBGP"}]},
        "expected": {
            "result": "failure",
            "messages": ["Prefix: 10.10.0.1/32 VRF: default - Incorrect route type - Expected: iBGP Actual: eBGP"],
        },
    },
    {
        "name": "failure-vrf-not-configured",
        "test": VerifyIPv4RouteType,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"routes_entries": [{"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"}]},
        "expected": {"result": "failure", "messages": ["Prefix: 10.10.0.1/32 VRF: default - VRF not configured"]},
    },
    {
        "name": "success",
        "test": VerifyRouteEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [
                                    {"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"},
                                    {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"},
                                    {"nexthopAddr": "10.100.0.101", "interface": "Ethernet4"},
                                ],
                            }
                        }
                    },
                }
            },
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-strict-true",
        "test": VerifyRouteEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                }
            },
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyRouteEntry,
        "eos_data": [
            {"vrfs": {"default": {"routes": {}}, "MGMT": {"routes": {}}}},
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Prefix: 10.10.0.1/32 VRF: default - prefix not found", "Prefix: 10.100.0.128/31 VRF: MGMT - prefix not found"],
        },
    },
    {
        "name": "failure-strict-failed",
        "test": VerifyRouteEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                }
            },
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.10.0.1/32 VRF: default - Exact nexthop not listed - Expected: 10.100.0.8, 10.100.0.10, 10.100.0.11 Actual: 10.100.0.8, 10.100.0.10",
                "Prefix: 10.100.0.128/31 VRF: MGMT - Exact nexthop not listed - Expected: 10.100.0.8, 10.100.0.10, 10.100.0.11 Actual: 10.100.0.8, 10.100.0.10",
            ],
        },
    },
    {
        "name": "failure",
        "test": VerifyRouteEntry,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routes": {
                            "10.10.0.1/32": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    },
                }
            },
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "nexthops": ["10.100.0.8", "10.100.0.10", "10.100.0.11"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Prefix: 10.10.0.1/32 VRF: default Nexthop: 10.100.0.11 - Route not found",
                "Prefix: 10.100.0.128/31 VRF: MGMT Nexthop: 10.100.0.11 - Route not found",
            ],
        },
    },
]


class TestVerifyRoutingTableSizeInputs:
    """Test anta.tests.routing.generic.VerifyRoutingTableSize.Input."""

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [
            pytest.param(0, 0, id="zero"),
            pytest.param(1, 2, id="1<2"),
            pytest.param(0, sys.maxsize, id="max"),
        ],
    )
    def test_valid(self, minimum: int, maximum: int) -> None:
        """Test VerifyRoutingTableSize valid inputs."""
        VerifyRoutingTableSize.Input(minimum=minimum, maximum=maximum)

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [
            pytest.param(-2, -1, id="negative"),
            pytest.param(2, 1, id="2<1"),
            pytest.param(sys.maxsize, 0, id="max"),
        ],
    )
    def test_invalid(self, minimum: int, maximum: int) -> None:
        """Test VerifyRoutingTableSize invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyRoutingTableSize.Input(minimum=minimum, maximum=maximum)
