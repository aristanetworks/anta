# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.mlag.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.tests.mlag import VerifyMlagConfigSanity, VerifyMlagDualPrimary, VerifyMlagInterfaces, VerifyMlagPrimaryPriority, VerifyMlagReloadDelay, VerifyMlagStatus
from tests.units.anta_tests import AntaUnitTest, test

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = type


AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
    (VerifyMlagStatus, "success"): {
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "up", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyMlagStatus, "skipped"): {"eos_data": [{"state": "disabled"}], "inputs": None, "expected": {"result": "skipped", "messages": ["MLAG is disabled"]}},
    (VerifyMlagStatus, "failure-negotiation-status"): {
        "eos_data": [{"state": "active", "negStatus": "connecting", "peerLinkStatus": "up", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MLAG negotiation status mismatch - Expected: connected Actual: connecting"]},
    },
    (VerifyMlagStatus, "failure-local-interface"): {
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "up", "localIntfStatus": "down"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Operational state of the MLAG local interface is not correct - Expected: up Actual: down"]},
    },
    (VerifyMlagStatus, "failure-peer-link"): {
        "eos_data": [{"state": "active", "negStatus": "connected", "peerLinkStatus": "down", "localIntfStatus": "up"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Operational state of the MLAG peer link is not correct - Expected: up Actual: down"]},
    },
    (VerifyMlagInterfaces, "success"): {
        "eos_data": [{"state": "active", "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 0, "Active-partial": 0, "Active-full": 1}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyMlagInterfaces, "skipped"): {"eos_data": [{"state": "disabled"}], "inputs": None, "expected": {"result": "skipped", "messages": ["MLAG is disabled"]}},
    (VerifyMlagInterfaces, "failure-active-partial"): {
        "eos_data": [{"state": "active", "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 0, "Active-partial": 1, "Active-full": 1}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MLAG status is not ok - Inactive Ports: 0 Partial Active Ports: 1"]},
    },
    (VerifyMlagInterfaces, "failure-inactive"): {
        "eos_data": [{"state": "active", "mlagPorts": {"Disabled": 0, "Configured": 0, "Inactive": 1, "Active-partial": 1, "Active-full": 1}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MLAG status is not ok - Inactive Ports: 1 Partial Active Ports: 1"]},
    },
    (VerifyMlagConfigSanity, "success"): {
        "eos_data": [{"globalConfiguration": {}, "interfaceConfiguration": {}, "mlagActive": True, "mlagConnected": True}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyMlagConfigSanity, "skipped"): {
        "eos_data": [{"mlagActive": False}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    (VerifyMlagConfigSanity, "failure-global"): {
        "eos_data": [
            {
                "globalConfiguration": {"mlag": {"globalParameters": {"dual-primary-detection-delay": {"localValue": "0", "peerValue": "200"}}}},
                "interfaceConfiguration": {},
                "mlagActive": True,
                "mlagConnected": True,
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MLAG config-sanity found in global configuration"]},
    },
    (VerifyMlagConfigSanity, "failure-interface"): {
        "eos_data": [
            {
                "globalConfiguration": {},
                "interfaceConfiguration": {"trunk-native-vlan mlag30": {"interface": {"Port-Channel30": {"localValue": "123", "peerValue": "3700"}}}},
                "mlagActive": True,
                "mlagConnected": True,
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["MLAG config-sanity found in interface configuration"]},
    },
    (VerifyMlagReloadDelay, "success"): {
        "eos_data": [{"state": "active", "reloadDelay": 300, "reloadDelayNonMlag": 330}],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {"result": "success"},
    },
    (VerifyMlagReloadDelay, "skipped-disabled"): {
        "eos_data": [{"state": "disabled"}],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    (VerifyMlagReloadDelay, "failure"): {
        "eos_data": [{"state": "active", "reloadDelay": 400, "reloadDelayNonMlag": 430}],
        "inputs": {"reload_delay": 300, "reload_delay_non_mlag": 330},
        "expected": {
            "result": "failure",
            "messages": ["MLAG reload-delay mismatch - Expected: 300s Actual: 400s", "Delay for non-MLAG ports mismatch - Expected: 330s Actual: 430s"],
        },
    },
    (VerifyMlagDualPrimary, "success"): {
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "none"},
            }
        ],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "success"},
    },
    (VerifyMlagDualPrimary, "skipped-disabled"): {
        "eos_data": [{"state": "disabled"}],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    (VerifyMlagDualPrimary, "failure-disabled"): {
        "eos_data": [{"state": "active", "dualPrimaryDetectionState": "disabled", "dualPrimaryPortsErrdisabled": False}],
        "inputs": {"detection_delay": 200, "errdisabled": False, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "failure", "messages": ["Dual-primary detection is disabled"]},
    },
    (VerifyMlagDualPrimary, "failure-wrong-timers"): {
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 160,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 300, "dualPrimaryAction": "none"},
            }
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
    (VerifyMlagDualPrimary, "failure-wrong-action"): {
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 0,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "none"},
            }
        ],
        "inputs": {"detection_delay": 200, "errdisabled": True, "recovery_delay": 60, "recovery_delay_non_mlag": 0},
        "expected": {"result": "failure", "messages": ["Dual-primary action mismatch - Expected: errdisableAllInterfaces Actual: none"]},
    },
    (VerifyMlagDualPrimary, "failure-wrong-non-mlag-delay"): {
        "eos_data": [
            {
                "state": "active",
                "dualPrimaryDetectionState": "configured",
                "dualPrimaryPortsErrdisabled": False,
                "dualPrimaryMlagRecoveryDelay": 60,
                "dualPrimaryNonMlagRecoveryDelay": 120,
                "detail": {"dualPrimaryDetectionDelay": 200, "dualPrimaryAction": "errdisableAllInterfaces"},
            }
        ],
        "inputs": {"detection_delay": 200, "errdisabled": True, "recovery_delay": 60, "recovery_delay_non_mlag": 60},
        "expected": {"result": "failure", "messages": ["Dual-primary non MLAG recovery delay mismatch - Expected: 60 Actual: 120"]},
    },
    (VerifyMlagPrimaryPriority, "success"): {
        "eos_data": [{"state": "active", "detail": {"mlagState": "primary", "primaryPriority": 32767}}],
        "inputs": {"primary_priority": 32767},
        "expected": {"result": "success"},
    },
    (VerifyMlagPrimaryPriority, "skipped-disabled"): {
        "eos_data": [{"state": "disabled"}],
        "inputs": {"primary_priority": 32767},
        "expected": {"result": "skipped", "messages": ["MLAG is disabled"]},
    },
    (VerifyMlagPrimaryPriority, "failure-not-primary"): {
        "eos_data": [{"state": "active", "detail": {"mlagState": "secondary", "primaryPriority": 32767}}],
        "inputs": {"primary_priority": 32767},
        "expected": {"result": "failure", "messages": ["The device is not set as MLAG primary"]},
    },
    (VerifyMlagPrimaryPriority, "failure-incorrect-priority"): {
        "eos_data": [{"state": "active", "detail": {"mlagState": "secondary", "primaryPriority": 32767}}],
        "inputs": {"primary_priority": 1},
        "expected": {"result": "failure", "messages": ["The device is not set as MLAG primary", "MLAG primary priority mismatch - Expected: 1 Actual: 32767"]},
    },
}
