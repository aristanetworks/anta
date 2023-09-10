# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.bgp.py
"""
# pylint: disable=C0302
from __future__ import annotations

from functools import wraps
from typing import Any
from unittest.mock import patch

from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611


# Patching the decorator
# Thanks - https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc
def mock_decorator(*args, **kwargs):  # type: ignore
    """Decorate by doing nothing."""
    # pylint: disable=W0613

    def decorator(f):  # type: ignore
        @wraps(f)
        def decorated_function(*args, **kwargs):  # type: ignore
            return f(*args, **kwargs)

        return decorated_function

    return decorator


patch("anta.decorators.check_bgp_family_enable", mock_decorator).start()

# pylint: disable=C0413
# because of the patch above
from anta.tests.routing.bgp import (  # noqa: E402
    VerifyBGPEVPNCount,
    VerifyBGPEVPNState,
    VerifyBGPIPv4UnicastCount,
    VerifyBGPIPv4UnicastState,
    VerifyBGPIPv6UnicastState,
    VerifyBGPPeerCount,
    VerifyBGPPeersHealth,
    VerifyBGPRTCCount,
    VerifyBGPRTCState,
    VerifyBGPSpecificPeers,
)

DATA: list[dict[str, Any]] = [
    {
        "name": "success-no-vrf",
        "test": VerifyBGPIPv4UnicastState,
        "eos_data": [{"vrfs": {}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPIPv4UnicastState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBGPIPv4UnicastState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'7.7.7.7': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}},"
                " 'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            ],
        },
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPIPv4UnicastCount,
        "inputs": {"vrfs": {"BLAH": 1, "BLIH": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            },
            {
                "vrfs": {
                    "BLIH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "5.5.5.5": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLIH",
                        "asn": "666",
                    },
                }
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "failure-count",
        "test": VerifyBGPIPv4UnicastCount,
        "inputs": {"vrfs": {"BLAH": 2}},
        "eos_data": [
            {
                "vrfs": {
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "expected": {"result": "failure", "messages": ["Expecting 2 BGP peer(s) in vrf BLAH but got 1 peer(s)"]},
    },
    {
        "name": "failure-Established",
        "test": VerifyBGPIPv4UnicastCount,
        "inputs": {"vrfs": {"BLAH": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "expected": {
            "result": "failure",
            "messages": ["The following IPv4 peer(s) are not established: {'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"],
        },
    },
    {
        "name": "success-no-vrf",
        "test": VerifyBGPIPv6UnicastState,
        "eos_data": [{"vrfs": {}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPIPv6UnicastState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "2001:db8::cafe": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "2001:db8::beef::cafe": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBGPIPv6UnicastState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "2001:db8::cafe": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                    "BLAH": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "2001:db8::beef:cafe": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "BLAH",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'2001:db8::cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}},"
                " 'BLAH': {'2001:db8::beef:cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBGPEVPNState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBGPEVPNState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following EVPN peers are not established: ['7.7.7.7']"]},
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPEVPNCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": {"number": 1},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-count",
        "test": VerifyBGPEVPNCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 42,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": "failure", "messages": ["Expecting 2 BGP EVPN peers and got 1"]},
    },
    {
        "name": "failure-Established",
        "test": VerifyBGPEVPNCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": {"number": 1},
        "expected": {"result": "failure", "messages": ["The following EVPN peers are not established: ['8.8.8.8']"]},
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPRTCState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 42,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    }
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyBGPRTCState,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "7.7.7.7": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206265.363882,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "65000",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following RTC peers are not established: ['7.7.7.7']"]},
    },
    {
        "name": "success-vrfs",
        "test": VerifyBGPRTCCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 42,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": {"number": 1},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-count",
        "test": VerifyBGPRTCCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 42,
                                "prefixAccepted": 0,
                                "peerState": "Established",
                                "outMsgQueue": 42,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "inputs": {"number": 2},
        "expected": {"result": "failure", "messages": ["Expecting 2 BGP RTC peers and got 1"]},
    },
    {
        "name": "failure-Established",
        "test": VerifyBGPRTCCount,
        "inputs": {"number": 1},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "routerId": "3.3.3.3",
                        "peers": {
                            "8.8.8.8": {
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "peerStateIdleReason": "NoInterface",
                                "prefixReceived": 0,
                                "upDownTime": 1683206557.031003,
                                "version": 4,
                                "msgReceived": 0,
                                "prefixAccepted": 0,
                                "peerState": "Idle",
                                "outMsgQueue": 0,
                                "underMaintenance": False,
                                "asn": "12345",
                            }
                        },
                        "vrf": "default",
                        "asn": "666",
                    },
                }
            }
        ],
        "expected": {"result": "failure", "messages": ["The following RTC peers are not established: ['8.8.8.8']"]},
    },
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
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 2}]},
        "expected": {"result": "success"},
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
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default", "num_peers": 3}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': 'Expected: 3, Actual: 2'}}]"]},
    },
    {
        "name": "failure-no-peers",
        "test": VerifyBGPPeerCount,
        "eos_data": [{"vrfs": {"default": {"vrf": "default", "routerId": "10.1.0.3", "asn": "65120", "peers": {}}}}],
        "inputs": {"address_families": [{"afi": "ipv6", "safi": "unicast", "vrf": "default", "num_peers": 3}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'default': 'Expected: 3, Actual: 0'}}]"]},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyBGPPeerCount,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"address_families": [{"afi": "ipv6", "safi": "multicast", "vrf": "DEV", "num_peers": 3}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv6', 'safi': 'multicast', 'vrfs': {'DEV': 'Not Configured'}}]"]},
    },
    {
        "name": "success-vrf-all",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "all", "num_peers": 3}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-vrf-all",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "all", "num_peers": 5}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'all': 'Expected: 5, Actual: 3'}}]"]},
    },
    {
        "name": "success-multiple-afi",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD", "num_peers": 2},
                {"afi": "evpn", "num_peers": 2},
            ]
        },
        "expected": {
            "result": "success",
        },
    },
    {
        "name": "failure-multiple-afi",
        "test": VerifyBGPPeerCount,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {"vrfs": {}},
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD", "num_peers": 3},
                {"afi": "evpn", "num_peers": 3},
                {"afi": "ipv6", "safi": "unicast", "vrf": "default", "num_peers": 3},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'PROD': 'Expected: 3, Actual: 2'}}, "
                "{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'default': 'Not Configured'}}, "
                "{'afi': 'evpn', 'vrfs': {'default': 'Expected: 3, Actual: 2'}}"
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
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-issues",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': {'10.1.255.0': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}}]"
            ],
        },
    },
    {
        "name": "success-vrf-all",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "all"}]},
        "expected": {
            "result": "success",
        },
    },
    {
        "name": "failure-issues-vrf-all",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 100,
                                "outMsgQueue": 200,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    },
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "all"}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': {'10.1.255.0': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}, "
                "'PROD': {'192.168.1.11': {'peerState': 'Established', 'inMsgQueue': 100, 'outMsgQueue': 200}}}}]"
            ],
        },
    },
    {
        "name": "failure-not-configured",
        "test": VerifyBGPPeersHealth,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "DEV"}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'DEV': 'Not Configured'}}]"]},
    },
    {
        "name": "failure-no-peers",
        "test": VerifyBGPPeersHealth,
        "eos_data": [{"vrfs": {"default": {"vrf": "default", "routerId": "10.1.0.3", "asn": "65120", "peers": {}}}}],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "multicast"}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'default': 'No Peers'}}]"]},
    },
    {
        "name": "success-multiple-afi",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD"},
                {"afi": "evpn"},
            ]
        },
        "expected": {
            "result": "success",
        },
    },
    {
        "name": "failure-multiple-afi",
        "test": VerifyBGPPeersHealth,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 10,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {"vrfs": {}},
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD"},
                {"afi": "evpn"},
                {"afi": "ipv6", "safi": "unicast", "vrf": "default"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': "
                "{'PROD': {'192.168.1.11': {'peerState': 'Established', 'inMsgQueue': 10, 'outMsgQueue': 0}}}}, "
                "{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'default': 'Not Configured'}}, "
                "{'afi': 'evpn', 'vrfs': {'default': {'10.1.0.2': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
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
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default", "peers": ["10.1.255.0", "10.1.255.2"]}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-issues",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.0": {
                                "description": "DC1-SPINE1_Ethernet1",
                                "version": 4,
                                "msgReceived": 0,
                                "msgSent": 0,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266295.098931,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                            "10.1.255.2": {
                                "description": "DC1-SPINE2_Ethernet1",
                                "version": 4,
                                "msgReceived": 3759,
                                "msgSent": 3757,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694266296.367261,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            }
        ],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "default", "peers": ["10.1.255.0", "10.1.255.2"]}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'default': {'10.1.255.0': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}}]"
            ],
        },
    },
    {
        "name": "failure-not-configured",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [{"vrfs": {}}],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "unicast", "vrf": "DEV", "peers": ["10.1.255.0"]}]},
        "expected": {"result": "failure", "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': {'DEV': 'Not Configured'}}]"]},
    },
    {
        "name": "failure-no-peers",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [{"vrfs": {"default": {"vrf": "default", "routerId": "10.1.0.3", "asn": "65120", "peers": {}}}}],
        "inputs": {"address_families": [{"afi": "ipv4", "safi": "multicast", "peers": ["10.1.255.0"]}]},
        "expected": {
            "result": "failure",
            "messages": ["Failures: [{'afi': 'ipv4', 'safi': 'multicast', 'vrfs': {'default': {'10.1.255.0': {'peerNotFound': True}}}}]"],
        },
    },
    {
        "name": "success-multiple-afi",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD", "peers": ["10.1.254.1", "192.168.1.11"]},
                {"afi": "evpn", "peers": ["10.1.0.1", "10.1.0.2"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-multiple-afi",
        "test": VerifyBGPSpecificPeers,
        "eos_data": [
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.1": {
                                "description": "DC1-LEAF1B",
                                "version": 4,
                                "msgReceived": 3777,
                                "msgSent": 3764,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 2,
                                "prefixReceived": 2,
                                "upDownTime": 1694266296.659891,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "192.168.1.11": {
                                "description": "K8S-CLUSTER1",
                                "version": 4,
                                "msgReceived": 6417,
                                "msgSent": 7546,
                                "inMsgQueue": 10,
                                "outMsgQueue": 0,
                                "asn": "65000",
                                "prefixAccepted": 1,
                                "prefixReceived": 1,
                                "upDownTime": 1694266329.978035,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {"vrfs": {}},
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.3",
                        "asn": "65120",
                        "peers": {
                            "10.1.0.1": {
                                "description": "DC1-SPINE1",
                                "version": 4,
                                "msgReceived": 3894,
                                "msgSent": 3897,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266296.584472,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.0.2": {
                                "description": "DC1-SPINE2",
                                "version": 4,
                                "msgReceived": 3893,
                                "msgSent": 3902,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 0,
                                "prefixReceived": 0,
                                "upDownTime": 1694266297.433896,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                        },
                    }
                }
            },
        ],
        "inputs": {
            "address_families": [
                {"afi": "ipv4", "safi": "unicast", "vrf": "PROD", "peers": ["10.1.254.1", "192.168.1.11"]},
                {"afi": "evpn", "peers": ["10.1.0.1", "10.1.0.2"]},
                {"afi": "ipv6", "safi": "unicast", "vrf": "default", "peers": ["10.1.0.1", "10.1.0.2"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Failures: [{'afi': 'ipv4', 'safi': 'unicast', 'vrfs': "
                "{'PROD': {'192.168.1.11': {'peerState': 'Established', 'inMsgQueue': 10, 'outMsgQueue': 0}}}}, "
                "{'afi': 'ipv6', 'safi': 'unicast', 'vrfs': {'default': 'Not Configured'}}, "
                "{'afi': 'evpn', 'vrfs': {'default': {'10.1.0.2': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            ],
        },
    },
]
