# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.ospf.py."""

# pylint: disable=too-many-lines

from __future__ import annotations

from typing import Any

import pytest

from anta.tests.routing.isis import (
    VerifyISISInterfaceMode,
    VerifyISISNeighborCount,
    VerifyISISNeighborState,
    VerifyISISSegmentRoutingAdjacencySegments,
    VerifyISISSegmentRoutingDataplane,
    VerifyISISSegmentRoutingTunnels,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success-default-vrf",
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
                                                "state": "down",
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
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-vrfs",
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
            },
        ],
        "inputs": {"check_all_vrfs": True},
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
            "messages": ["Instance: CORE-ISIS VRF: default Interface: Ethernet1 - Adjacency down"],
        },
    },
    {
        "name": "skipped-not-configured",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {"vrfs": {}},
        ],
        "inputs": None,
        "expected": {
            "result": "skipped",
            "messages": ["IS-IS not configured"],
        },
    },
    {
        "name": "failure-multiple-vrfs",
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
                                                "state": "down",
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
            },
        ],
        "inputs": {"check_all_vrfs": True},
        "expected": {
            "result": "failure",
            "messages": ["Instance: CORE-ISIS VRF: customer Interface: Ethernet2 - Adjacency down"],
        },
    },
    {
        "name": "skipped-no-neighbor-detected",
        "test": VerifyISISNeighborState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "CORE-ISIS": {
                                "neighbors": {},
                            },
                        },
                    },
                    "customer": {"isisInstances": {"CORE-ISIS": {"neighbors": {}}}},
                }
            },
        ],
        "inputs": {"check_all_vrfs": True},
        "expected": {
            "result": "skipped",
            "messages": ["No IS-IS neighbor detected"],
        },
    },
    {
        "name": "success-default-vrf",
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
        "name": "success-multiple-VRFs",
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
                    },
                    "PROD": {
                        "isisInstances": {
                            "PROD-ISIS": {
                                "interfaces": {
                                    "Ethernet3": {
                                        "enabled": True,
                                        "intfLevels": {
                                            "1": {
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
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "level": 2, "count": 1},
                {"name": "Ethernet2", "level": 2, "count": 1},
                {"name": "Ethernet3", "vrf": "PROD", "level": 1, "count": 1},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "skipped-not-configured",
        "test": VerifyISISNeighborCount,
        "eos_data": [
            {"vrfs": {}},
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet1", "level": 2, "count": 1},
            ]
        },
        "expected": {
            "result": "skipped",
            "messages": ["IS-IS not configured"],
        },
    },
    {
        "name": "failure-interface-not-configured",
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
            "messages": ["Interface: Ethernet2 VRF: default Level: 2 - Not configured"],
        },
    },
    {
        "name": "success-interface-is-in-wrong-vrf",
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
                    "PROD": {
                        "isisInstances": {
                            "PROD-ISIS": {
                                "interfaces": {
                                    "Ethernet2": {
                                        "enabled": True,
                                        "intfLevels": {
                                            "1": {
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
                    },
                }
            },
        ],
        "inputs": {
            "interfaces": [
                {"name": "Ethernet2", "level": 2, "count": 1},
                {"name": "Ethernet1", "vrf": "PROD", "level": 1, "count": 1},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Interface: Ethernet2 VRF: default Level: 2 - Not configured", "Interface: Ethernet1 VRF: PROD Level: 1 - Not configured"],
        },
    },
    {
        "name": "failure-wrong-count",
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
            "messages": ["Interface: Ethernet1 VRF: default Level: 2 - Neighbor count mismatch - Expected: 1 Actual: 3"],
        },
    },
    {
        "name": "success-default-vrf",
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
        "name": "success-multiple-VRFs",
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
                                }
                            }
                        }
                    },
                    "PROD": {
                        "isisInstances": {
                            "PROD-ISIS": {
                                "interfaces": {
                                    "Ethernet4": {
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
                                    "Ethernet5": {
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
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
                {"name": "Ethernet4", "mode": "point-to-point", "vrf": "PROD"},
                {"name": "Ethernet5", "mode": "passive", "vrf": "PROD"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-interface-not-passive",
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
            "messages": ["Interface: Ethernet2 VRF: default Level: 2 - Not running in passive mode"],
        },
    },
    {
        "name": "failure-interface-not-point-to-point",
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
            "messages": ["Interface: Ethernet1 VRF: default Level: 2 - Incorrect interface mode - Expected: point-to-point Actual: broadcast"],
        },
    },
    {
        "name": "failure-interface-wrong-vrf",
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
                "Interface: Loopback0 VRF: default Level: 2 - Not configured",
                "Interface: Ethernet2 VRF: default Level: 2 - Not configured",
                "Interface: Ethernet1 VRF: default Level: 2 - Not configured",
            ],
        },
    },
    {
        "name": "skipped-not-configured",
        "test": VerifyISISInterfaceMode,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet2", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
            ]
        },
        "expected": {"result": "skipped", "messages": ["IS-IS not configured"]},
    },
    {
        "name": "failure-multiple-VRFs",
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
                                }
                            }
                        }
                    },
                    "PROD": {
                        "isisInstances": {
                            "PROD-ISIS": {
                                "interfaces": {
                                    "Ethernet4": {
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
                                    "Ethernet5": {
                                        "enabled": True,
                                        "interfaceType": "broadcast",
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
                    },
                }
            }
        ],
        "inputs": {
            "interfaces": [
                {"name": "Loopback0", "mode": "passive"},
                {"name": "Ethernet1", "mode": "point-to-point", "vrf": "default"},
                {"name": "Ethernet4", "mode": "point-to-point", "vrf": "PROD"},
                {"name": "Ethernet5", "mode": "passive", "vrf": "PROD"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Interface: Ethernet1 VRF: default Level: 2 - Incorrect interface mode - Expected: point-to-point Actual: broadcast",
                "Interface: Ethernet4 VRF: PROD Level: 2 - Incorrect interface mode - Expected: point-to-point Actual: broadcast",
                "Interface: Ethernet5 VRF: PROD Level: 2 - Not running in passive mode",
            ],
        },
    },
    {
        "name": "skipped-not-configured",
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
        "expected": {"result": "skipped", "messages": ["IS-IS not configured"]},
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "success",
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
        "name": "failure-segment-not-found",
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
            "messages": ["Instance: CORE-ISIS VRF: default Local Intf: Ethernet3 Adj IP Address: 10.0.1.2 - Adjacency segment not found"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "failure-no-segments-incorrect-instance",
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
            "messages": ["Instance: CORE-ISIS2 VRF: default - No adjacency segments found"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "failure-incorrect-segment-level",
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
            "messages": ["Instance: CORE-ISIS VRF: default Local Intf: Ethernet2 Adj IP Address: 10.0.1.3 - Incorrect IS-IS level - Expected: 1 Actual: 2"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingAdjacencySegments,
        "name": "failure-incorrect-sid-origin",
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
                                        "sidOrigin": "configured",
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
                            "level": 2,  # Wrong level
                        },
                    ],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Instance: CORE-ISIS VRF: default Local Intf: Ethernet2 Adj IP Address: 10.0.1.3 - Incorrect SID origin - Expected: dynamic Actual: configured"
            ],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "success",
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
        "name": "failure-incorrect-dataplane",
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
            "messages": ["Instance: CORE-ISIS VRF: default - Data-plane not correctly configured - Expected: UNSET Actual: MPLS"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "failure-instance-not-configured",
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
            "messages": ["Instance: CORE-ISIS2 VRF: default - Not configured"],
        },
    },
    {
        "test": VerifyISISSegmentRoutingDataplane,
        "name": "skipped-not-configured",
        "eos_data": [{"vrfs": {}}],
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
            "result": "skipped",
            "messages": ["IS-IS not configured"],
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
            "messages": ["Tunnel to 1.0.0.122/32 is not found."],
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
            "messages": ["Tunnel to 1.0.0.13/32 is incorrect."],
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
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect."],
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
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect."],
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
            "messages": ["Tunnel to 1.0.0.122/32 is incorrect."],
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
            "messages": ["Tunnel to 1.0.0.111/32 is incorrect."],
        },
    },
    {
        "test": VerifyISISSegmentRoutingTunnels,
        "name": "skipped with ISIS-SR not running",
        "eos_data": [{"entries": {}}],
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
            "result": "skipped",
            "messages": ["IS-IS-SR is not running on device."],
        },
    },
]
