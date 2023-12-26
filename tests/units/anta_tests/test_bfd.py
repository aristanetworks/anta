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
from anta.tests.bfd import VerifyBFDPeersIntervals, VerifyBFDSpecificPeers  # noqa: E402
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyBFDPeersIntervals,
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
                                                        "peerStatsDetail": {
                                                            "operTxInterval": 1200000,
                                                            "operRxInterval": 1200000,
                                                            "detectMult": 3,
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
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer": "192.0.255.7", "vrf": "default", "source_address": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBFDPeersIntervals,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "bfd_peers": [
                {"peer": "192.0.255.70", "vrf": "default", "source_address": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers are not configured or timers are not correct:\n{'192.0.255.70': {'default': 'Not Configured'}}"],
        },
    },
    {
        "name": "failure-incorrect-timers",
        "test": VerifyBFDPeersIntervals,
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
                                                        "peerStatsDetail": {
                                                            "operTxInterval": 1300000,
                                                            "operRxInterval": 1300000,
                                                            "detectMult": 4,
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
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer": "192.0.255.7", "vrf": "default", "source_address": "192.0.255.1", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3}
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured or timers are not correct:\n"
                "{'192.0.255.7': {'default': {'tx_interval': 1300000, 'rx_interval': 1300000, 'multiplier': 4}}}"
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBFDSpecificPeers,
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
                                                        "remoteDisc": 108328132,
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
        "inputs": {"bfd_peers": [{"peer": "192.0.255.7", "vrf": "default", "source_address": "192.0.255.1"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBFDSpecificPeers,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"bfd_peers": [{"peer": "192.0.255.70", "vrf": "default", "source_address": "192.0.255.1"}]},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers are not configured, status is not up or remote disc is zero:\n{'192.0.255.70': {'default': 'Not Configured'}}"],
        },
    },
    {
        "name": "failure-session-down",
        "test": VerifyBFDSpecificPeers,
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
                                                        "remoteDisc": 108328132,
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
        "inputs": {"bfd_peers": [{"peer": "192.0.255.7", "vrf": "default", "source_address": "192.0.255.1"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured, status is not up or remote disc is zero:\n"
                "{'192.0.255.7': {'default': {'status': 'down', 'remote_disc': 108328132}}}"
            ],
        },
    },
    {
        "name": "failure-zero-remote-disk",
        "test": VerifyBFDSpecificPeers,
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
                                                        "remoteDisc": 0,
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
        "inputs": {"bfd_peers": [{"peer": "192.0.255.7", "vrf": "default", "source_address": "192.0.255.1"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured, status is not up or remote disc is zero:\n"
                "{'192.0.255.7': {'default': {'status': 'down', 'remote_disc': 0}}}"
            ],
        },
    },
]
