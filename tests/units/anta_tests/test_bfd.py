# Copyright (c) 2023-2024 Arista Networks, Inc.
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
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 1200000,
                                            "operRxInterval": 1200000,
                                            "detectMult": 3,
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 1200000,
                                            "operRxInterval": 1200000,
                                            "detectMult": 3,
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBFDPeersIntervals,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 1200000,
                                            "operRxInterval": 1200000,
                                            "detectMult": 3,
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 1200000,
                                            "operRxInterval": 1200000,
                                            "detectMult": 3,
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "CS", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured or timers are not correct:\n"
                "{'192.0.255.7': {'CS': 'Not Configured'}, '192.0.255.70': {'MGMT': 'Not Configured'}}"
            ],
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
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 1200001,
                                            "operRxInterval": 1200000,
                                            "detectMult": 4,
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {
                                        "peerStatsDetail": {
                                            "operTxInterval": 120000,
                                            "operRxInterval": 120000,
                                            "detectMult": 5,
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200000, "rx_interval": 1200000, "multiplier": 3},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured or timers are not correct:\n"
                "{'192.0.255.7': {'default': {'tx_interval': 1200001, 'rx_interval': 1200000, 'multiplier': 4}}, "
                "'192.0.255.70': {'MGMT': {'tx_interval': 120000, 'rx_interval': 120000, 'multiplier': 5}}}"
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
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 108328132,
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 108328132,
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "default"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBFDSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 108328132,
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 108328132,
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "CS"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured, status is not up or remote disc is zero:\n"
                "{'192.0.255.7': {'CS': 'Not Configured'}, '192.0.255.70': {'MGMT': 'Not Configured'}}"
            ],
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
                                "peerStats": {
                                    "": {
                                        "status": "Down",
                                        "remoteDisc": 108328132,
                                    }
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {
                                        "status": "Down",
                                        "remoteDisc": 0,
                                    }
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "default"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured, status is not up or remote disc is zero:\n"
                "{'192.0.255.7': {'default': {'status': 'Down', 'remote_disc': 108328132}}, "
                "'192.0.255.70': {'MGMT': {'status': 'Down', 'remote_disc': 0}}}"
            ],
        },
    },
]
