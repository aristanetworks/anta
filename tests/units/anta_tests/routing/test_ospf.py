# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.ospf.py."""

from __future__ import annotations

from typing import Any

from anta.tests.routing.ospf import VerifyOSPFMaxLSA, VerifyOSPFNeighborCount, VerifyOSPFNeighborState
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyOSPFNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "666": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "7.7.7.7",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                    {
                                        "routerId": "9.9.9.9",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                    "BLAH": {
                        "instList": {
                            "777": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "8.8.8.8",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyOSPFNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "666": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "7.7.7.7",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "2-way",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                    {
                                        "routerId": "9.9.9.9",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                    "BLAH": {
                        "instList": {
                            "777": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "8.8.8.8",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "down",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
                " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}].",
            ],
        },
    },
    {
        "name": "skipped",
        "test": VerifyOSPFNeighborState,
        "eos_data": [
            {
                "vrfs": {},
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["no OSPF neighbor found"]},
    },
    {
        "name": "success",
        "test": VerifyOSPFNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "666": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "7.7.7.7",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                    {
                                        "routerId": "9.9.9.9",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                    "BLAH": {
                        "instList": {
                            "777": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "8.8.8.8",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"number": 3},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifyOSPFNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "666": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "7.7.7.7",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"number": 3},
        "expected": {"result": "failure", "messages": ["device has 1 neighbors (expected 3)"]},
    },
    {
        "name": "failure-good-number-wrong-state",
        "test": VerifyOSPFNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "666": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "7.7.7.7",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "2-way",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                    {
                                        "routerId": "9.9.9.9",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "full",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                    "BLAH": {
                        "instList": {
                            "777": {
                                "ospfNeighborEntries": [
                                    {
                                        "routerId": "8.8.8.8",
                                        "priority": 1,
                                        "drState": "DR",
                                        "interfaceName": "Ethernet1",
                                        "adjacencyState": "down",
                                        "inactivity": 1683298014.844345,
                                        "interfaceAddress": "10.3.0.1",
                                    },
                                ],
                            },
                        },
                    },
                },
            },
        ],
        "inputs": {"number": 3},
        "expected": {
            "result": "failure",
            "messages": [
                "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
                " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}].",
            ],
        },
    },
    {
        "name": "skipped",
        "test": VerifyOSPFNeighborCount,
        "eos_data": [
            {
                "vrfs": {},
            },
        ],
        "inputs": {"number": 3},
        "expected": {"result": "skipped", "messages": ["no OSPF neighbor found"]},
    },
    {
        "name": "success",
        "test": VerifyOSPFMaxLSA,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "1": {
                                "instanceId": 1,
                                "maxLsaInformation": {
                                    "maxLsa": 12000,
                                    "maxLsaThreshold": 75,
                                },
                                "routerId": "1.1.1.1",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 9,
                                },
                            },
                        },
                    },
                    "TEST": {
                        "instList": {
                            "10": {
                                "instanceId": 10,
                                "maxLsaInformation": {
                                    "maxLsa": 1000,
                                    "maxLsaThreshold": 75,
                                },
                                "routerId": "20.20.20.20",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 5,
                                },
                            },
                        },
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyOSPFMaxLSA,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "1": {
                                "instanceId": 1,
                                "maxLsaInformation": {
                                    "maxLsa": 12000,
                                    "maxLsaThreshold": 75,
                                },
                                "routerId": "1.1.1.1",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 11500,
                                },
                            },
                        },
                    },
                    "TEST": {
                        "instList": {
                            "10": {
                                "instanceId": 10,
                                "maxLsaInformation": {
                                    "maxLsa": 1000,
                                    "maxLsaThreshold": 75,
                                },
                                "routerId": "20.20.20.20",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 1500,
                                },
                            },
                        },
                    },
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["OSPF Instances ['1', '10'] crossed the maximum LSA threshold."],
        },
    },
    {
        "name": "skipped",
        "test": VerifyOSPFMaxLSA,
        "eos_data": [
            {
                "vrfs": {},
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["No OSPF instance found."]},
    },
]
