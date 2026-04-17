# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.multicast."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.multicast import VerifyIGMPSnoopingGlobal, VerifyIGMPSnoopingVlans
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyIGMPSnoopingVlans, "success-enabled"): {
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
        "inputs": {"vlans": {1: True, 42: True}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIGMPSnoopingVlans, "success-disabled"): {
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
        "inputs": {"vlans": {42: False}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIGMPSnoopingVlans, "failure-missing-vlan"): {
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
                    }
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": {1: False, 42: False}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VLAN1 - Incorrect IGMP state - Expected: disabled Actual: enabled", "Supplied vlan 42 is not present on the device"],
        },
    },
    (VerifyIGMPSnoopingVlans, "failure-wrong-state"): {
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
                    }
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            }
        ],
        "inputs": {"vlans": {1: True}},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN1 - Incorrect IGMP state - Expected: enabled Actual: disabled"]},
    },
    (VerifyIGMPSnoopingGlobal, "success-enabled"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "enabled", "robustness": 2, "immediateLeave": "enabled", "reportFloodingSwitchPorts": []}],
        "inputs": {"enabled": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIGMPSnoopingGlobal, "success-disabled"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "disabled"}],
        "inputs": {"enabled": False},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIGMPSnoopingGlobal, "failure-wrong-state"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "disabled"}],
        "inputs": {"enabled": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["IGMP state is not valid - Expected: enabled Actual: disabled"]},
    },
}
