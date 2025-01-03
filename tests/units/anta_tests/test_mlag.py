# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.mlag.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.mlag import VerifyMlagConfigSanity, VerifyMlagDualPrimary, VerifyMlagInterfaces, VerifyMlagPrimaryPriority, VerifyMlagReloadDelay, VerifyMlagStatus
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
    {
        "name": "success",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "up", "localIntfStatus": "up"}],
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
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    {
        "name": "failure",
        "test": VerifyMlagStatus,
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "down", "localIntfStatus": "up"}],
        "expected": {
            "result": "failure",
            "messages": ["MLAG status is not OK: {'state': 'active', 'negStatus': 'connected', 'localIntfStatus': 'up', 'peerLinkStatus': 'down'}"],
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
        "expected": {
            "result": "failure",
            "messages": ["MLAG status is not OK: {'Disabled': 0, 'Configured': 0, 'Inactive': 0, 'Active-partial': 1, 'Active-full': 1}"],
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
        "expected": {
            "result": "failure",
            "messages": ["MLAG status is not OK: {'Disabled': 0, 'Configured': 0, 'Inactive': 1, 'Active-partial': 1, 'Active-full': 1}"],
        },
    },
    {
        "name": "success",
        "test": VerifyMlagConfigSanity,
        "eos_data": [{"globalConfiguration": {}, "interfaceConfiguration": {}, "mlagActive": True, "mlagConnected": True}],
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
        "expected": {
            "result": "failure",
            "messages": [
                "MLAG config-sanity returned inconsistencies: "
                "{'globalConfiguration': {'mlag': {'globalParameters': "
                "{'dual-primary-detection-delay': {'localValue': '0', 'peerValue': '200'}}}}, "
                "'interfaceConfiguration': {}}",
            ],
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
        "expected": {
            "result": "failure",
            "messages": [
                "MLAG config-sanity returned inconsistencies: "
                "{'globalConfiguration': {}, "
                "'interfaceConfiguration': {'trunk-native-vlan mlag30': "
                "{'interface': {'Port-Channel30': {'localValue': '123', 'peerValue': '3700'}}}}}",
            ],
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
        "expected": {"result": "failure", "messages": ["The reload-delay parameters are not configured properly: {'reloadDelay': 400, 'reloadDelayNonMlag': 430}"]},
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
                (
                    "The dual-primary parameters are not configured properly: "
                    "{'detail.dualPrimaryDetectionDelay': 300, "
                    "'detail.dualPrimaryAction': 'none', "
                    "'dualPrimaryMlagRecoveryDelay': 160, "
                    "'dualPrimaryNonMlagRecoveryDelay': 0}"
                ),
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
            "messages": [
                (
                    "The dual-primary parameters are not configured properly: "
                    "{'detail.dualPrimaryDetectionDelay': 200, "
                    "'detail.dualPrimaryAction': 'none', "
                    "'dualPrimaryMlagRecoveryDelay': 60, "
                    "'dualPrimaryNonMlagRecoveryDelay': 0}"
                ),
            ],
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
            "messages": ["The device is not set as MLAG primary.", "The primary priority does not match expected. Expected `1`, but found `32767` instead."],
        },
    },
]
