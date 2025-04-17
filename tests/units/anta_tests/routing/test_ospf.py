# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.ospf.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.routing.ospf import VerifyOSPFMaxLSA, VerifyOSPFNeighborCount, VerifyOSPFNeighborState
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyOSPFNeighborState, "success"): {
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
    (VerifyOSPFNeighborState, "failure"): {
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
                "Instance: 666 VRF: default Interface: 7.7.7.7 - Incorrect adjacency state - Expected: Full Actual: 2-way",
                "Instance: 777 VRF: BLAH Interface: 8.8.8.8 - Incorrect adjacency state - Expected: Full Actual: down",
            ],
        },
    },
    (VerifyOSPFNeighborState, "skipped-ospf-not-configured"): {
        "eos_data": [{"vrfs": {}}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["OSPF not configured"]},
    },
    (VerifyOSPFNeighborState, "skipped-neighbor-not-found"): {
        "eos_data": [{"vrfs": {"default": {"instList": {"666": {"ospfNeighborEntries": []}}}, "BLAH": {"instList": {"777": {"ospfNeighborEntries": []}}}}}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["No OSPF neighbor detected"]},
    },
    (VerifyOSPFNeighborCount, "success"): {
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
    (VerifyOSPFNeighborCount, "failure-good-number-wrong-state"): {
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
        "expected": {"result": "failure", "messages": ["Neighbor count mismatch - Expected: 3 Actual: 1"]},
    },
    (VerifyOSPFNeighborCount, "skipped-ospf-not-configured"): {
        "eos_data": [{"vrfs": {}}],
        "inputs": {"number": 3},
        "expected": {"result": "skipped", "messages": ["OSPF not configured"]},
    },
    (VerifyOSPFNeighborCount, "skipped-no-neighbor-detected"): {
        "eos_data": [{"vrfs": {"default": {"instList": {"666": {"ospfNeighborEntries": []}}}, "BLAH": {"instList": {"777": {"ospfNeighborEntries": []}}}}}],
        "inputs": {"number": 3},
        "expected": {"result": "skipped", "messages": ["No OSPF neighbor detected"]},
    },
    (VerifyOSPFMaxLSA, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "1": {
                                "instanceId": 1,
                                "maxLsaInformation": {"maxLsa": 12000, "maxLsaThreshold": 75},
                                "routerId": "1.1.1.1",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 9,
                                },
                            }
                        }
                    },
                    "TEST": {
                        "instList": {
                            "10": {
                                "instanceId": 10,
                                "maxLsaInformation": {"maxLsa": 1000, "maxLsaThreshold": 75},
                                "routerId": "20.20.20.20",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 5,
                                },
                            }
                        }
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    (VerifyOSPFMaxLSA, "failure"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "instList": {
                            "1": {
                                "instanceId": 1,
                                "maxLsaInformation": {"maxLsa": 12000, "maxLsaThreshold": 75},
                                "routerId": "1.1.1.1",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 11500,
                                },
                            }
                        }
                    },
                    "TEST": {
                        "instList": {
                            "10": {
                                "instanceId": 10,
                                "maxLsaInformation": {"maxLsa": 1000, "maxLsaThreshold": 75},
                                "routerId": "20.20.20.20",
                                "lsaInformation": {
                                    "lsaArrivalInterval": 1000,
                                    "lsaStartInterval": 1000,
                                    "lsaHoldInterval": 5000,
                                    "lsaMaxWaitInterval": 5000,
                                    "numLsa": 1500,
                                },
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
                "Instance: 1 - Crossed the maximum LSA threshold - Expected: < 9000 Actual: 11500",
                "Instance: 10 - Crossed the maximum LSA threshold - Expected: < 750 Actual: 1500",
            ],
        },
    },
    (VerifyOSPFMaxLSA, "skipped"): {"eos_data": [{"vrfs": {}}], "inputs": None, "expected": {"result": "skipped", "messages": ["OSPF not configured"]}},
}
