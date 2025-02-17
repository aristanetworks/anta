# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.mlag.py."""

from __future__ import annotations

from typing import Any

from anta.tests.mlag import VerifyMlagConfigSanity, VerifyMlagDualPrimary, VerifyMlagInterfaces, VerifyMlagPrimaryPriority, VerifyMlagReloadDelay, VerifyMlagStatus
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "up", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "skipped",
        "test": VerifyMlagStatus,
        "eos_data": [
            {
                "state": "disabled",
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure-negotian-status",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connecting", "peerLinkStatus": "up", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["MLAG Negotiation status mismatch - Expected: connected Actual: connecting"],
        },
    },
    {
        "name": "failure-local-interface",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "up", "localIntfStatus": "down"}],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Operational state of the MLAG local interface is not correct - Expected: up Actual: down"],
        },
    },
    {
        "name": "failure-peer-link",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "down", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Operational state of the MLAG peer link is not correct - Expected: up Actual: down"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagInterfaces,
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 0, "Active-partial": 0, "Active-full": 1},
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "skipped",
        "test": VerifyMlagInterfaces,
        "eos_data": [
            {
                "state": "disabled",
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure-active-partial",
        "test": VerifyMlagInterfaces,
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 0, "Active-partial": 1, "Active-full": 1},
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["MLAG status is not ok - Inactive Ports: 0 Partial Active Ports: 1"],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifyMlagInterfaces,
        "eos_data": [
            {
                "state": "active",
                "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 1, "Active-partial": 1, "Active-full": 1},
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["MLAG status is not ok - Inactive Ports: 1 Partial Active Ports: 1"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagConfigSanity,
        "eos_data": [{"globalConfiguration": {}, "interfaceConfiguration": {}, "mlagActive": True, "mlagConnected": True}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "skipped",
        "test": VerifyMlagConfigSanity,
        "eos_data": [
            {
                "mlagActive": False,
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure-global",
        "test": VerifyMlagConfigSanity,
        "eos_data": [
            {
                "globalConfiguration": {"mlag": {"globalParameters": {"dual-primary-detection-delay": {"localValue": "0", "peerValue": "200"}}}},
                "interfaceConfiguration": {},
                "mlagActive": True,
                "mlagConnected": True,
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["MLAG config-sanity found in global configuration"],
        },
    },
    {
        "name": "failure-interface",
        "test": VerifyMlagConfigSanity,
        "eos_data": [
            {
                "globalConfiguration": {},
                "interfaceConfiguration": {"trunk-native-vlan mlag30": {"interface": {"Port-Channel30": {"localValue": "123", "peerValue": "3700"}}}},
                "mlagActive": True,
                "mlagConnected": True,
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["MLAG config-sanity found in interface configuration"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagReloadDelay,
        "eos_data": [{"state": "active", "reloadDelay": 300, "reloadDelayNonMlag": 330}],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {"result": "success"},
    },
    {
        "name": "skipped-disabled",
        "test": VerifyMlagReloadDelay,
        "eos_data": [
            {
                "state": "disabled",
            },
        ],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure",
        "test": VerifyMlagReloadDelay,
        "eos_data": [{"state": "active", "reloadDelay": 400, "reloadDelayNonMlag": 430}],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {
            "result": "failure",
            "messages": ["MLAG reload delay mismatch - Expected: 300s Actual: 400s", "Delay for non MLAG ports mismatch - Expected: 330s Actual: 430s"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "none"},
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "success"},
    },
    {
        "name": "skipped-disabled",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "disabled",
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure-disabled",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "disabled",
                "dualPrimaryPortsErrdisabled": False,
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "failure", "messages": ["Dual-primary detection is disabled"]},
    },
    {
        "name": "failure-wrong-timers",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 160,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 300, "dualPrimaryAction": "none"},
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {
            "result": "failure",
            "messages": [
                "Dual-primary detection delay mismatch - Expected: 200 Actual: 300",
                "Dual-primary MLAG recovery delay mismatch - Expected: 60 Actual: 160",
            ],
        },
    },
    {
        "name": "failure-wrong-action",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "none"},
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": True, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {
            "result": "failure",
            "messages": ["Dual-primary action mismatch - Expected: errdisableAllInterfaces Actual: none"],
        },
    },
    {
        "name": "failure-wrong-non-mlag-delay",
        "test": VerifyMlagDualPrimary,
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 120,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "errdisableAllInterfaces"},
            },
        ],
        "inputs": {"detection_delay": 200, "errdisabled": True, "recovery_delay": 60, "recovery_delay_non_mlag": 60},
        "expected": {
            "result": "failure",
            "messages": ["Dual-primary non MLAG recovery delay mismatch - Expected: 60 Actual: 120"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagPrimaryPriority,
        "eos_data": [
            {
                "state": "active",
                "detail": {"mlagState": "primary", "primaryPriority": 32767},
            }
        ],
        "inputs": {
            "primary_priority": 32767,
        },
        "expected": {"result": "success"},
    },
    {
        "name": "skipped-disabled",
        "test": VerifyMlagPrimaryPriority,
        "eos_data": [
            {
                "state": "disabled",
            }
        ],
        "inputs": {"primary_priority": 32767},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure-not-primary",
        "test": VerifyMlagPrimaryPriority,
        "eos_data": [
            {
                "state": "active",
                "detail": {"mlagState": "secondary", "primaryPriority": 32767},
            }
        ],
        "inputs": {"primary_priority": 32767},
        "expected": {
            "result": "failure",
            "messages": ["The device is not set as MLAG primary."],
        },
    },
    {
        "name": "failure-incorrect-priority",
        "test": VerifyMlagPrimaryPriority,
        "eos_data": [
            {
                "state": "active",
                "detail": {"mlagState": "secondary", "primaryPriority": 32767},
            }
        ],
        "inputs": {"primary_priority": 1},
        "expected": {
            "result": "failure",
            "messages": ["The device is not set as MLAG primary.", "The primary priority mismatch - Expected: 1 Actual: 32767"],
        },
    },
]
