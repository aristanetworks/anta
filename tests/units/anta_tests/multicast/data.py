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
        "side_effect": {"vlans": ["1", "42"], "configuration": "enabled"},
        "expected_result": "success",
        "expected_messages": [],
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
        "side_effect": {"vlans": ["42"], "configuration": "disabled"},
        "expected_result": "success",
        "expected_messages": [],
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
        "side_effect": {"vlans": ["1", "42"], "configuration": "disabled"},
        "expected_result": "failure",
        "expected_messages": ["IGMP state for vlan 1 is enabled", "Supplied vlan 42 is not present on the device."],
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
        "side_effect": {"vlans": ["1"], "configuration": "enabled"},
        "expected_result": "failure",
        "expected_messages": ["IGMP state for vlan 1 is disabled"],
    },
    {
        "name": "skipped-missing-vlans",
        "eos_data": [{}],
        "side_effect": {"vlans": None, "configuration": "disabled"},
        "expected_result": "skipped",
        "expected_messages": ["VerifyIGMPSnoopingVlans was not run as no vlans or configuration was given"],
    },
    {
        "name": "skipped-missing-confguration",
        "eos_data": [{}],
        "side_effect": {"vlans": ["1"], "configuration": None},
        "expected_result": "skipped",
        "expected_messages": ["VerifyIGMPSnoopingVlans was not run as no vlans or configuration was given"],
    },
    {
        "name": "error-wrong-confguration",
        "eos_data": [{}],
        "side_effect": {"vlans": ["1"], "configuration": "wrong"},
        "expected_result": "error",
        "expected_messages": ["VerifyIGMPSnoopingVlans was not run as 'configuration': wrong is not in the allowed values: ['enabled', 'disabled'])"],
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
        "side_effect": "enabled",
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-disabled",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            }
        ],
        "side_effect": "disabled",
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-wrong-state",
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            }
        ],
        "side_effect": "enabled",
        "expected_result": "failure",
        "expected_messages": ["IGMP state is not valid: disabled"],
    },
    {
        "name": "skipped-missing-confguration",
        "eos_data": [{}],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyIGMPSnoopingGlobal was not run as no configuration was given"],
    },
    {
        "name": "error-wrong-confguration",
        "eos_data": [{}],
        "side_effect": "wrong",
        "expected_result": "error",
        "expected_messages": ["VerifyIGMPSnoopingGlobal was not run as 'configuration': wrong is not in the allowed values: ['enabled', 'disabled'])"],
    },
]
