# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.multicast."""

from __future__ import annotations

from typing import Any

from anta.tests.multicast import VerifyIGMPSnoopingGlobal, VerifyIGMPSnoopingVlans
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success-enabled",
        "test": VerifyIGMPSnoopingVlans,
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
            },
        ],
        "inputs": {"vlans": {1: True, 42: True}},
        "expected": {"result": "success"},
    },
    {
        "name": "success-disabled",
        "test": VerifyIGMPSnoopingVlans,
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
                    },
                },
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            },
        ],
        "inputs": {"vlans": {42: False}},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-missing-vlan",
        "test": VerifyIGMPSnoopingVlans,
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
            },
        ],
        "inputs": {"vlans": {1: False, 42: False}},
        "expected": {"result": "failure", "messages": ["IGMP state for vlan 1 is enabled", "Supplied vlan 42 is not present on the device."]},
    },
    {
        "name": "failure-wrong-state",
        "test": VerifyIGMPSnoopingVlans,
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
            },
        ],
        "inputs": {"vlans": {1: True}},
        "expected": {"result": "failure", "messages": ["IGMP state for vlan 1 is disabled"]},
    },
    {
        "name": "success-enabled",
        "test": VerifyIGMPSnoopingGlobal,
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "enabled",
                "robustness": 2,
                "immediateLeave": "enabled",
                "reportFloodingSwitchPorts": [],
            },
        ],
        "inputs": {"enabled": True},
        "expected": {"result": "success"},
    },
    {
        "name": "success-disabled",
        "test": VerifyIGMPSnoopingGlobal,
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            },
        ],
        "inputs": {"enabled": False},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-state",
        "test": VerifyIGMPSnoopingGlobal,
        "eos_data": [
            {
                "reportFlooding": "disabled",
                "igmpSnoopingState": "disabled",
            },
        ],
        "inputs": {"enabled": True},
        "expected": {"result": "failure", "messages": ["IGMP state is not valid: disabled"]},
    },
]
