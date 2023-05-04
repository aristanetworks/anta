"""Test inputs for anta.tests.mlag"""

from typing import Any, Dict, List

INPUT_MLAG_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "state": "active",
                "negStatus": "connected",
                "peerLinkStatus": "up",
                "localIntfStatus": "up"
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
                "state": "disabled",
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["MLAG is disabled"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "state": "active",
                "negStatus": "connected",
                "peerLinkStatus": "down",
                "localIntfStatus": "up"
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["MLAG status is not OK: {'state': 'active', 'negStatus': 'connected', 'peerLinkStatus': 'down', 'localIntfStatus': 'up'}"]
    },
]

INPUT_MLAG_INTERFACES: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {
                    "Disabled": 0,
                    "Configured": 0,
                    "Inactive": 0,
                    "Active-partial": 0,
                    "Active-full": 1
                },
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
                "state": "disabled",
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["MLAG is disabled"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {
                    "Disabled": 0,
                    "Configured": 0,
                    "Inactive": 0,
                    "Active-partial": 1,
                    "Active-full": 1
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["MLAG status is not OK: {'Disabled': 0, 'Configured': 0, 'Inactive': 0, 'Active-partial': 1, 'Active-full': 1}"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {
                    "Disabled": 0,
                    "Configured": 0,
                    "Inactive": 1,
                    "Active-partial": 1,
                    "Active-full": 1
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["MLAG status is not OK: {'Disabled': 0, 'Configured': 0, 'Inactive': 1, 'Active-partial': 1, 'Active-full': 1}"]
    },
]

INPUT_MLAG_CONFIG_SANITY: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "globalConfiguration": {},
                "interfaceConfiguration": {},
                "mlagActive": True,
                "mlagConnected": True
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
                "mlagActive": False,
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["MLAG is disabled"]
    },
    {
        "name": "error",
        "eos_data": [
            {
                "dummy": False,
            }
        ],
        "side_effect": [],
        "expected_result": "error",
        "expected_messages": ["Incorrect JSON response - mlagActive state not found"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "globalConfiguration": {
                    "bridging": {
                        "globalParameters": {
                            "admin-state vlan 33": {
                                "localValue": "active"
                            },
                            "mac-learning vlan 33": {
                                "localValue": "True"
                            }
                        }
                    }
                },
                "interfaceConfiguration": {},
                "mlagActive": True,
                "mlagConnected": True
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["MLAG config-sanity returned Global inconsistancies: {'bridging': {'globalParameters': {'admin-state vlan 33': {'localValue': 'active'}, 'mac-learning vlan 33': {'localValue': 'True'}}}}"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "globalConfiguration": {},
                "interfaceConfiguration": {
                    "trunk-native-vlan mlag30": {
                        "interface": {
                            "Port-Channel30": {
                                "localValue": "123",
                                "peerValue": "3700"
                            }
                        }
                    }
                },
                "mlagActive": True,
                "mlagConnected": True
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["MLAG config-sanity returned Interface inconsistancies: {'trunk-native-vlan mlag30': {'interface': {'Port-Channel30': {'localValue': '123', 'peerValue': '3700'}}}}"]
    },
]
