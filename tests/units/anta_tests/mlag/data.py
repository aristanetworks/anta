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
