# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.ospf.py."""

# pylint: disable=too-many-lines

from __future__ import annotations

from typing import Any

import pytest

from anta.tests.routing.isis import (
    VerifyISISGracefulRestart,
    VerifyISISInterfaceMode,
    VerifyISISNeighborCount,
    VerifyISISNeighborState,
    VerifyISISSegmentRoutingAdjacencySegments,
    VerifyISISSegmentRoutingDataplane,
    VerifyISISSegmentRoutingTunnels,
    _get_interface_data,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success only default vrf",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "neighbors": {
                                    "0168.0000.0111": {
                                        "adjacencies": [
                                            {
                                                "hostname": "s1-p01",
                                                "circuitId": "83",
                                                "interfaceName": "Ethernet1",
                                                "state": "up",
                                                "lastHelloTime": 1713688408,
                                                "routerIdV4": "1.0.0.111",
                                            }
                                        ]
                                    },
                                    "0168.0000.0112": {
                                        "adjacencies": [
                                            {
                                                "hostname": "s1-p02",
                                                "circuitId": "87",
                                                "interfaceName": "Ethernet2",
                                                "state": "up",
                                                "lastHelloTime": 1713688405,
                                                "routerIdV4": "1.0.0.112",
                                            }
                                        ]
                                    },
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success different vrfs",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "neighbors": {
                                    "0168.0000.0111": {
                                        "adjacencies": [
                                            {
                                                "hostname": "s1-p01",
                                                "circuitId": "83",
                                                "interfaceName": "Ethernet1",
                                                "state": "up",
                                                "lastHelloTime": 1713688408,
                                                "routerIdV4": "1.0.0.111",
                                            }
                                        ]
                                    },
                                },
                            },
                        },
                        "customer": {
                            "isisInstances": {
                                "CORE-ISIS": {
                                    "neighbors": {
                                        "0168.0000.0112": {
                                            "adjacencies": [
                                                {
                                                    "hostname": "s1-p02",
                                                    "circuitId": "87",
                                                    "interfaceName": "Ethernet2",
                                                    "state": "up",
                                                    "lastHelloTime": 1713688405,
                                                    "routerIdV4": "1.0.0.112",
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "neighbors": {
                                    "0168.0000.0111": {
                                        "adjacencies": [
                                            {
                                                "hostname": "s1-p01",
                                                "circuitId": "83",
                                                "interfaceName": "Ethernet1",
                                                "state": "down",
                                                "lastHelloTime": 1713688408,
                                                "routerIdV4": "1.0.0.111",
                                            }
                                        ]
                                    },
                                    "0168.0000.0112": {
                                        "adjacencies": [
                                            {
                                                "hostname": "s1-p02",
                                                "circuitId": "87",
                                                "interfaceName": "Ethernet2",
                                                "state": "up",
                                                "lastHelloTime": 1713688405,
                                                "routerIdV4": "1.0.0.112",
                                            }
                                        ]
                                    },
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Some neighbors are not in the correct state (UP): [{'vrf': 'default', 'instance': 'CORE-ISIS', 'neighbor': 's1-p01', 'state': 'down'}]."],
        },
    },
    {
        "name": "skipped - no neighbor",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {"vrfs": {"default": {"isisInstances": {"CORE-ISIS": {"neighbors": {}}}}}},
        ],
        "inputs": None,
        "expected": {
            "result": "skipped",
            "messages": ["No IS-IS neighbor detected"],
        },
    },
    {
        "name": "success only default vrf",
        "test": VerifyISISNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Loopback0": {
                                        "enabled": True,
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet1": {
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet2": {
                                        "enabled": True,
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "88",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "level": 2, "count": 1},
                {"name": "Ethernet2", "level": 2, "count": 1},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "skipped - no neighbor",
        "test": VerifyISISNeighborCount,
        "eos_data": [
            {"vrfs": {"default": {"isisInstances": {"CORE-ISIS": {"interfaces": {}}}}}},
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "level": 2, "count": 1},
            ]
        },
        "expected": {
            "result": "skipped",
            "messages": ["No IS-IS neighbor detected"],
        },
    },
    {
        "name": "failure - missing interface",
        "test": VerifyISISNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Ethernet1": {
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 0,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "level": 2, "count": 1},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["No neighbor detected for interface Ethernet2"],
        },
    },
    {
        "name": "failure - wrong count",
        "test": VerifyISISNeighborCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Ethernet1": {
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 3,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "level": 2, "count": 1},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface Ethernet1: expected Level 2: count 1, got Level 2: count 3"],
        },
    },
    {
        "name": "success VerifyISISInterfaceMode only default vrf",
        "test": VerifyISISInterfaceMode,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Loopback0": {
                                        "enabled": True,
                                        "index": 2,
                                        "snpa": "0:0:0:0:0:0",
                                        "mtu": 65532,
                                        "interfaceAddressFamily": "ipv4",
                                        "interfaceType": "loopback",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet1": {
                                        "enabled": True,
                                        "index": 132,
                                        "snpa": "P2P",
                                        "interfaceType": "point-to-point",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet2": {
                                        "enabled": True,
                                        "interfaceType": "broadcast",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 0,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure VerifyISISInterfaceMode default vrf with interface not running passive mode",
        "test": VerifyISISInterfaceMode,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Loopback0": {
                                        "enabled": True,
                                        "index": 2,
                                        "snpa": "0:0:0:0:0:0",
                                        "mtu": 65532,
                                        "interfaceAddressFamily": "ipv4",
                                        "interfaceType": "loopback",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet1": {
                                        "enabled": True,
                                        "index": 132,
                                        "snpa": "P2P",
                                        "interfaceType": "point-to-point",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet2": {
                                        "enabled": True,
                                        "interfaceType": "point-to-point",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 0,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface Ethernet2 in VRF default is not running in passive mode"],
        },
    },
    {
        "name": "failure VerifyISISInterfaceMode default vrf with interface not running point-point mode",
        "test": VerifyISISInterfaceMode,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Loopback0": {
                                        "enabled": True,
                                        "index": 2,
                                        "snpa": "0:0:0:0:0:0",
                                        "mtu": 65532,
                                        "interfaceAddressFamily": "ipv4",
                                        "interfaceType": "loopback",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet1": {
                                        "enabled": True,
                                        "index": 132,
                                        "snpa": "P2P",
                                        "interfaceType": "broadcast",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet2": {
                                        "enabled": True,
                                        "interfaceType": "broadcast",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 0,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface Ethernet1 in VRF default is not running in point-to-point reporting broadcast"],
        },
    },
    {
        "name": "failure VerifyISISInterfaceMode default vrf with interface not running correct VRF mode",
        "test": VerifyISISInterfaceMode,
        "eos_data": [
            {
                "vrfs": {
                    "fake_vrf": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "interfaces": {
                                    "Loopback0": {
                                        "enabled": True,
                                        "index": 2,
                                        "snpa": "0:0:0:0:0:0",
                                        "mtu": 65532,
                                        "interfaceAddressFamily": "ipv4",
                                        "interfaceType": "loopback",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet1": {
                                        "enabled": True,
                                        "index": 132,
                                        "snpa": "P2P",
                                        "interfaceType": "point-to-point",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 1,
                                                "linkId": "84",
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": False,
                                                "v4Protection": "link",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                    "Ethernet2": {
                                        "enabled": True,
                                        "interfaceType": "broadcast",
                                        "intfLevels": {
                                            "2": {
                                                "ipv4Metric": 10,
                                                "numAdjacencies": 0,
                                                "sharedSecretProfile": "",
                                                "isisAdjacencies": [],
                                                "passive": True,
                                                "v4Protection": "disabled",
                                                "v6Protection": "disabled",
                                            }
                                        },
                                        "interfaceSpeed": 1000,
                                        "areaProxyBoundary": False,
                                    },
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface Loopback0 not found in VRF default",
                "Interface Ethernet2 not found in VRF default",
                "Interface Ethernet1 not found in VRF default",
            ],
        },
    },
    {
        "name": "skipped VerifyISISInterfaceMode no vrf",
        "test": VerifyISISInterfaceMode,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {"result": "skipped", "messages": ["IS-IS is not configured on device"]},
    },
    {
        "name": "Skipped of VerifyISISSegmentRoutingAdjacencySegments no VRF.",
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                        }
                    ],
                }
            ]
        },
        "expected": {"result": "skipped", "messages": ["IS-IS is not configured on device"]},
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "Success of VerifyISISSegmentRoutingAdjacencySegments in default VRF.",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                                "adjSidAllocationMode": "SrOnly",
                                "adjSidPoolBase": 116384,
                                "adjSidPoolSize": 16384,
                                "adjacencySegments": [
                                    {
                                        "ipAddress": "10.0.1.3",
                                        "localIntf": "Ethernet2",
                                        "sid": 116384,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                ],
                                "receivedGlobalAdjacencySegments": [],
                                "misconfiguredAdjacencySegments": [],
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                        }
                    ],
                }
            ]
        },
        "expected": {
            "result": "success",
            "messages": [],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "Failure of VerifyISISSegmentRoutingAdjacencySegments in default VRF for incorrect segment definition.",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                                "adjSidAllocationMode": "SrOnly",
                                "adjSidPoolBase": 116384,
                                "adjSidPoolSize": 16384,
                                "adjacencySegments": [
                                    {
                                        "ipAddress": "10.0.1.3",
                                        "localIntf": "Ethernet2",
                                        "sid": 116384,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                ],
                                "receivedGlobalAdjacencySegments": [],
                                "misconfiguredAdjacencySegments": [],
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                        },
                        {
                            "interface": "Ethernet3",
                            "address": "10.0.1.2",
                            "sid_origin": "dynamic",
                        },
                    ],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Your segment has not been found: interface='Ethernet3' level=2 sid_origin='dynamic' address=IPv4Address('10.0.1.2')."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "Failure of VerifyISISSegmentRoutingAdjacencySegments with incorrect VRF.",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                                "adjSidAllocationMode": "SrOnly",
                                "adjSidPoolBase": 116384,
                                "adjSidPoolSize": 16384,
                                "adjacencySegments": [
                                    {
                                        "ipAddress": "10.0.1.3",
                                        "localIntf": "Ethernet2",
                                        "sid": 116384,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                ],
                                "receivedGlobalAdjacencySegments": [],
                                "misconfiguredAdjacencySegments": [],
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "custom",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                        },
                        {
                            "interface": "Ethernet3",
                            "address": "10.0.1.2",
                            "sid_origin": "dynamic",
                        },
                    ],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["VRF custom is not configured to run segment routging."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "Failure of VerifyISISSegmentRoutingAdjacencySegments with incorrect Instance.",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                                "adjSidAllocationMode": "SrOnly",
                                "adjSidPoolBase": 116384,
                                "adjSidPoolSize": 16384,
                                "adjacencySegments": [
                                    {
                                        "ipAddress": "10.0.1.3",
                                        "localIntf": "Ethernet2",
                                        "sid": 116384,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                ],
                                "receivedGlobalAdjacencySegments": [],
                                "misconfiguredAdjacencySegments": [],
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS2",
                    "vrf": "default",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                        },
                        {
                            "interface": "Ethernet3",
                            "address": "10.0.1.2",
                            "sid_origin": "dynamic",
                        },
                    ],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Instance CORE-ISIS2 is not found in vrf default."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "Failure of VerifyISISSegmentRoutingAdjacencySegments with incorrect segment info.",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                                "adjSidAllocationMode": "SrOnly",
                                "adjSidPoolBase": 116384,
                                "adjSidPoolSize": 16384,
                                "adjacencySegments": [
                                    {
                                        "ipAddress": "10.0.1.3",
                                        "localIntf": "Ethernet2",
                                        "sid": 116384,
                                        "lan": False,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": False,
                                            "v": True,
                                            "l": True,
                                            "f": False,
                                            "s": False,
                                        },
                                        "level": 2,
                                    },
                                ],
                                "receivedGlobalAdjacencySegments": [],
                                "misconfiguredAdjacencySegments": [],
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "segments": [
                        {
                            "interface": "Ethernet2",
                            "address": "10.0.1.3",
                            "sid_origin": "dynamic",
                            "level": 1,  # Wrong level
                        },
                    ],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                (
                    "Your segment is not correct: Expected: interface='Ethernet2' level=1 sid_origin='dynamic' address=IPv4Address('10.0.1.3') - "
                    "Found: {'ipAddress': '10.0.1.3', 'localIntf': 'Ethernet2', 'sid': 116384, 'lan': False, 'sidOrigin': 'dynamic', 'protection': "
                    "'unprotected', 'flags': {'b': False, 'v': True, 'l': True, 'f': False, 's': False}, 'level': 2}."
                )
            ],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "Check VerifyISISSegmentRoutingDataplane is running successfully",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "dataplane": "MPLS",
                },
            ]
        },
        "expected": {
            "result": "success",
            "messages": [],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "Check VerifyISISSegmentRoutingDataplane is failing with incorrect dataplane",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "default",
                    "dataplane": "unset",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["ISIS instance CORE-ISIS is not running dataplane unset (MPLS)"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "Check VerifyISISSegmentRoutingDataplane is failing for unknown instance",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS2",
                    "vrf": "default",
                    "dataplane": "unset",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Instance CORE-ISIS2 is not found in vrf default."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "Check VerifyISISSegmentRoutingDataplane is failing for unknown VRF",
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "dataPlane": "MPLS",
                                "routerId": "1.0.0.11",
                                "systemId": "0168.0000.0011",
                                "hostname": "s1-pe01",
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "wrong_vrf",
                    "dataplane": "unset",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["VRF wrong_vrf is not configured to run segment routing."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "Check VerifyISISSegmentRoutingDataplane is skipped",
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "instances": [
                {
                    "name": "CORE-ISIS",
                    "vrf": "wrong_vrf",
                    "dataplane": "unset",
                },
            ]
        },
        "expected": {
            "result": "skipped",
            "messages": ["IS-IS-SR is not running on device"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "runs successfully",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "ip"}]},
                {
                    "endpoint": "1.0.0.111/32",
                    "vias": [{"type": "tunnel", "tunnel_id": "ti-lfa"}],
                },
                {
                    "endpoint": "1.0.0.122/32",
                    "vias": [
                        {"interface": "Ethernet1", "nexthop": "10.0.1.1"},  # Testing empty type
                        {"type": "ip", "interface": "Ethernet2", "nexthop": "10.0.1.3"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "success",
            "messages": [],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "is skipped if not entry founf in EOS",
        "eos_data": [{"entries": {}}],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
            ]
        },
        "expected": {
            "result": "skipped",
            "messages": ["IS-IS-SR is not running on device."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "runs successfully",
        "eos_data": [
            {
                "entries": {
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to endpoint=IPv4Network('1.0.0.122/32') vias=None is not found."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "fails with incorrect tunnel type",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "tunnel"}]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to 1.0.0.13/32 is incorrect: incorrect tunnel type"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "fails with incorrect nexthop",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "ip"}]},
                {
                    "endpoint": "1.0.0.122/32",
                    "vias": [
                        {"type": "ip", "interface": "Ethernet1", "nexthop": "10.0.1.2"},
                        {"type": "ip", "interface": "Ethernet2", "nexthop": "10.0.1.3"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect: incorrect nexthop"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "fails with incorrect nexthop",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "ip"}]},
                {
                    "endpoint": "1.0.0.122/32",
                    "vias": [
                        {"type": "ip", "interface": "Ethernet4", "nexthop": "10.0.1.1"},
                        {"type": "ip", "interface": "Ethernet2", "nexthop": "10.0.1.3"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect: incorrect interface"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "fails with incorrect interface",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "ip"}]},
                {
                    "endpoint": "1.0.0.122/32",
                    "vias": [
                        {"type": "ip", "interface": "Ethernet1", "nexthop": "10.0.1.2"},
                        {"type": "ip", "interface": "Ethernet2", "nexthop": "10.0.1.3"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect: incorrect nexthop"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "fails with incorrect tunnel ID type",
        "eos_data": [
            {
                "entries": {
                    "3": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "31": {
                        "endpoint": "1.0.0.13/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "32": {
                        "endpoint": "1.0.0.122/32",
                        "vias": [
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.1",
                                "interface": "Ethernet1",
                                "labels": ["900021"],
                            },
                            {
                                "type": "ip",
                                "nexthop": "10.0.1.3",
                                "interface": "Ethernet2",
                                "labels": ["900021"],
                            },
                        ],
                    },
                    "2": {
                        "endpoint": "1.0.0.111/32",
                        "vias": [
                            {
                                "type": "tunnel",
                                "tunnelId": {"type": "TI-LFA", "index": 4},
                                "labels": ["3"],
                            }
                        ],
                    },
                }
            }
        ],
        "inputs": {
            "entries": [
                {"endpoint": "1.0.0.122/32"},
                {"endpoint": "1.0.0.13/32", "vias": [{"type": "ip"}]},
                {
                    "endpoint": "1.0.0.111/32",
                    "vias": [
                        {"type": "tunnel", "tunnel_id": "unset"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Tunnel to 1.0.0.111/32 is incorrect: incorrect tunnel ID"],
        },
    },
    {
        "name": "success",
        "test": VerifyISISGracefulRestart,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "1": {"gracefulRestart": True, "gracefulRestartHelper": True},
                            "2": {"gracefulRestart": True, "gracefulRestartHelper": True},
                        }
                    },
                    "test": {
                        "isisInstances": {
                            "1": {"gracefulRestart": True, "gracefulRestartHelper": True},
                            "2": {"gracefulRestart": True, "gracefulRestartHelper": True},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "instances": [
                {"vrf": "default", "name": "1", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "default", "name": "2", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "test", "name": "1", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "test", "name": "2", "graceful_restart": True, "graceful_helper": True},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-isis-not-configured",
        "test": VerifyISISGracefulRestart,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"instances": [{"vrf": "default", "name": "1", "graceful_restart": True, "graceful_helper": True}]},
        "expected": {"result": "failure", "messages": ["ISIS is not configured"]},
    },
    {
        "name": "failure-isis-instance-not-found",
        "test": VerifyISISGracefulRestart,
        "eos_data": [{"vrfs": {"default": {"isisInstances": {"2": {"gracefulRestart": True, "gracefulRestartHelper": True}}}}}],
        "inputs": {"instances": [{"vrf": "default", "name": "1", "graceful_restart": True, "graceful_helper": True}]},
        "expected": {"result": "failure", "messages": ["Instance: 1 VRF: default - Not found"]},
    },
    {
        "name": "failure-graceful-restart-disabled",
        "test": VerifyISISGracefulRestart,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "1": {"gracefulRestart": False, "gracefulRestartHelper": True},
                            "2": {"gracefulRestart": True, "gracefulRestartHelper": True},
                        }
                    },
                    "test": {
                        "isisInstances": {
                            "1": {"gracefulRestart": False, "gracefulRestartHelper": True},
                            "2": {"gracefulRestart": True, "gracefulRestartHelper": True},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "instances": [
                {"vrf": "default", "name": "1", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "default", "name": "2", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "test", "name": "1", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "test", "name": "2", "graceful_restart": True, "graceful_helper": True},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Instance: 1 VRF: default - Graceful Restart disabled", "Instance: 1 VRF: test - Graceful Restart disabled"],
        },
    },
    {
        "name": "failure-graceful-restart-helper-disabled",
        "test": VerifyISISGracefulRestart,
        "eos_data": [
            {
                "vrfs": {
                    "default": {"isisInstances": {"1": {"gracefulRestart": True, "gracefulRestartHelper": False}}},
                    "test": {"isisInstances": {"1": {"gracefulRestart": True, "gracefulRestartHelper": False}}},
                }
            }
        ],
        "inputs": {
            "instances": [
                {"vrf": "default", "name": "1", "graceful_restart": True, "graceful_helper": True},
                {"vrf": "test", "name": "1", "graceful_restart": True, "graceful_helper": True},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Instance: 1 VRF: default - Graceful Restart Helper disabled", "Instance: 1 VRF: test - Graceful Restart Helper disabled"],
        },
    },
]


COMMAND_OUTPUT = {
    "vrfs": {
        "default": {
            "isisInstances": {
                "CORE-ISIS": {
                    "interfaces": {
                        "Loopback0": {
                            "enabled": True,
                            "intfLevels": {
                                "2": {
                                    "ipv4Metric": 10,
                                    "sharedSecretProfile": "",
                                    "isisAdjacencies": [],
                                    "passive": True,
                                    "v4Protection": "disabled",
                                    "v6Protection": "disabled",
                                }
                            },
                            "areaProxyBoundary": False,
                        },
                        "Ethernet1": {
                            "intfLevels": {
                                "2": {
                                    "ipv4Metric": 10,
                                    "numAdjacencies": 1,
                                    "linkId": "84",
                                    "sharedSecretProfile": "",
                                    "isisAdjacencies": [],
                                    "passive": False,
                                    "v4Protection": "link",
                                    "v6Protection": "disabled",
                                }
                            },
                            "interfaceSpeed": 1000,
                            "areaProxyBoundary": False,
                        },
                    }
                }
            }
        },
        "EMPTY": {"isisInstances": {}},
        "NO_INTERFACES": {"isisInstances": {"CORE-ISIS": {}}},
    }
}
EXPECTED_LOOPBACK_0_OUTPUT = {
    "enabled": True,
    "intfLevels": {
        "2": {
            "ipv4Metric": 10,
            "sharedSecretProfile": "",
            "isisAdjacencies": [],
            "passive": True,
            "v4Protection": "disabled",
            "v6Protection": "disabled",
        }
    },
    "areaProxyBoundary": False,
}


@pytest.mark.parametrize(
    ("interface", "vrf", "expected_value"),
    [
        pytest.param("Loopback0", "WRONG_VRF", None, id="VRF_not_found"),
        pytest.param("Loopback0", "EMPTY", None, id="VRF_no_ISIS_instances"),
        pytest.param("Loopback0", "NO_INTERFACES", None, id="ISIS_instance_no_interfaces"),
        pytest.param("Loopback42", "default", None, id="interface_not_found"),
        pytest.param("Loopback0", "default", EXPECTED_LOOPBACK_0_OUTPUT, id="interface_found"),
    ],
)
def test__get_interface_data(interface: str, vrf: str, expected_value: dict[str, Any] | None) -> None:
    """Test anta.tests.routing.isis._get_interface_data."""
    assert _get_interface_data(interface, vrf, COMMAND_OUTPUT) == expected_value
