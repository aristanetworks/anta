# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.generic.py."""

from __future__ import annotations

from typing import Any

from anta.tests.routing.generic import VerifyRouteEntry, VerifyRoutingProtocolModel, VerifyRoutingTableEntry, VerifyRoutingTableSize
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
        "name": "error-max-smaller-than-min",
        "test": VerifyRoutingTableSize,
        "eos_data": [{}],
        "inputs": {"minimum": 666, "maximum": 42},
        "expected": {
            "result": "error",
            "messages": ["Minimum 666 is greater than maximum 42"],
        },
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
        "name": "collect-input-error",
        "test": VerifyRoutingTableEntry,
        "eos_data": {},
        "inputs": {"vrf": "default", "routes": ["10.1.0.1", "10.1.0.2"], "collect": "not-valid"},
        "expected": {"result": "error", "messages": ["Inputs are not valid"]},
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
                    }
                }
            },
            {
                "vrfs": {
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    }
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
            {"vrfs": {"default": {"routes": {}}}},
            {"vrfs": {"MGMT": {"routes": {}}}},
        ],
        "inputs": {
            "route_entries": [
                {"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
                {"prefix": "10.100.0.128/31", "vrf": "MGMT", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following route entry(s) or nexthop path(s) not found or not correct:\n"
                "{'10.10.0.1/32': {'default': 'Not configured'}, '10.100.0.128/31': {'MGMT': 'Not configured'}}"
            ],
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
                    }
                }
            },
            {
                "vrfs": {
                    "MGMT": {
                        "routes": {
                            "10.100.0.128/31": {
                                "vias": [{"nexthopAddr": "10.100.0.8", "interface": "Ethernet1"}, {"nexthopAddr": "10.100.0.10", "interface": "Ethernet2"}],
                            }
                        }
                    }
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
                "Following route entry(s) or nexthop path(s) not found or not correct:\n"
                "{'10.10.0.1/32': {'default': 'Expected only `10.100.0.8, 10.100.0.10, 10.100.0.11` nexthops should be listed but "
                "found `10.100.0.8, 10.100.0.10` instead.'}, '10.100.0.128/31': {'MGMT': 'Expected only `10.100.0.8, 10.100.0.10, "
                "10.100.0.11` nexthops should be listed but found `10.100.0.8, 10.100.0.10` instead.'}}"
            ],
        },
    },
]
