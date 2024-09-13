# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.bfd.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import Any

from anta.tests.bfd import VerifyBFDPeersHealth, VerifyBFDPeersIntervals, VerifyBFDPeersRegProtocols, VerifyBFDSpecificPeers
from tests.units.anta_tests import test

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
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
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
                {"peer_address": "192.0.255.7", "vrf": "CS", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
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
                                            "operTxInterval": 1300000,
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
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not configured or timers are not correct:\n"
                "{'192.0.255.7': {'default': {'tx_interval': 1300, 'rx_interval': 1200, 'multiplier': 4}}, "
                "'192.0.255.70': {'MGMT': {'tx_interval': 120, 'rx_interval': 120, 'multiplier': 5}}}"
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
    {
        "name": "success",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    },
                }
            },
            {
                "utcTime": 1703667348.111288,
            },
        ],
        "inputs": {"down_threshold": 2},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "MGMT": {
                        "ipv6Neighbors": {},
                        "ipv4Neighbors": {},
                    },
                    "default": {
                        "ipv6Neighbors": {},
                        "ipv4Neighbors": {},
                    },
                }
            },
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["No IPv4 BFD peers are configured for any VRF."],
        },
    },
    {
        "name": "failure-session-down",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "down",
                                        "remoteDisc": 0,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "status": "down",
                                        "remoteDisc": 0,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    },
                }
            },
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers are not up:\n192.0.255.7 is down in default VRF with remote disc 0.\n192.0.255.71 is down in MGMT VRF with remote disc 0."
            ],
        },
    },
    {
        "name": "failure-session-up-disc",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 0,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "Ethernet2",
                                    }
                                }
                            },
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 0,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "Ethernet2",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers were down:\n192.0.255.7 in default VRF has remote disc 0.\n192.0.255.71 in default VRF has remote disc 0."],
        },
    },
    {
        "name": "failure-last-down",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                            "192.0.255.17": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "remoteDisc": 3940685114,
                                        "lastDown": 1703657258.652725,
                                        "l3intf": "",
                                    }
                                }
                            },
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {
                "utcTime": 1703667348.111288,
            },
        ],
        "inputs": {"down_threshold": 4},
        "expected": {
            "result": "failure",
            "messages": [
                "Following BFD peers were down:\n192.0.255.7 in default VRF was down 3 hours ago.\n"
                "192.0.255.71 in default VRF was down 3 hours ago.\n192.0.255.17 in default VRF was down 3 hours ago."
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBFDPeersRegProtocols,
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
                                        "peerStatsDetail": {
                                            "role": "active",
                                            "apps": ["ospf"],
                                        },
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
                                        "peerStatsDetail": {
                                            "role": "active",
                                            "apps": ["bgp"],
                                        },
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
                {"peer_address": "192.0.255.7", "vrf": "default", "protocols": ["ospf"]},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "protocols": ["bgp"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBFDPeersRegProtocols,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {
                                        "status": "up",
                                        "peerStatsDetail": {
                                            "role": "active",
                                            "apps": ["ospf"],
                                        },
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
                                        "remoteDisc": 0,
                                        "peerStatsDetail": {
                                            "role": "active",
                                            "apps": ["bgp"],
                                        },
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
                {"peer_address": "192.0.255.7", "vrf": "default", "protocols": ["isis"]},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "protocols": ["isis"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "The following BFD peers are not configured or have non-registered protocol(s):\n"
                "{'192.0.255.7': {'default': ['isis']}, "
                "'192.0.255.70': {'MGMT': ['isis']}}"
            ],
        },
    },
    {
        "name": "failure-not-found",
        "test": VerifyBFDPeersRegProtocols,
        "eos_data": [
            {
                "vrfs": {
                    "default": {},
                    "MGMT": {},
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "protocols": ["isis"]},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "protocols": ["isis"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "The following BFD peers are not configured or have non-registered protocol(s):\n"
                "{'192.0.255.7': {'default': 'Not Configured'}, '192.0.255.70': {'MGMT': 'Not Configured'}}"
            ],
        },
    },
]
