"""Test inputs for anta.tests.routing.generic"""

from typing import Any, Dict, List

INPUT_ROUTING_PROTOCOL_MODEL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "multi-agent"}}],
        "side_effect": "multi-agent",
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-wrong-configured-model",
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": "ribd"}}],
        "side_effect": "multi-agent",
        "expected_result": "failure",
        "expected_messages": ["routing model is misconfigured: configured: ribd - operating: ribd - expected: multi-agent"],
    },
    {
        "name": "failure-mismatch-operating-model",
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "ribd"}}],
        "side_effect": "multi-agent",
        "expected_result": "failure",
        "expected_messages": ["routing model is misconfigured: configured: multi-agent - operating: ribd - expected: multi-agent"],
    },
    {
        "name": "skipped",
        "eos_data": [{"vrfs": {"default": {}}, "protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "multi-agent"}}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyRoutingProtocolModel was not run as no model was given"],
    },
]

INPUT_ROUTING_TABLE_SIZE: List[Dict[str, Any]] = [
    {
        "name": "success",
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
        "side_effect": {"minimum": 42, "maximum": 666},
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": {"minimum": 42, "maximum": 666},
        "expected_result": "failure",
        "expected_messages": ["routing-table has 1000 routes and not between min (42) and maximum (666)"],
    },
    {
        "name": "error-max-smaller-than-min",
        "eos_data": [{}],
        "side_effect": {"minimum": 666, "maximum": 42},
        "expected_result": "error",
        "expected_messages": ["VerifyRoutingTableSize was not run as minimum 666 is greate than maximum 42."],
    },
    {
        "name": "skipped-minimum-None",
        "eos_data": [{}],
        "side_effect": {"minimum": None, "maximum": 42},
        "expected_result": "skipped",
        "expected_messages": ["VerifyRoutingTableSize was not run as either minimum None or maximum 42 was not provided"],
    },
    {
        "name": "error-maximum-string",
        "eos_data": [{}],
        "side_effect": {"minimum": 42, "maximum": "blah"},
        "expected_result": "error",
        "expected_messages": ["VerifyRoutingTableSize was not run as either minimum 42 or maximum blah is not a valid value (integer)"],
    },
]

INPUT_BFD: List[Dict[str, Any]] = [
    {
        "name": "success-no-peer",
        "eos_data": [{"vrfs": {}}],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-peers-up",
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
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["bfd state for peer '' is down (expected up)."],
    },
]
