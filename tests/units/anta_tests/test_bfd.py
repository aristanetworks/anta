# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.bfd.py
"""
# pylint: disable=C0302
from __future__ import annotations

from typing import Any

# pylint: disable=C0413
# because of the patch above
from anta.tests.bfd import VerifyBFDPeers  # noqa: E402
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyBFDPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peers": {
                                    "": {
                                        "types": {
                                            "multihop": {
                                                "peerStats": {
                                                    "192.0.255.1": {
                                                        "status": "up",
                                                        "peerStatsDetail": {
                                                            "operTxInterval": 1200000,
                                                            "operRxInterval": 1200000,
                                                            "detectMult": 3,
                                                        },
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "bfd_neighbors": [
                {"neighbor": "192.0.255.7", "vrf": "default", "loopback": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-neighbor",
        "test": VerifyBFDPeers,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "bfd_neighbors": [
                {"neighbor": "192.0.255.70", "vrf": "default", "loopback": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Following BFD neighbors are not UP, not configured, or timers are not ok:\n{'192.0.255.70': {'default': 'Not Configured'}}"],
        },
    },
    {
        "name": "failure-session-down",
        "test": VerifyBFDPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peers": {
                                    "": {
                                        "types": {
                                            "multihop": {
                                                "peerStats": {
                                                    "192.0.255.1": {
                                                        "status": "down",
                                                        "peerStatsDetail": {
                                                            "operTxInterval": 1200000,
                                                            "operRxInterval": 1200000,
                                                            "detectMult": 3,
                                                        },
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "bfd_neighbors": [
                {"neighbor": "192.0.255.7", "vrf": "default", "loopback": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD neighbors are not UP, not configured, or timers are not ok:\n"
                "{'192.0.255.7': {'default': {'status': 'down', 'tx_interval': 1200000, 'rx_interval': 1200000, 'multiplier': 3}}}"
            ],
        },
    },
    {
        "name": "failure-incorrect-timers",
        "test": VerifyBFDPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peers": {
                                    "": {
                                        "types": {
                                            "multihop": {
                                                "peerStats": {
                                                    "192.0.255.1": {
                                                        "status": "up",
                                                        "peerStatsDetail": {
                                                            "operTxInterval": 1300000,
                                                            "operRxInterval": 1300000,
                                                            "detectMult": 4,
                                                        },
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "bfd_neighbors": [
                {"neighbor": "192.0.255.7", "vrf": "default", "loopback": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD neighbors are not UP, not configured, or timers are not ok:\n"
                "{'192.0.255.7': {'default': {'status': 'up', 'tx_interval': 1300000, 'rx_interval': 1300000, 'multiplier': 4}}}"
            ],
        },
    },
]
