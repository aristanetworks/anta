# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.ospf.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.routing.ospf import VerifyOSPFNeighborCount, VerifyOSPFNeighborState
from tests.lib.utils import generate_test_ids

INPUT_OSPF_NEIGHBOR_STATE: list[dict[str, Any]] = [
    {
        "name": "success",
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
                                ]
                            }
                        }
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
                                    }
                                ]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
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
                                ]
                            }
                        }
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
                                    }
                                ]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure"},
        "messages": [
            "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
            " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}]."
        ],
    },
]

INPUT_OSPF_NEIGHBOR_COUNT: List[Dict[str, Any]] = [
    {
        "name": "success",
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
                                ]
                            }
                        }
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
                                    }
                                ]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": 3,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
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
                                ]
                            }
                        }
                    }
                }
            }
        ],
        "inputs": 3,
        "expected": {"result": "failure", "messages": ["device has 1 neighbors (expected 3)"]},
    },
    {
        "name": "failure-good-number-wrong-state",
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
                                ]
                            }
                        }
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
                                    }
                                ]
                            }
                        }
                    },
                }
            }
        ],
        "inputs": 3,
        "expected": {"result": "failure"},
        "messages": [
            "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
            " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}]."
        ],
    },
    {
        "name": "skipped",
        "eos_data": [{}],
        "inputs": None,
        "expected_result": "skipped",
        "messages": ["VerifyOSPFNeighborCount was not run as the number given 'None' is not a valid value."],
    },
]
