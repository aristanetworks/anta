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
        "expected_messages": ["MLAG status is not OK: {'state': 'active', 'negStatus': 'connected', 'localIntfStatus': 'up', 'peerLinkStatus': 'down'}"]
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
        "name": "failure-active-partial",
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
        "name": "failure-inactive",
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
        "expected_messages": ["Incorrect JSON response - 'mlagActive' state was not found"]
    },
    {
        "name": "failure-global",
        "eos_data": [
            {
                "globalConfiguration": {
                    "mlag": {
                        "globalParameters": {
                            "dual-primary-detection-delay": {
                                "localValue": "0",
                                "peerValue": "200"
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
        "expected_messages": ["MLAG config-sanity returned inconsistencies: "
                              "{'globalConfiguration': {'mlag': {'globalParameters': "
                              "{'dual-primary-detection-delay': {'localValue': '0', 'peerValue': '200'}}}}, "
                              "'interfaceConfiguration': {}}"]
    },
    {
        "name": "failure-interface",
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
        "expected_messages": ["MLAG config-sanity returned inconsistencies: "
                              "{'globalConfiguration': {}, "
                              "'interfaceConfiguration': {'trunk-native-vlan mlag30': "
                              "{'interface': {'Port-Channel30': {'localValue': '123', 'peerValue': '3700'}}}}}"]
    },
]

INPUT_MLAG_RELOAD_DELAY: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "state": "active",
                "reloadDelay": 300,
                "reloadDelayNonMlag": 330
            }
        ],
        "side_effect": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "skipped-disabled",
        "eos_data": [
            {
                "state": "disabled",
            }
        ],
        "side_effect": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected_result": "skipped",
        "expected_messages": ["MLAG is disabled"]
    },
    {
        "name": "skipped-no-params",
        "eos_data": [
            {
                "state": "disabled",
            }
        ],
        "side_effect": {"reload_delay": None, "reload_delay_non_mlag": None},
        "expected_result": "skipped",
        "expected_messages": ["VerifyMlagReloadDelay did not run because reload_delay or reload_delay_non_mlag were not supplied"]
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "state": "active",
                "reloadDelay": 400,
                "reloadDelayNonMlag": 430
            }
        ],
        "side_effect": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected_result": "failure",
        "expected_messages": ["The reload-delay parameters are not configured properly: {'reloadDelay': 400, 'reloadDelayNonMlag': 430}"]
    }
]

INPUT_MLAG_DUAL_PRIMARY: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {
                   "dualPrimaryDetectionDelay": 200,
                   "dualPrimaryAction": "none"
                }
            }
        ],
        "side_effect": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "skipped-disabled",
        "eos_data": [
            {
                "state": "disabled",
            }
        ],
        "side_effect": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "skipped",
        "expected_messages": ["MLAG is disabled"]
    },
    {
        "name": "skipped-no-params",
        "eos_data": [
            {
                "state": "disabled",
            }
        ],
        "side_effect": {"detection_delay": None, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "skipped",
        "expected_messages": ["VerifyMlagDualPrimary did not run because detection_delay, errdisabled, recovery_delay or recovery_delay_non_mlag were not supplied"]
    },
    {
        "name": "failure-disabled",
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "disabled",
                "dualPrimaryPortsErrdisabled": False,
            }
        ],
        "side_effect": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "failure",
        "expected_messages": ["Dual-primary detection is disabled"]
    },
    {
        "name": "failure-wrong-timers",
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 160,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {
                   "dualPrimaryDetectionDelay": 300,
                   "dualPrimaryAction": "none"
                }
            }
        ],
        "side_effect": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "failure",
        "expected_messages": [("The dual-primary parameters are not configured properly: "
                               "{'detail.dualPrimaryDetectionDelay': 300, "
                               "'detail.dualPrimaryAction': 'none', "
                               "'dualPrimaryMlagRecoveryDelay': 160, "
                               "'dualPrimaryNonMlagRecoveryDelay': 0}")]
    },
    {
        "name": "failure-wrong-action",
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {
                   "dualPrimaryDetectionDelay": 200,
                   "dualPrimaryAction": "none"
                }
            }
        ],
        "side_effect": {"detection_delay": 200, "errdisabled": True, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected_result": "failure",
        "expected_messages": [("The dual-primary parameters are not configured properly: "
                               "{'detail.dualPrimaryDetectionDelay': 200, "
                               "'detail.dualPrimaryAction': 'none', "
                               "'dualPrimaryMlagRecoveryDelay': 60, "
                               "'dualPrimaryNonMlagRecoveryDelay': 0}")]
    },
]
