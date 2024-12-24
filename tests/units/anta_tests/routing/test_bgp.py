# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.routing.bgp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta.input_models.routing.bgp import BgpAddressFamily
from anta.tests.routing.bgp import (
    VerifyBGPAdvCommunities,
    VerifyBGPExchangedRoutes,
    VerifyBGPPeerASNCap,
    VerifyBGPPeerCount,
    VerifyBGPPeerDropStats,
    VerifyBGPPeerMD5Auth,
    VerifyBGPPeerMPCaps,
    VerifyBGPPeerRouteLimit,
    VerifyBGPPeerRouteRefreshCap,
    VerifyBGPPeersHealth,
    VerifyBGPPeerUpdateErrors,
    VerifyBgpRouteMaps,
    VerifyBGPSpecificPeers,
    VerifyBGPTimers,
    VerifyEVPNType2Route,
    _check_bgp_neighbor_capability,
)
from tests.units.anta_tests import test


@pytest.mark.parametrize(
    ("input_dict", "expected"),
    [
        pytest.param({"advertised": True, "received": True, "enabled": True}, True, id="all True"),
        pytest.param({"advertised": False, "received": True, "enabled": True}, False, id="advertised False"),
        pytest.param({"advertised": True, "received": False, "enabled": True}, False, id="received False"),
        pytest.param({"advertised": True, "received": True, "enabled": False}, False, id="enabled False"),
        pytest.param({"advertised": True, "received": True}, False, id="missing enabled"),
        pytest.param({}, False),
    ],
)
def test_check_bgp_neighbor_capability(input_dict: dict[str, bool], expected: bool) -> None:
    """Test check_bgp_neighbor_capability."""
    assert _check_bgp_neighbor_capability(input_dict) == expected


DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Idle",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.0.2": {
                                "peerState": "Idle",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Idle",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 2},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 2},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "num_peers": 1},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-peer-state-check-true",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.0.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 17, "nlrisAccepted": 17},
                            },
                            "10.1.255.0": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                            "10.1.255.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 2, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 3, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "num_peers": 1, "check_peer_state": True},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-vrf-not-configured",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.0.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 17, "nlrisAccepted": 17},
                            },
                            "10.1.255.0": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                            "10.1.255.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 2, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 3, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD", "num_peers": 2, "check_peer_state": True},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: PROD - VRF not configured",
            ],
        },
    },
    {
        "name": "failure-peer-state-check-true",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.0.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 17, "nlrisAccepted": 17},
                            },
                            "10.1.255.0": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                            "10.1.255.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 2, "check_peer_state": True},
                {"afi": "vpn-ipv4", "num_peers": 2, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 3, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "num_peers": 1, "check_peer_state": True},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: vpn-ipv4 - Expected: 2, Actual: 0",
            ],
        },
    },
    {
        "name": "failure-wrong-count-peer-state-check-true",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.0.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4MplsVpn": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 17, "nlrisAccepted": 17},
                            },
                            "10.1.255.0": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                            "10.1.255.2": {
                                "peerState": "Established",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 14, "nlrisAccepted": 14},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Established",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 3, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 3, "check_peer_state": True},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "num_peers": 2, "check_peer_state": True},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: evpn - Expected: 3, Actual: 2",
                "AFI: ipv4 SAFI: unicast VRF: DEV - Expected: 2, Actual: 1",
            ],
        },
    },
    {
        "name": "failure-wrong-count",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "peerState": "Idle",
                                "peerAsn": "65100",
                                "ipv4Unicast": {"afiSafiState": "advertised", "nlrisReceived": 0, "nlrisAccepted": 0},
                                "l2VpnEvpn": {"afiSafiState": "negotiated", "nlrisReceived": 42, "nlrisAccepted": 42},
                            },
                        },
                    },
                    "DEV": {
                        "vrf": "DEV",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "peerState": "Idle",
                                "peerAsn": "65120",
                                "ipv4Unicast": {"afiSafiState": "negotiated", "nlrisReceived": 4, "nlrisAccepted": 4},
                            }
                        },
                    },
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn", "num_peers": 2},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 2},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "num_peers": 2},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: evpn - Expected: 2, Actual: 1",
                "AFI: ipv4 SAFI: unicast VRF: default - Expected: 2, Actual: 1",
                "AFI: ipv4 SAFI: unicast VRF: DEV - Expected: 2, Actual: 1",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                            {
                                "peerAddress": "10.100.0.13",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"l2VpnEvpn": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                    "DEV": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "evpn"},
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "unicast", "vrf": "DEV"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-vrf-not-configured",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {},
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "sr-te", "vrf": "MGMT"},
                {"afi": "path-selection"},
                {"afi": "link-state"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default - VRF not configured",
                "AFI: ipv4 SAFI: sr-te VRF: MGMT - VRF not configured",
                "AFI: path-selection - VRF not configured",
                "AFI: link-state - VRF not configured",
            ],
        },
    },
    {
        "name": "failure-peer-not-found",
        "test": VerifyBGPPeersHealth,
        "eos_data": [{"vrfs": {"default": {"peerList": []}, "MGMT": {"peerList": []}}}],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "sr-te", "vrf": "MGMT"},
                {"afi": "path-selection"},
                {"afi": "link-state"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default - No peers found",
                "AFI: ipv4 SAFI: sr-te VRF: MGMT - No peers found",
                "AFI: path-selection - No peers found",
                "AFI: link-state - No peers found",
            ],
        },
    },
    {
        "name": "failure-session-not-established",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Idle",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                            },
                            {
                                "peerAddress": "10.100.0.13",
                                "state": "Idle",
                                "neighborCapabilities": {"multiprotocolCaps": {"dps": {"advertised": True, "received": True, "enabled": True}}},
                            },
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Active",
                                "neighborCapabilities": {"multiprotocolCaps": {"linkState": {"advertised": True, "received": True, "enabled": True}}},
                            },
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Active",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4SrTe": {"advertised": True, "received": True, "enabled": True}}},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "sr-te", "vrf": "MGMT"},
                {"afi": "path-selection"},
                {"afi": "link-state"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - Session state is not established - State: Idle",
                "AFI: ipv4 SAFI: sr-te VRF: MGMT Peer: 10.100.0.12 - Session state is not established - State: Active",
                "AFI: path-selection Peer: 10.100.0.13 - Session state is not established - State: Idle",
                "AFI: link-state Peer: 10.100.0.14 - Session state is not established - State: Active",
            ],
        },
    },
    {
        "name": "failure-afi-not-negotiated",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": False, "received": False, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                            {
                                "peerAddress": "10.100.0.13",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"dps": {"advertised": True, "received": False, "enabled": False}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"linkState": {"advertised": False, "received": False, "enabled": False}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4SrTe": {"advertised": False, "received": False, "enabled": False}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "sr-te", "vrf": "MGMT"},
                {"afi": "path-selection"},
                {"afi": "link-state"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - AFI/SAFI state is not negotiated - Advertised: False, Received: False, Enabled: True",
                "AFI: ipv4 SAFI: sr-te VRF: MGMT Peer: 10.100.0.12 - AFI/SAFI state is not negotiated - Advertised: False, Received: False, Enabled: False",
                "AFI: path-selection Peer: 10.100.0.13 - AFI/SAFI state is not negotiated - Advertised: True, Received: False, Enabled: False",
                "AFI: link-state Peer: 10.100.0.14 - AFI/SAFI state is not negotiated - Advertised: False, Received: False, Enabled: False",
            ],
        },
    },
    {
        "name": "failure-tcp-queues",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 4, "inputQueueLength": 2},
                            },
                            {
                                "peerAddress": "10.100.0.13",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"dps": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 1, "inputQueueLength": 1},
                            },
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"linkState": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 2, "inputQueueLength": 3},
                            },
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4SrTe": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 1, "inputQueueLength": 5},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "default"},
                {"afi": "ipv4", "safi": "sr-te", "vrf": "MGMT"},
                {"afi": "path-selection"},
                {"afi": "link-state"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - Session has non-empty message queues - InQ: 2, OutQ: 4",
                "AFI: ipv4 SAFI: sr-te VRF: MGMT Peer: 10.100.0.12 - Session has non-empty message queues - InQ: 5, OutQ: 1",
                "AFI: path-selection Peer: 10.100.0.13 - Session has non-empty message queues - InQ: 1, OutQ: 1",
                "AFI: link-state Peer: 10.100.0.14 - Session has non-empty message queues - InQ: 3, OutQ: 2",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                            {
                                "peerAddress": "10.100.0.13",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"l2VpnEvpn": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "evpn", "peers": ["10.100.0.13"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-peer-not-configured",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.20",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"l2VpnEvpn": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.10",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "evpn", "peers": ["10.100.0.13"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - Not configured",
                "AFI: evpn Peer: 10.100.0.13 - Not configured",
                "AFI: ipv4 SAFI: unicast VRF: MGMT Peer: 10.100.0.14 - Not configured",
            ],
        },
    },
    {
        "name": "failure-vrf-not-configured",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {},
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "evpn", "peers": ["10.100.0.13"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default - VRF not configured",
                "AFI: evpn - VRF not configured",
                "AFI: ipv4 SAFI: unicast VRF: MGMT - VRF not configured",
            ],
        },
    },
    {
        "name": "failure-session-not-established",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Idle",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Idle",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - Session state is not established - State: Idle",
                "AFI: ipv4 SAFI: unicast VRF: MGMT Peer: 10.100.0.14 - Session state is not established - State: Idle",
            ],
        },
    },
    {
        "name": "failure-afi-safi-not-negotiated",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": False, "received": False, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": False, "received": False, "enabled": False}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - AFI/SAFI state is not negotiated - Advertised: False, Received: False, Enabled: True",
                "AFI: ipv4 SAFI: unicast VRF: MGMT Peer: 10.100.0.14 - AFI/SAFI state is not negotiated - Advertised: False, Received: False, Enabled: False",
            ],
        },
    },
    {
        "name": "failure-afi-safi-not-correct",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"l2VpnEvpn": {"advertised": False, "received": False, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"l2VpnEvpn": {"advertised": False, "received": False, "enabled": False}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 0, "inputQueueLength": 0},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - AFI/SAFI state is not negotiated",
                "AFI: ipv4 SAFI: unicast VRF: MGMT Peer: 10.100.0.14 - AFI/SAFI state is not negotiated",
            ],
        },
    },
    {
        "name": "failure-tcp-queues",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.12",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 3, "inputQueueLength": 3},
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.14",
                                "state": "Established",
                                "neighborCapabilities": {"multiprotocolCaps": {"ipv4Unicast": {"advertised": True, "received": True, "enabled": True}}},
                                "peerTcpInfo": {"state": "ESTABLISHED", "outputQueueLength": 2, "inputQueueLength": 2},
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "peers": ["10.100.0.12"]},
                {"afi": "ipv4", "safi": "unicast", "vrf": "MGMT", "peers": ["10.100.0.14"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AFI: ipv4 SAFI: unicast VRF: default Peer: 10.100.0.12 - Session has non-empty message queues - InQ: 3, OutQ: 3",
                "AFI: ipv4 SAFI: unicast VRF: MGMT Peer: 10.100.0.14 - Session has non-empty message queues - InQ: 2, OutQ: 2",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPExchangedRoutes,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                            "192.0.254.5/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                            "192.0.254.5/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ],
                            },
                            "192.0.255.4/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ],
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ],
                            },
                            "192.0.255.4/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": True,
                                        },
                                    }
                                ],
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.5/32", "192.0.254.3/32"],
                    "received_routes": ["192.0.254.3/32", "192.0.255.4/32"],
                },
                {
                    "peer_address": "172.30.11.5",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32", "192.0.254.5/32"],
                    "received_routes": ["192.0.254.3/32", "192.0.255.4/32"],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-routes",
        "test": VerifyBGPExchangedRoutes,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "192.0.255.1",
                        "asn": "65001",
                        "bgpRouteEntries": {},
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "192.0.255.1",
                        "asn": "65001",
                        "bgpRouteEntries": {},
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "192.0.255.1",
                        "asn": "65001",
                        "bgpRouteEntries": {},
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "192.0.255.1",
                        "asn": "65001",
                        "bgpRouteEntries": {},
                    }
                }
            },
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32"],
                    "received_routes": ["192.0.255.3/32"],
                },
                {
                    "peer_address": "172.30.11.12",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.31/32"],
                    "received_routes": ["192.0.255.31/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.11 VRF: default Advertised route: 192.0.254.3/32 - Not found",
                "Peer: 172.30.11.11 VRF: default Received route: 192.0.255.3/32 - Not found",
                "Peer: 172.30.11.12 VRF: default Advertised route: 192.0.254.31/32 - Not found",
                "Peer: 172.30.11.12 VRF: default Received route: 192.0.255.31/32 - Not found",
            ],
        },
    },
    {
        "name": "failure-invalid-or-inactive-routes",
        "test": VerifyBGPExchangedRoutes,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": False,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                            "192.0.254.5/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": False,
                                        },
                                    }
                                ]
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": False,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                            "192.0.254.5/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": False,
                                            "active": True,
                                        },
                                    }
                                ]
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": False,
                                            "active": False,
                                        },
                                    }
                                ],
                            },
                            "192.0.255.4/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": False,
                                            "active": False,
                                        },
                                    }
                                ],
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "bgpRouteEntries": {
                            "192.0.254.3/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": False,
                                        },
                                    }
                                ],
                            },
                            "192.0.255.4/32": {
                                "bgpRoutePaths": [
                                    {
                                        "routeType": {
                                            "valid": True,
                                            "active": False,
                                        },
                                    }
                                ],
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32", "192.0.254.51/32"],
                    "received_routes": ["192.0.254.31/32", "192.0.255.4/32"],
                },
                {
                    "peer_address": "172.30.11.5",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.31/32", "192.0.254.5/32"],
                    "received_routes": ["192.0.254.3/32", "192.0.255.41/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default Advertised route: 192.0.254.3/32 - Valid: False, Active: True",
                "Peer: 172.30.11.1 VRF: default Advertised route: 192.0.254.51/32 - Not found",
                "Peer: 172.30.11.1 VRF: default Received route: 192.0.254.31/32 - Not found",
                "Peer: 172.30.11.1 VRF: default Received route: 192.0.255.4/32 - Valid: False, Active: False",
                "Peer: 172.30.11.5 VRF: default Advertised route: 192.0.254.31/32 - Not found",
                "Peer: 172.30.11.5 VRF: default Advertised route: 192.0.254.5/32 - Valid: False, Active: True",
                "Peer: 172.30.11.5 VRF: default Received route: 192.0.254.3/32 - Valid: True, Active: False",
                "Peer: 172.30.11.5 VRF: default Received route: 192.0.255.41/32 - Not found",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsLabels": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "capabilities": ["Ipv4 Unicast", "ipv4 Mpls labels"],
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                    "capabilities": ["ipv4 Unicast", "ipv4 MplsVpn"],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-vrf",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    }
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "MGMT",
                    "capabilities": ["ipv4 Unicast", "ipv4mplslabels"],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Peer: 172.30.11.1 VRF: MGMT - VRF not configured"],
        },
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "default",
                    "capabilities": ["ipv4Unicast", "L2 Vpn EVPN"],
                },
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "MGMT",
                    "capabilities": ["ipv4Unicast", "L2 Vpn EVPN"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.10 VRF: default - Not found",
                "Peer: 172.30.11.1 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "failure-missing-capabilities",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    }
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "capabilities": ["ipv4 Unicast", "L2VpnEVPN"],
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Peer: 172.30.11.1 VRF: default - l2VpnEvpn not found"],
        },
    },
    {
        "name": "failure-incorrect-capabilities",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": False,
                                            "received": False,
                                            "enabled": False,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": False,
                                            "received": True,
                                            "enabled": False,
                                        },
                                    },
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "l2VpnEvpn": {
                                            "advertised": True,
                                            "received": False,
                                            "enabled": False,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": False,
                                            "received": False,
                                            "enabled": True,
                                        },
                                    },
                                },
                            },
                            {
                                "peerAddress": "172.30.11.11",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": False,
                                            "received": False,
                                            "enabled": False,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": False,
                                            "received": False,
                                            "enabled": False,
                                        },
                                    },
                                },
                            },
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "capabilities": ["ipv4 unicast", "ipv4 mpls vpn", "L2 vpn EVPN"],
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                    "capabilities": ["ipv4unicast", "ipv4 mplsvpn", "L2vpnEVPN"],
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "MGMT",
                    "capabilities": ["Ipv4 Unicast", "ipv4 MPLSVPN", "L2 vpnEVPN"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - ipv4Unicast not negotiated - Advertised: False, Received: False, Enabled: False",
                "Peer: 172.30.11.1 VRF: default - ipv4MplsVpn not negotiated - Advertised: False, Received: True, Enabled: False",
                "Peer: 172.30.11.1 VRF: default - l2VpnEvpn not found",
                "Peer: 172.30.11.10 VRF: MGMT - ipv4Unicast not found",
                "Peer: 172.30.11.10 VRF: MGMT - ipv4MplsVpn not negotiated - Advertised: False, Received: False, Enabled: True",
                "Peer: 172.30.11.10 VRF: MGMT - l2VpnEvpn not negotiated - Advertised: True, Received: False, Enabled: False",
                "Peer: 172.30.11.11 VRF: MGMT - ipv4Unicast not negotiated - Advertised: False, Received: False, Enabled: False",
                "Peer: 172.30.11.11 VRF: MGMT - ipv4MplsVpn not negotiated - Advertised: False, Received: False, Enabled: False",
                "Peer: 172.30.11.11 VRF: MGMT - l2VpnEvpn not found",
            ],
        },
    },
    {
        "name": "success-strict",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsLabels": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "strict": True,
                    "capabilities": ["Ipv4 Unicast", "ipv4 Mpls labels"],
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                    "strict": True,
                    "capabilities": ["ipv4 Unicast", "ipv4 MplsVpn"],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-srict",
        "test": VerifyBGPPeerMPCaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsLabels": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        },
                                        "ipv4MplsVpn": {
                                            "advertised": False,
                                            "received": True,
                                            "enabled": True,
                                        },
                                    }
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "strict": True,
                    "capabilities": ["Ipv4 Unicast"],
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                    "strict": True,
                    "capabilities": ["ipv4MplsVpn", "L2vpnEVPN"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Mismatch - Expected: ipv4Unicast Actual: ipv4Unicast, ipv4MplsLabels",
                "Peer: 172.30.11.10 VRF: MGMT - Mismatch - Expected: ipv4MplsVpn, l2VpnEvpn Actual: ipv4Unicast, ipv4MplsVpn",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerASNCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "fourOctetAsnCap": {
                                        "advertised": True,
                                        "received": True,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "fourOctetAsnCap": {
                                        "advertised": True,
                                        "received": True,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPPeerASNCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            },
                        ]
                    }
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "default",
                }
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Peer: 172.30.11.10 VRF: default - Not found"],
        },
    },
    {
        "name": "failure-missing-capabilities",
        "test": VerifyBGPPeerASNCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4MplsLabels": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "172.30.11.1", "vrf": "default"},
                {"peer_address": "172.30.11.10", "vrf": "MGMT"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - 4-octet ASN capability not found",
                "Peer: 172.30.11.10 VRF: MGMT - 4-octet ASN capability not found",
            ],
        },
    },
    {
        "name": "failure-incorrect-capabilities",
        "test": VerifyBGPPeerASNCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "fourOctetAsnCap": {
                                        "advertised": False,
                                        "received": False,
                                        "enabled": False,
                                    },
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "neighborCapabilities": {
                                    "fourOctetAsnCap": {
                                        "advertised": True,
                                        "received": False,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "172.30.11.1", "vrf": "default"},
                {"peer_address": "172.30.11.10", "vrf": "MGMT"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - 4-octet ASN capability not negotiated - Advertised: False, Received: False, Enabled: False",
                "Peer: 172.30.11.10 VRF: MGMT - 4-octet ASN capability not negotiated - Advertised: True, Received: False, Enabled: True",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerRouteRefreshCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "routeRefreshCap": {
                                        "advertised": True,
                                        "received": True,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "neighborCapabilities": {
                                    "routeRefreshCap": {
                                        "advertised": True,
                                        "received": True,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "CS",
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPPeerRouteRefreshCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ip4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.12",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ip4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.12",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "CS",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.12 VRF: default - Not found",
                "Peer: 172.30.11.1 VRF: CS - Not found",
            ],
        },
    },
    {
        "name": "failure-missing-capabilities",
        "test": VerifyBGPPeerRouteRefreshCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "neighborCapabilities": {
                                    "multiprotocolCaps": {
                                        "ipv4Unicast": {
                                            "advertised": True,
                                            "received": True,
                                            "enabled": True,
                                        }
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "172.30.11.1", "vrf": "default"},
                {"peer_address": "172.30.11.11", "vrf": "CS"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Route refresh capability not found",
                "Peer: 172.30.11.11 VRF: CS - Route refresh capability not found",
            ],
        },
    },
    {
        "name": "failure-incorrect-capabilities",
        "test": VerifyBGPPeerRouteRefreshCap,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "neighborCapabilities": {
                                    "routeRefreshCap": {
                                        "advertised": False,
                                        "received": False,
                                        "enabled": False,
                                    },
                                },
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "neighborCapabilities": {
                                    "routeRefreshCap": {
                                        "advertised": True,
                                        "received": True,
                                        "enabled": True,
                                    },
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "172.30.11.1", "vrf": "default"},
                {"peer_address": "172.30.11.11", "vrf": "CS"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Route refresh capability not negotiated - Advertised: False, Received: False, Enabled: False",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerMD5Auth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "state": "Established",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "state": "Established",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "CS",
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPPeerMD5Auth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "state": "Established",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "state": "Established",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.12",
                    "vrf": "CS",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.10 VRF: default - Not found",
                "Peer: 172.30.11.12 VRF: CS - Not found",
            ],
        },
    },
    {
        "name": "failure-not-established-peer",
        "test": VerifyBGPPeerMD5Auth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "state": "Idle",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "state": "Idle",
                                "md5AuthEnabled": True,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Session state is not established - State: Idle",
                "Peer: 172.30.11.10 VRF: MGMT - Session state is not established - State: Idle",
            ],
        },
    },
    {
        "name": "failure-not-md5-peer",
        "test": VerifyBGPPeerMD5Auth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "state": "Established",
                            },
                            {
                                "peerAddress": "172.30.11.10",
                                "state": "Established",
                                "md5AuthEnabled": False,
                            },
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "state": "Established",
                                "md5AuthEnabled": False,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "MGMT",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Session does not have MD5 authentication enabled",
                "Peer: 172.30.11.11 VRF: MGMT - Session does not have MD5 authentication enabled",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            }
        ],
        "inputs": {"vxlan_endpoints": [{"address": "192.168.20.102", "vni": 10020}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-endpoints",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10010 aac1.ab5d.b41e": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "vxlan_endpoints": [
                {"address": "192.168.20.102", "vni": 10020},
                {"address": "aac1.ab5d.b41e", "vni": 10010},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-routes-ip",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                    "RD: 10.1.0.6:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {"vxlan_endpoints": [{"address": "192.168.20.102", "vni": 10020}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-routes-mac",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                    "RD: 10.1.0.6:500 mac-ip 10020 aac1.ab4e.bec2": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {"vxlan_endpoints": [{"address": "aac1.ab4e.bec2", "vni": 10020}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-routes-multiple-paths-ip",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                    "ecmp": True,
                                    "ecmpContributor": True,
                                    "ecmpHead": True,
                                },
                            },
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                    "ecmp": True,
                                    "ecmpContributor": True,
                                    "ecmpHead": False,
                                },
                            },
                        ]
                    },
                    "RD: 10.1.0.6:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {"vxlan_endpoints": [{"address": "192.168.20.102", "vni": 10020}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-routes-multiple-paths-mac",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                    "ecmp": True,
                                    "ecmpContributor": True,
                                    "ecmpHead": True,
                                },
                            },
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                    "ecmp": True,
                                    "ecmpContributor": True,
                                    "ecmpHead": False,
                                },
                            },
                        ]
                    },
                    "RD: 10.1.0.6:500 mac-ip 10020 aac1.ab4e.bec2": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": True,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {"vxlan_endpoints": [{"address": "aac1.ab4e.bec2", "vni": 10020}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-routes",
        "test": VerifyEVPNType2Route,
        "eos_data": [{"vrf": "default", "routerId": "10.1.0.3", "asn": 65120, "evpnRoutes": {}}],
        "inputs": {"vxlan_endpoints": [{"address": "192.168.20.102", "vni": 10020}]},
        "expected": {
            "result": "failure",
            "messages": ["Address: 192.168.20.102 VNI: 10020 - No EVPN Type-2 route"],
        },
    },
    {
        "name": "failure-path-not-active",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": True,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {"vxlan_endpoints": [{"address": "192.168.20.102", "vni": 10020}]},
        "expected": {
            "result": "failure",
            "messages": ["Address: 192.168.20.102 VNI: 10020 - No valid and active path"],
        },
    },
    {
        "name": "failure-multiple-endpoints",
        "test": VerifyEVPNType2Route,
        "eos_data": [
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10020 aac1.ab4e.bec2 192.168.20.102": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                        ]
                    },
                },
            },
            {
                "vrf": "default",
                "routerId": "10.1.0.3",
                "asn": 65120,
                "evpnRoutes": {
                    "RD: 10.1.0.5:500 mac-ip 10010 aac1.ab5d.b41e": {
                        "evpnRoutePaths": [
                            {
                                "routeType": {
                                    "active": False,
                                    "valid": False,
                                },
                            },
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "vxlan_endpoints": [
                {"address": "192.168.20.102", "vni": 10020},
                {"address": "aac1.ab5d.b41e", "vni": 10010},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["Address: 192.168.20.102 VNI: 10020 - No valid and active path", "Address: aa:c1:ab:5d:b4:1e VNI: 10010 - No valid and active path"],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPAdvCommunities,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "advertisedCommunities": {
                                    "standard": True,
                                    "extended": True,
                                    "large": True,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "advertisedCommunities": {
                                    "standard": True,
                                    "extended": True,
                                    "large": True,
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "MGMT",
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPAdvCommunities,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "advertisedCommunities": {
                                    "standard": True,
                                    "extended": True,
                                    "large": True,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "advertisedCommunities": {
                                    "standard": True,
                                    "extended": True,
                                    "large": True,
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.12",
                    "vrf": "MGMT",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.10 VRF: default - Not found",
                "Peer: 172.30.11.12 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "failure-not-correct-communities",
        "test": VerifyBGPAdvCommunities,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "advertisedCommunities": {
                                    "standard": False,
                                    "extended": False,
                                    "large": False,
                                },
                            }
                        ]
                    },
                    "CS": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.10",
                                "advertisedCommunities": {
                                    "standard": True,
                                    "extended": True,
                                    "large": False,
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                },
                {
                    "peer_address": "172.30.11.10",
                    "vrf": "CS",
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Standard: False, Extended: False, Large: False",
                "Peer: 172.30.11.10 VRF: CS - Standard: True, Extended: True, Large: False",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPTimers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "holdTime": 180,
                                "keepaliveTime": 60,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "holdTime": 180,
                                "keepaliveTime": 60,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "MGMT",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyBGPTimers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {"peerList": []},
                    "MGMT": {"peerList": []},
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "MGMT",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "default",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: MGMT - Not found",
                "Peer: 172.30.11.11 VRF: default - Not found",
            ],
        },
    },
    {
        "name": "failure-not-correct-timers",
        "test": VerifyBGPTimers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.1",
                                "holdTime": 160,
                                "keepaliveTime": 60,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "172.30.11.11",
                                "holdTime": 120,
                                "keepaliveTime": 40,
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "172.30.11.1",
                    "vrf": "default",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
                {
                    "peer_address": "172.30.11.11",
                    "vrf": "MGMT",
                    "hold_time": 180,
                    "keep_alive_time": 60,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 172.30.11.1 VRF: default - Hold time mismatch - Expected: 180, Actual: 160",
                "Peer: 172.30.11.11 VRF: MGMT - Hold time mismatch - Expected: 180, Actual: 120",
                "Peer: 172.30.11.11 VRF: MGMT - Keepalive time mismatch - Expected: 60, Actual: 40",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerDropStats,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 0,
                                    "inDropNhLocal": 0,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 0,
                                    "inDropNhLocal": 0,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "10.100.0.8",
                    "vrf": "default",
                    "drop_stats": ["prefixDroppedMartianV4", "prefixDroppedMaxRouteLimitViolatedV4", "prefixDroppedMartianV6"],
                },
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "drop_stats": ["inDropClusterIdLoop", "inDropOrigId", "inDropNhLocal"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-found",
        "test": VerifyBGPPeerDropStats,
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "10.100.0.8",
                    "vrf": "default",
                    "drop_stats": ["prefixDroppedMartianV4", "prefixDroppedMaxRouteLimitViolatedV4", "prefixDroppedMartianV6"],
                },
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "drop_stats": ["inDropClusterIdLoop", "inDropOrigId", "inDropNhLocal"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Not found",
                "Peer: 10.100.0.9 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "failure",
        "test": VerifyBGPPeerDropStats,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 1,
                                    "inDropNhLocal": 1,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 1,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 1,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 1,
                                    "inDropNhLocal": 1,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {
                    "peer_address": "10.100.0.8",
                    "vrf": "default",
                    "drop_stats": ["prefixDroppedMartianV4", "prefixDroppedMaxRouteLimitViolatedV4", "prefixDroppedMartianV6"],
                },
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "drop_stats": ["inDropClusterIdLoop", "inDropOrigId", "inDropNhLocal"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - prefixDroppedMartianV4: 1",
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - prefixDroppedMaxRouteLimitViolatedV4: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero NLRI drop statistics counter - inDropOrigId: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero NLRI drop statistics counter - inDropNhLocal: 1",
            ],
        },
    },
    {
        "name": "success-all-drop-stats",
        "test": VerifyBGPPeerDropStats,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 0,
                                    "inDropNhLocal": 0,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "dropStats": {
                                    "inDropAsloop": 0,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 0,
                                    "inDropNhLocal": 0,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default"},
                {"peer_address": "10.100.0.9", "vrf": "MGMT"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-all-drop-stats",
        "test": VerifyBGPPeerDropStats,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "dropStats": {
                                    "inDropAsloop": 3,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 1,
                                    "inDropNhLocal": 1,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 1,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 1,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "dropStats": {
                                    "inDropAsloop": 2,
                                    "inDropClusterIdLoop": 0,
                                    "inDropMalformedMpbgp": 0,
                                    "inDropOrigId": 1,
                                    "inDropNhLocal": 1,
                                    "inDropNhAfV6": 0,
                                    "prefixDroppedMartianV4": 0,
                                    "prefixDroppedMaxRouteLimitViolatedV4": 0,
                                    "prefixDroppedMartianV6": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default"},
                {"peer_address": "10.100.0.9", "vrf": "MGMT"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - inDropAsloop: 3",
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - inDropOrigId: 1",
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - inDropNhLocal: 1",
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - prefixDroppedMartianV4: 1",
                "Peer: 10.100.0.8 VRF: default - Non-zero NLRI drop statistics counter - prefixDroppedMaxRouteLimitViolatedV4: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero NLRI drop statistics counter - inDropAsloop: 2",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero NLRI drop statistics counter - inDropOrigId: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero NLRI drop statistics counter - inDropNhLocal: 1",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 0,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 0,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-found",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {"vrfs": {}},
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Not found",
                "Peer: 10.100.0.9 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "failure-errors",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 0,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "ipv4Unicast",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 1,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Non-zero update error counter - disabledAfiSafi: ipv4Unicast",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero update error counter - inUpdErrWithdraw: 1",
            ],
        },
    },
    {
        "name": "success-all-error-counters",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 0,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 0,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default"},
                {"peer_address": "10.100.0.9", "vrf": "MGMT"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-all-error-counters",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 1,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "ipv4Unicast",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 1,
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 1,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
                {
                    "peer_address": "10.100.0.9",
                    "vrf": "MGMT",
                    "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi", "inUpdErrDisableAfiSafi"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Non-zero update error counter - inUpdErrWithdraw: 1",
                "Peer: 10.100.0.8 VRF: default - Non-zero update error counter - disabledAfiSafi: ipv4Unicast",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero update error counter - inUpdErrWithdraw: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero update error counter - inUpdErrDisableAfiSafi: 1",
            ],
        },
    },
    {
        "name": "failure-all-not-found",
        "test": VerifyBGPPeerUpdateErrors,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "peerInUpdateErrors": {
                                    "inUpdErrIgnore": 0,
                                    "inUpdErrDisableAfiSafi": 0,
                                    "disabledAfiSafi": "ipv4Unicast",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "peerInUpdateErrors": {
                                    "inUpdErrWithdraw": 1,
                                    "inUpdErrIgnore": 0,
                                    "disabledAfiSafi": "None",
                                    "lastUpdErrTime": 0,
                                },
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi"]},
                {
                    "peer_address": "10.100.0.9",
                    "vrf": "MGMT",
                    "update_errors": ["inUpdErrWithdraw", "inUpdErrIgnore", "disabledAfiSafi", "inUpdErrDisableAfiSafi"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Non-zero update error counter - inUpdErrWithdraw: Not Found",
                "Peer: 10.100.0.8 VRF: default - Non-zero update error counter - disabledAfiSafi: ipv4Unicast",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero update error counter - inUpdErrWithdraw: 1",
                "Peer: 10.100.0.9 VRF: MGMT - Non-zero update error counter - inUpdErrDisableAfiSafi: Not Found",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBgpRouteMaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "routeMapInbound": "RM-MLAG-PEER-IN",
                                "routeMapOutbound": "RM-MLAG-PEER-OUT",
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.10",
                                "routeMapInbound": "RM-MLAG-PEER-IN",
                                "routeMapOutbound": "RM-MLAG-PEER-OUT",
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
                {"peer_address": "10.100.0.10", "vrf": "MGMT", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-route-map",
        "test": VerifyBgpRouteMaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "routeMapInbound": "RM-MLAG-PEER",
                                "routeMapOutbound": "RM-MLAG-PEER",
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.10",
                                "routeMapInbound": "RM-MLAG-PEER",
                                "routeMapOutbound": "RM-MLAG-PEER",
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
                {"peer_address": "10.100.0.10", "vrf": "MGMT", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: RM-MLAG-PEER",
                "Peer: 10.100.0.8 VRF: default - Outbound route-map mismatch - Expected: RM-MLAG-PEER-OUT, Actual: RM-MLAG-PEER",
                "Peer: 10.100.0.10 VRF: MGMT - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: RM-MLAG-PEER",
                "Peer: 10.100.0.10 VRF: MGMT - Outbound route-map mismatch - Expected: RM-MLAG-PEER-OUT, Actual: RM-MLAG-PEER",
            ],
        },
    },
    {
        "name": "failure-incorrect-inbound-map",
        "test": VerifyBgpRouteMaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "routeMapInbound": "RM-MLAG-PEER",
                                "routeMapOutbound": "RM-MLAG-PEER",
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.10",
                                "routeMapInbound": "RM-MLAG-PEER",
                                "routeMapOutbound": "RM-MLAG-PEER",
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "inbound_route_map": "RM-MLAG-PEER-IN"},
                {"peer_address": "10.100.0.10", "vrf": "MGMT", "inbound_route_map": "RM-MLAG-PEER-IN"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: RM-MLAG-PEER",
                "Peer: 10.100.0.10 VRF: MGMT - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: RM-MLAG-PEER",
            ],
        },
    },
    {
        "name": "failure-route-maps-not-configured",
        "test": VerifyBgpRouteMaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.10",
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
                {"peer_address": "10.100.0.10", "vrf": "MGMT", "inbound_route_map": "RM-MLAG-PEER-IN", "outbound_route_map": "RM-MLAG-PEER-OUT"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: Not Configured",
                "Peer: 10.100.0.8 VRF: default - Outbound route-map mismatch - Expected: RM-MLAG-PEER-OUT, Actual: Not Configured",
                "Peer: 10.100.0.10 VRF: MGMT - Inbound route-map mismatch - Expected: RM-MLAG-PEER-IN, Actual: Not Configured",
                "Peer: 10.100.0.10 VRF: MGMT - Outbound route-map mismatch - Expected: RM-MLAG-PEER-OUT, Actual: Not Configured",
            ],
        },
    },
    {
        "name": "failure-peer-not-found",
        "test": VerifyBgpRouteMaps,
        "eos_data": [
            {
                "vrfs": {
                    "default": {"peerList": []},
                    "MGMT": {"peerList": []},
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "inbound_route_map": "RM-MLAG-PEER-IN"},
                {"peer_address": "10.100.0.10", "vrf": "MGMT", "inbound_route_map": "RM-MLAG-PEER-IN"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Not found",
                "Peer: 10.100.0.10 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPPeerRouteLimit,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "maxTotalRoutes": 12000,
                                "totalRoutesWarnLimit": 10000,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "maxTotalRoutes": 10000,
                                "totalRoutesWarnLimit": 9000,
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "maximum_routes": 12000, "warning_limit": 10000},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "maximum_routes": 10000},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-peer-not-found",
        "test": VerifyBGPPeerRouteLimit,
        "eos_data": [
            {
                "vrfs": {
                    "default": {},
                    "MGMT": {},
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "maximum_routes": 12000, "warning_limit": 10000},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "maximum_routes": 10000, "warning_limit": 9000},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Not found",
                "Peer: 10.100.0.9 VRF: MGMT - Not found",
            ],
        },
    },
    {
        "name": "failure-incorrect-max-routes",
        "test": VerifyBGPPeerRouteLimit,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "maxTotalRoutes": 13000,
                                "totalRoutesWarnLimit": 11000,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                                "maxTotalRoutes": 11000,
                                "totalRoutesWarnLimit": 10000,
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "maximum_routes": 12000, "warning_limit": 10000},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "maximum_routes": 10000, "warning_limit": 9000},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Maximum routes mismatch - Expected: 12000, Actual: 13000",
                "Peer: 10.100.0.8 VRF: default - Maximum route warning limit mismatch - Expected: 10000, Actual: 11000",
                "Peer: 10.100.0.9 VRF: MGMT - Maximum routes mismatch - Expected: 10000, Actual: 11000",
                "Peer: 10.100.0.9 VRF: MGMT - Maximum route warning limit mismatch - Expected: 9000, Actual: 10000",
            ],
        },
    },
    {
        "name": "failure-routes-not-found",
        "test": VerifyBGPPeerRouteLimit,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.8",
                                "maxTotalRoutes": 12000,
                            }
                        ]
                    },
                    "MGMT": {
                        "peerList": [
                            {
                                "peerAddress": "10.100.0.9",
                            }
                        ]
                    },
                },
            },
        ],
        "inputs": {
            "bgp_peers": [
                {"peer_address": "10.100.0.8", "vrf": "default", "maximum_routes": 12000, "warning_limit": 10000},
                {"peer_address": "10.100.0.9", "vrf": "MGMT", "maximum_routes": 10000, "warning_limit": 9000},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.100.0.8 VRF: default - Maximum route warning limit mismatch - Expected: 10000, Actual: Not Found",
                "Peer: 10.100.0.9 VRF: MGMT - Maximum routes mismatch - Expected: 10000, Actual: Not Found",
                "Peer: 10.100.0.9 VRF: MGMT - Maximum route warning limit mismatch - Expected: 9000, Actual: Not Found",
            ],
        },
    },
]
