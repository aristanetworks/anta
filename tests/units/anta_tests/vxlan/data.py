"""Test inputs for anta.tests.vxlan"""

from typing import Any, Dict, List

INPUT_VXLAN_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Loopback0": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Vxlan1 interface is not configured"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "up"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is down/up"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "up",
                        "interfaceStatus": "down"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is up/down"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaceDescriptions": {
                    "Vxlan1": {
                        "lineProtocolStatus": "down",
                        "interfaceStatus": "down"
                    }
                }
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Vxlan1 interface is down/down"]
    },
]
