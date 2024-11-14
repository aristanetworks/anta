# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.generic.py."""

from __future__ import annotations

import sys
from typing import Any

import pytest
from pydantic import ValidationError

from anta.tests.routing.generic import VerifyRouteType, VerifyRoutingProtocolModel, VerifyRoutingTableEntry, VerifyRoutingTableSize
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
        "name": "Failure-route-not-found",
        "test": VerifyRouteType,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.10.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.0.12/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet1"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.14/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet2"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.128/31": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.1.5/32": {
                                "hardwareProgrammed": True,
                                "routeType": "iBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.4.4", "interface": "Vlan4093"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/32", "route_type": "connected"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For following routes, VRF is not configured or Route types are invalid:\n{'routes_entries': {"
                "'10.100.0.12/32': {'default': 'Routes not found.'}}}"
            ],
        },
    },
    {
        "name": "Success-valid-route-type",
        "test": VerifyRouteType,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.10.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.0.12/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet1"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.14/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet2"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.128/31": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.1.5/32": {
                                "hardwareProgrammed": True,
                                "routeType": "iBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.4.4", "interface": "Vlan4093"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.14/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.128/31", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.1.5/32", "route_type": "iBGP"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "Failure-invalid-route-type",
        "test": VerifyRouteType,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.10.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.0.12/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet1"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.14/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet2"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.128/31": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.1.5/32": {
                                "hardwareProgrammed": True,
                                "routeType": "iBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.4.4", "interface": "Vlan4093"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "iBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.14/31", "route_type": "static"},
                {"vrf": "default", "prefix": "10.100.0.128/31", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.1.5/32", "route_type": "eBGP"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For following routes, VRF is not configured or Route types are invalid:\n{'routes_entries': {'10.10.0.1/32': {'default': {'route_type': \"Expected route type is 'iBGP' however in actual it is found as 'eBGP'\"}}, '10.100.0.14/31': {'default': {'route_type': \"Expected route type is 'static' however in actual it is found as 'connected'\"}}, '10.100.1.5/32': {'default': {'route_type': \"Expected route type is 'eBGP' however in actual it is found as 'iBGP'\"}}}}"
            ],
        },
    },
    {
        "name": "Failure-vrf-not-configured",
        "test": VerifyRouteType,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "10.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.0.12/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.14/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.128/31", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.1.5/32", "route_type": "iBGP"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For following routes, VRF is not configured or Route types are invalid:\n{'routes_entries': {'10.10.0.1/32': {'default': 'Not configured'}, '10.100.0.12/31': {'default': 'Not configured'}, '10.100.0.14/31': {'default': 'Not configured'}, '10.100.0.128/31': {'default': 'Not configured'}, '10.100.1.5/32': {'default': 'Not configured'}}}"
            ],
        },
    },
    {
        "name": "Failure-invalid-network-address",
        "test": VerifyRouteType,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routingDisabled": False,
                        "allRoutesProgrammedHardware": True,
                        "allRoutesProgrammedKernel": True,
                        "defaultRouteState": "notSet",
                        "routes": {
                            "10.10.0.1/32": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.0.12/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet1"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.14/31": {
                                "hardwareProgrammed": True,
                                "routeType": "connected",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "vias": [{"interface": "Ethernet2"}],
                                "directlyConnected": True,
                            },
                            "10.100.0.128/31": {
                                "hardwareProgrammed": True,
                                "routeType": "eBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.0.12", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.14", "interface": "Ethernet2"}],
                                "directlyConnected": False,
                            },
                            "10.100.1.5/32": {
                                "hardwareProgrammed": True,
                                "routeType": "iBGP",
                                "routeLeaked": False,
                                "kernelProgrammed": True,
                                "routeAction": "forward",
                                "directlyConnected": False,
                                "preference": 200,
                                "metric": 0,
                                "vias": [{"nexthopAddr": "10.100.4.4", "interface": "Vlan4093"}],
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {
            "routes_entries": [
                {"vrf": "default", "prefix": "1022.10.0.1/32", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "2001:db8:3333:4444:5555:6666:7777:8888:", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.14/31", "route_type": "connected"},
                {"vrf": "default", "prefix": "10.100.0.128/31", "route_type": "eBGP"},
                {"vrf": "default", "prefix": "10.100.1.5/32", "route_type": "iBGP"},
            ]
        },
        "expected": {"result": "error", "messages": ["Input is not a valid IPv4 network"]},
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
