# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.generic.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.routing.generic import VerifyBFD, VerifyRoutingProtocolModel, VerifyRoutingTableSize
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

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
                    }
                },
            }
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
                    }
                },
            }
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
        "name": "success-no-peer",
        "test": VerifyBFD,
        "eos_data": [{"vrfs": {}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-peers-up",
        "test": VerifyBFD,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv6Neighbors": {},
                        "ipv4Neighbors": {
                            "7.7.7.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "authType": "None",
                                        "kernelIfIndex": 0,
                                        "lastDiag": "diagNone",
                                        "authProfileName": "",
                                        "lastUp": 1683288421.669188,
                                        "remoteDisc": 345332116,
                                        "sessType": "sessionTypeMultihop",
                                        "localDisc": 1654273918,
                                        "lastDown": 0.0,
                                        "l3intf": "",
                                        "tunnelId": 0,
                                    }
                                }
                            },
                            "10.3.0.1": {
                                "peerStats": {
                                    "Ethernet1": {
                                        "status": "up",
                                        "authType": "None",
                                        "kernelIfIndex": 11,
                                        "lastDiag": "diagNone",
                                        "authProfileName": "",
                                        "lastUp": 1683288900.004889,
                                        "remoteDisc": 1017672851,
                                        "sessType": "sessionTypeNormal",
                                        "localDisc": 4269977256,
                                        "lastDown": 0.0,
                                        "l3intf": "Ethernet1",
                                        "tunnelId": 0,
                                    }
                                }
                            },
                        },
                        "ipv4ReflectorNeighbors": {},
                        "ipv6ReflectorNeighbors": {},
                        "ipv6InitiatorNeighbors": {},
                        "ipv4InitiatorNeighbors": {},
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBFD,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv6Neighbors": {},
                        "ipv4Neighbors": {
                            "7.7.7.7": {
                                "peerStats": {
                                    "": {
                                        "status": "down",
                                        "authType": "None",
                                        "kernelIfIndex": 0,
                                        "lastDiag": "diagNone",
                                        "authProfileName": "",
                                        "lastUp": 1683288421.669188,
                                        "remoteDisc": 345332116,
                                        "sessType": "sessionTypeMultihop",
                                        "localDisc": 1654273918,
                                        "lastDown": 0.0,
                                        "l3intf": "",
                                        "tunnelId": 0,
                                    }
                                }
                            },
                            "10.3.0.1": {
                                "peerStats": {
                                    "Ethernet1": {
                                        "status": "up",
                                        "authType": "None",
                                        "kernelIfIndex": 11,
                                        "lastDiag": "diagNone",
                                        "authProfileName": "",
                                        "lastUp": 1683288900.004889,
                                        "remoteDisc": 1017672851,
                                        "sessType": "sessionTypeNormal",
                                        "localDisc": 4269977256,
                                        "lastDown": 0.0,
                                        "l3intf": "Ethernet1",
                                        "tunnelId": 0,
                                    }
                                }
                            },
                        },
                        "ipv4ReflectorNeighbors": {},
                        "ipv6ReflectorNeighbors": {},
                        "ipv6InitiatorNeighbors": {},
                        "ipv4InitiatorNeighbors": {},
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["bfd state for peer '' is down (expected up)."]},
    },
]
