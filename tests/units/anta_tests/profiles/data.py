# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.profiles"""

from typing import Any, Dict, List

INPUT_UFT_SETTING: List[Dict[str, Any]] = [
    {
        "name": "skipped",
        "eos_data": [{}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyUnifiedForwardingTableMode was not run as no mode was given"]
    },
    {
        "name": "success",
        "eos_data": [
            {
                "uftMode": "2",
                "urpfEnabled": False,
                "chipModel": "bcm56870",
                "l2TableSize": 163840,
                "l3TableSize": 147456,
                "lpmTableSize": 32768
            }
        ],
        "side_effect": "2",
        "expected": {"result": "success"},
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "uftMode": "2",
                "urpfEnabled": False,
                "chipModel": "bcm56870",
                "l2TableSize": 163840,
                "l3TableSize": 147456,
                "lpmTableSize": 32768
            }
        ],
        "side_effect": "3",
        "expected": {"result": "failure", "messages": ["Device is not running correct UFT mode (expected: 3 / running: 2)"]}
    },
]

INPUT_TCAM_PROFILE: List[Dict[str, Any]] = [
    {
        "name": "skipped",
        "eos_data": [{}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyTcamProfile was not run as no profile was given"]
    },
    {
        "name": "success",
        "eos_data": [
            {
                "pmfProfiles": {
                    "FixedSystem": {
                        "config": "test",
                        "configType": "System Profile",
                        "status": "test",
                        "mode": "tcam"
                    }
                },
                "lastProgrammingStatus": {}
            }
        ],
        "side_effect": "test",
        "expected": {"result": "success"},
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "pmfProfiles": {
                    "FixedSystem": {
                        "config": "test",
                        "configType": "System Profile",
                        "status": "default",
                        "mode": "tcam"
                    }
                },
                "lastProgrammingStatus": {}
            }
        ],
        "side_effect": "test",
        "expected": {"result": "failure", "messages": ["Incorrect profile running on device: default"]}
    },
]
