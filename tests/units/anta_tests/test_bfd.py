# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.bfd.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.bfd import VerifyBFDPeersHealth, VerifyBFDPeersIntervals, VerifyBFDPeersRegProtocols, VerifyBFDSpecificPeers
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyBFDPeersIntervals, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
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
    (VerifyBFDPeersIntervals, "success-detection-time"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
            ]
        },
        "expected": {"result": "success"},
    },
    (VerifyBFDPeersIntervals, "failure-no-peer"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1200000, "operRxInterval": 1200000, "detectMult": 3, "detectTime": 3600000}}
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "CS", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
            ]
        },
        "expected": {"result": "failure", "messages": ["Peer: 192.0.255.7 VRF: CS - Not found", "Peer: 192.0.255.70 VRF: MGMT - Not found"]},
    },
    (VerifyBFDPeersIntervals, "failure-incorrect-timers"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1300000, "operRxInterval": 1200000, "detectMult": 4, "detectTime": 4000000}}
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {"": {"peerStatsDetail": {"operTxInterval": 120000, "operRxInterval": 120000, "detectMult": 5, "detectTime": 4000000}}}
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
                "Peer: 192.0.255.7 VRF: default - Incorrect Transmit interval - Expected: 1200 Actual: 1300",
                "Peer: 192.0.255.7 VRF: default - Incorrect Multiplier - Expected: 3 Actual: 4",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Transmit interval - Expected: 1200 Actual: 120",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Receive interval - Expected: 1200 Actual: 120",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Multiplier - Expected: 3 Actual: 5",
            ],
        },
    },
    (VerifyBFDPeersIntervals, "failure-incorrect-timers-with-detection-time"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {
                                "peerStats": {
                                    "": {"peerStatsDetail": {"operTxInterval": 1300000, "operRxInterval": 1200000, "detectMult": 4, "detectTime": 4000000}}
                                }
                            }
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {
                                "peerStats": {"": {"peerStatsDetail": {"operTxInterval": 120000, "operRxInterval": 120000, "detectMult": 5, "detectTime": 4000000}}}
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3, "detection_time": 3600},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - Incorrect Transmit interval - Expected: 1200 Actual: 1300",
                "Peer: 192.0.255.7 VRF: default - Incorrect Multiplier - Expected: 3 Actual: 4",
                "Peer: 192.0.255.7 VRF: default - Incorrect Detection Time - Expected: 3600 Actual: 4000",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Transmit interval - Expected: 1200 Actual: 120",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Receive interval - Expected: 1200 Actual: 120",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Multiplier - Expected: 3 Actual: 5",
                "Peer: 192.0.255.70 VRF: MGMT - Incorrect Detection Time - Expected: 3600 Actual: 4000",
            ],
        },
    },
    (VerifyBFDSpecificPeers, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"ipv4Neighbors": {"192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132}}}}},
                    "MGMT": {"ipv4Neighbors": {"192.0.255.70": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132}}}}},
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "default"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {"result": "success"},
    },
    (VerifyBFDSpecificPeers, "failure-no-peer"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"ipv4Neighbors": {"192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132}}}}},
                    "MGMT": {"ipv4Neighbors": {"192.0.255.71": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132}}}}},
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "CS"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {"result": "failure", "messages": ["Peer: 192.0.255.7 VRF: CS - Not found", "Peer: 192.0.255.70 VRF: MGMT - Not found"]},
    },
    (VerifyBFDSpecificPeers, "failure-session-down"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"ipv4Neighbors": {"192.0.255.7": {"peerStats": {"": {"status": "down", "remoteDisc": 108328132}}}}},
                    "MGMT": {"ipv4Neighbors": {"192.0.255.70": {"peerStats": {"": {"status": "down", "remoteDisc": 0}}}}},
                }
            }
        ],
        "inputs": {"bfd_peers": [{"peer_address": "192.0.255.7", "vrf": "default"}, {"peer_address": "192.0.255.70", "vrf": "MGMT"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - Session not properly established - State: down Remote Discriminator: 108328132",
                "Peer: 192.0.255.70 VRF: MGMT - Session not properly established - State: down Remote Discriminator: 0",
            ],
        },
    },
    (VerifyBFDPeersHealth, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}}
                        },
                        "ipv6Neighbors": {},
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.71": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}}
                        },
                        "ipv6Neighbors": {},
                    },
                }
            },
            {"utcTime": 1703667348.111288},
        ],
        "inputs": {"down_threshold": 2},
        "expected": {"result": "success"},
    },
    (VerifyBFDPeersHealth, "failure-no-peer"): {
        "eos_data": [
            {"vrfs": {"MGMT": {"ipv6Neighbors": {}, "ipv4Neighbors": {}}, "default": {"ipv6Neighbors": {}, "ipv4Neighbors": {}}}},
            {"utcTime": 1703658481.8778424},
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["No IPv4 BFD peers are configured for any VRF"]},
    },
    (VerifyBFDPeersHealth, "failure-session-down"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {"peerStats": {"": {"status": "down", "remoteDisc": 0, "lastDown": 1703657258.652725, "l3intf": ""}}},
                            "192.0.255.70": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}},
                        },
                        "ipv6Neighbors": {},
                    },
                    "MGMT": {
                        "ipv4Neighbors": {"192.0.255.71": {"peerStats": {"": {"status": "down", "remoteDisc": 0, "lastDown": 1703657258.652725, "l3intf": ""}}}},
                        "ipv6Neighbors": {},
                    },
                }
            },
            {"utcTime": 1703658481.8778424},
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - Session not properly established - State: down Remote Discriminator: 0",
                "Peer: 192.0.255.71 VRF: MGMT - Session not properly established - State: down Remote Discriminator: 0",
            ],
        },
    },
    (VerifyBFDPeersHealth, "failure-session-up-disc"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 0, "lastDown": 1703657258.652725, "l3intf": "Ethernet2"}}},
                            "192.0.255.71": {"peerStats": {"": {"status": "up", "remoteDisc": 0, "lastDown": 1703657258.652725, "l3intf": "Ethernet2"}}},
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {"utcTime": 1703658481.8778424},
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - Session not properly established - State: up Remote Discriminator: 0",
                "Peer: 192.0.255.71 VRF: default - Session not properly established - State: up Remote Discriminator: 0",
            ],
        },
    },
    (VerifyBFDPeersHealth, "failure-last-down"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}},
                            "192.0.255.71": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}},
                            "192.0.255.17": {"peerStats": {"": {"status": "up", "remoteDisc": 3940685114, "lastDown": 1703657258.652725, "l3intf": ""}}},
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {"utcTime": 1703667348.111288},
        ],
        "inputs": {"down_threshold": 4},
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - Session failure detected within the expected uptime threshold (3 hours ago)",
                "Peer: 192.0.255.71 VRF: default - Session failure detected within the expected uptime threshold (3 hours ago)",
                "Peer: 192.0.255.17 VRF: default - Session failure detected within the expected uptime threshold (3 hours ago)",
            ],
        },
    },
    (VerifyBFDPeersRegProtocols, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "ipv4Neighbors": {
                            "192.0.255.7": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132, "peerStatsDetail": {"role": "active", "apps": ["ospf"]}}}}
                        }
                    },
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {"peerStats": {"": {"status": "up", "remoteDisc": 108328132, "peerStatsDetail": {"role": "active", "apps": ["bgp"]}}}}
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
    (VerifyBFDPeersRegProtocols, "failure"): {
        "eos_data": [
            {
                "vrfs": {
                    "default": {"ipv4Neighbors": {"192.0.255.7": {"peerStats": {"": {"status": "up", "peerStatsDetail": {"role": "active", "apps": ["ospf"]}}}}}},
                    "MGMT": {
                        "ipv4Neighbors": {
                            "192.0.255.70": {"peerStats": {"": {"status": "up", "remoteDisc": 0, "peerStatsDetail": {"role": "active", "apps": ["bgp"]}}}}
                        }
                    },
                }
            }
        ],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "protocols": ["isis"]},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "protocols": ["isis", "ospf"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 192.0.255.7 VRF: default - `isis` routing protocol(s) not configured",
                "Peer: 192.0.255.70 VRF: MGMT - `isis`, `ospf` routing protocol(s) not configured",
            ],
        },
    },
    (VerifyBFDPeersRegProtocols, "failure-not-found"): {
        "eos_data": [{"vrfs": {"default": {}, "MGMT": {}}}],
        "inputs": {
            "bfd_peers": [
                {"peer_address": "192.0.255.7", "vrf": "default", "protocols": ["isis"]},
                {"peer_address": "192.0.255.70", "vrf": "MGMT", "protocols": ["isis"]},
            ]
        },
        "expected": {"result": "failure", "messages": ["Peer: 192.0.255.7 VRF: default - Not found", "Peer: 192.0.255.70 VRF: MGMT - Not found"]},
    },
}
