# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.bgp.py
"""
from __future__ import annotations

from functools import wraps
from typing import Any
from unittest.mock import patch

from tests.units.anta_tests.test_case import test


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
    VerifyBGPRTCCount,
    VerifyBGPRTCState,
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
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'7.7.7.7': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}, 'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
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
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'2001:db8::cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}, 'BLAH': {'2001:db8::beef:cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
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
]
