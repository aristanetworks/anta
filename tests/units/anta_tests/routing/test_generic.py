# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.generic.py."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.tests.routing.generic import VerifyRoutingProtocolModel, VerifyRoutingTableEntry, VerifyRoutingTableSize
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
]


class TestVerifyRoutingTableSize:  # pylint: disable=too-few-public-methods
    """Test VerifyRoutingTableSize."""

    def test_inputs(self) -> None:
        """Test VerifyRoutingTableSize inputs."""
        VerifyRoutingTableSize.Input(minimum=1, maximum=2)
        with pytest.raises(ValidationError):
            VerifyRoutingTableSize.Input(minimum=2, maximum=1)
