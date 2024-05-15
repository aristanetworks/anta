# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.ospf.py."""

from __future__ import annotations

from typing import Any

from anta.tests.routing.isis import VerifyISISInterfaceMode, VerifyISISNeighborCount, VerifyISISNeighborState, VerifyISISSegmentRoutingAdjacencySegments
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

true: bool = True
false: bool = False

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
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
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
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
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
            "messages": ["Your segment has not been found: interface='Ethernet3' level=2 sid_origin='dynamic' address='10.0.1.2'."],
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
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
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
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
                                        },
                                        "level": 2,
                                    },
                                    {
                                        "ipAddress": "10.0.1.1",
                                        "localIntf": "Ethernet1",
                                        "sid": 116385,
                                        "lan": false,
                                        "sidOrigin": "dynamic",
                                        "protection": "unprotected",
                                        "flags": {
                                            "b": false,
                                            "v": true,
                                            "l": true,
                                            "f": false,
                                            "s": false,
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
]
