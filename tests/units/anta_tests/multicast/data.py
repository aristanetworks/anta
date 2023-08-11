# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.multicast"""

from typing import Any, Dict, List

INPUT_IGMP_SNOOPING_VLANS: List[Dict[str, Any]] = [
    {
        "name": "success-enabled",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "vlans": {
                    "1": {
                        "reportFlooding": "disabled",
                        "proxyActive": False,
                        "groupsOverrun": False,
                        "multicastRouterLearningMode": "pim-dvmrp",
                        "igmpSnoopingState": "enabled",
                        "pruningActive": False,
                        "maxGroups": 65534,
                        "immediateLeave": "default",
                        "floodingTraffic": True,
                    },
                    "42": {
                        "reportFlooding": "disabled",
                        "proxyActive": False,
                        "groupsOverrun": False,
                        "multicastRouterLearningMode": "pim-dvmrp",
                        "igmpSnoopingState": "enabled",
                        "pruningActive": False,
                        "maxGroups": 65534,
                        "immediateLeave": "default",
                        "floodingTraffic": True,
                    },
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": ["1", "42"], "configuration": "enabled"},
        "expected": {"result": "success"},
            },
    {
        "name": "success-disabled",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "vlans": {
                    "42": {
                        "reportFlooding": "disabled",
                        "proxyActive": False,
                        "groupsOverrun": False,
                        "multicastRouterLearningMode": "pim-dvmrp",
                        "igmpSnoopingState": "disabled",
                        "pruningActive": False,
                        "maxGroups": 65534,
                        "immediateLeave": "default",
                        "floodingTraffic": True,
                    }
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": ["42"], "configuration": "disabled"},
        "expected": {"result": "success"},
            },
    {
        "name": "failure-missing-vlan",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "vlans": {
                    "1": {
                        "reportFlooding": "disabled",
                        "proxyActive": False,
                        "groupsOverrun": False,
                        "multicastRouterLearningMode": "pim-dvmrp",
                        "igmpSnoopingState": "enabled",
                        "pruningActive": False,
                        "maxGroups": 65534,
                        "immediateLeave": "default",
                        "floodingTraffic": True,
                    },
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": ["1", "42"], "configuration": "disabled"},
        "expected": {"result": "failure", "messages": ["IGMP state for vlan 1 is enabled", "Supplied vlan 42 is not present on the device."]},
    },
    {
        "name": "failure-wrong-state",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "vlans": {
                    "1": {
                        "reportFlooding": "disabled",
                        "proxyActive": False,
                        "groupsOverrun": False,
                        "multicastRouterLearningMode": "pim-dvmrp",
                        "igmpSnoopingState": "disabled",
                        "pruningActive": False,
                        "maxGroups": 65534,
                        "immediateLeave": "default",
                        "floodingTraffic": True,
                    },
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": ["1"], "configuration": "enabled"},
        "expected": {"result": "failure", "messages": ["IGMP state for vlan 1 is disabled"]},
    },
    {
        "name": "skipped-missing-vlans",
        "eos_data": [{}],
        "inputs": {"vlans": None, "configuration": "disabled"},
        "expected": {"result":"skipped"}, "messages": ["VerifyIGMPSnoopingVlans was not run as no vlans or configuration was given"],
    },
    {
        "name": "skipped-missing-confguration",
        "eos_data": [{}],
        "inputs": {"vlans": ["1"], "configuration": None},
        "expected": {"result":"skipped"}, "messages": ["VerifyIGMPSnoopingVlans was not run as no vlans or configuration was given"],
    },
    {
        "name": "error-wrong-confguration",
        "eos_data": [{}],
        "inputs": {"vlans": ["1"], "configuration": "wrong"},
        "expected": {"result": "error"}, "messages": ["VerifyIGMPSnoopingVlans was not run as 'configuration': wrong is not in the allowed values: ['enabled', 'disabled'])"],
    },
]

INPUT_IGMP_SNOOPING_GLOBAL: List[Dict[str, Any]] = [
    {
        "name": "success-enabled",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": "enabled",
        "expected": {"result": "success"},
            },
    {
        "name": "success-disabled",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            }
        ],
        "inputs": "disabled",
        "expected": {"result": "success"},
            },
    {
        "name": "failure-wrong-state",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            }
        ],
        "inputs": "enabled",
        "expected": {"result": "failure", "messages": ["IGMP state is not valid: disabled"]},
    },
    {
        "name": "skipped-missing-confguration",
        "eos_data": [{}],
        "inputs": None,
        "expected": {"result":"skipped"}, "messages": ["VerifyIGMPSnoopingGlobal was not run as no configuration was given"],
    },
    {
        "name": "error-wrong-confguration",
        "eos_data": [{}],
        "inputs": "wrong",
        "expected": {"result": "error"}, "messages": ["VerifyIGMPSnoopingGlobal was not run as 'configuration': wrong is not in the allowed values: ['enabled', 'disabled'])"],
    },
]
