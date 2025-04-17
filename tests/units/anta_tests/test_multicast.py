# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.multicast."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.multicast import VerifyIGMPSnoopingGlobal, VerifyIGMPSnoopingVlans
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
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
        "expected": {"result": "success"},
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
        "expected": {"result": "success"},
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
            "result": "failure",
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
        "expected": {"result": "failure", "messages": ["VLAN1 - Incorrect IGMP state - Expected: enabled Actual: disabled"]},
    },
    (VerifyIGMPSnoopingGlobal, "success-enabled"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "enabled", "robustness": 2, "immediateLeave": "enabled", "reportFloodingSwitchPorts": []}],
        "inputs": {"enabled": True},
        "expected": {"result": "success"},
    },
    (VerifyIGMPSnoopingGlobal, "success-disabled"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "disabled"}],
        "inputs": {"enabled": False},
        "expected": {"result": "success"},
    },
    (VerifyIGMPSnoopingGlobal, "failure-wrong-state"): {
        "eos_data": [{"reportFlooding": "disabled", "igmpSnoopingState": "disabled"}],
        "inputs": {"enabled": True},
        "expected": {"result": "failure", "messages": ["IGMP state is not valid - Expected: enabled Actual: disabled"]},
    },
}
