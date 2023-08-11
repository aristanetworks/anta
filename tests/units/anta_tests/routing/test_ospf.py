# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.ospf.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.routing.ospf import VerifyOSPFNeighborCount, VerifyOSPFNeighborState
from tests.lib.test_case import test  # noqa: F401

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
        "expected": {
            "result": "failure",
            "messages": [
                "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
                " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}]."
            ],
        },
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
                                ]
                            }
                        }
                    }
                }
            }
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
        "inputs": {"number": 3},
        "expected": {
            "result": "failure",
            "messages": [
                "Some neighbors are not correctly configured: [{'vrf': 'default', 'instance': '666', 'neighbor': '7.7.7.7', 'state': '2-way'},"
                " {'vrf': 'BLAH', 'instance': '777', 'neighbor': '8.8.8.8', 'state': 'down'}]."
            ],
        },
    },
]
