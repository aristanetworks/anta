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
    VerifyBGPIPv4UnicastPeers,
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
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'7.7.7.7': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}},"
                " 'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            ],
        },
    },
    {
        "name": "success-count-only",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 2, "PROD": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "success-peers",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "PROD": ["10.1.254.0"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "failure-count-only",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 3, "PROD": 2}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "failure", "messages": ["The following failure(s) occured: {'Wrong number of peers': {'default': 2, 'PROD': 1}}"]},
    },
    {
        "name": "failure-count-only-established",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 2, "PROD": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: {'Peer(s) issues': [{'default': {'10.1.255.6': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}]}"
            ],
        },
    },
    {
        "name": "failure-count-only-msg-queue",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 2, "PROD": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 100,
                                "outMsgQueue": 200,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: "
                "{'Peer(s) issues': [{'default': {'10.1.255.6': {'peerState': 'Established', 'inMsgQueue': 100, 'outMsgQueue': 200}}}]}"
            ],
        },
    },
    {
        "name": "failure-count-only-vrf-not-configured",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 2, "DEV": 1}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "failure", "messages": ["The following failure(s) occured: {'VRF(s) not configured': ['DEV']}"]},
    },
    {
        "name": "failure-count-only-multiple-failures",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": 2, "PROD": 2, "DEV": 5}},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
            {"vrfs": {}},
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: "
                "{'VRF(s) not configured': ['DEV'], "
                "'Wrong number of peers': {'PROD': 1}, "
                "'Peer(s) issues': [{'default': {'10.1.255.6': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}]}"
            ],
        },
    },
    {
        "name": "failure-peers",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "PROD": ["10.1.254.0", "10.1.254.2"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "failure", "messages": ["The following failure(s) occured: {'Peer(s) not configured': {'PROD': ['10.1.254.2']}}"]},
    },
    {
        "name": "failure-peers-established",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "PROD": ["10.1.254.0"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: {'Peer(s) issues': [{'PROD': {'10.1.254.0': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}]}"
            ],
        },
    },
    {
        "name": "failure-peers-msg-queue",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "PROD": ["10.1.254.0"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 100,
                                "outMsgQueue": 200,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: "
                "{'Peer(s) issues': [{'PROD': {'10.1.254.0': {'peerState': 'Established', 'inMsgQueue': 100, 'outMsgQueue': 200}}}]}"
            ],
        },
    },
    {
        "name": "failure-peers-vrf-not-configured",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "DEV": ["10.1.254.0"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 100,
                                "outMsgQueue": 200,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
        ],
        "expected": {"result": "failure", "messages": ["The following failure(s) occured: {'VRF(s) not configured': ['DEV']}"]},
    },
    {
        "name": "failure-peers-multiple-failures",
        "test": VerifyBGPIPv4UnicastPeers,
        "inputs": {"vrfs": {"default": ["10.1.255.4", "10.1.255.6"], "PROD": ["10.1.254.0", "10.1.254.2"], "DEV": ["10.1.254.0"]}, "count_only": False},
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "vrf": "default",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.255.4": {
                                "description": "DC1-SPINE1_Ethernet2",
                                "version": 4,
                                "msgReceived": 8269,
                                "msgSent": 8272,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694094940.980473,
                                "underMaintenance": False,
                                "peerState": "Established",
                            },
                            "10.1.255.6": {
                                "description": "DC1-SPINE2_Ethernet2",
                                "version": 4,
                                "msgReceived": 6504,
                                "msgSent": 6509,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65100",
                                "prefixAccepted": 14,
                                "prefixReceived": 14,
                                "upDownTime": 1694038182.927187,
                                "underMaintenance": False,
                                "peerState": "Idle",
                            },
                        },
                    }
                }
            },
            {
                "vrfs": {
                    "PROD": {
                        "vrf": "PROD",
                        "routerId": "10.1.0.4",
                        "asn": "65120",
                        "peers": {
                            "10.1.254.0": {
                                "description": "DC1-LEAF1A",
                                "version": 4,
                                "msgReceived": 7832,
                                "msgSent": 7809,
                                "inMsgQueue": 0,
                                "outMsgQueue": 0,
                                "asn": "65120",
                                "prefixAccepted": 4,
                                "prefixReceived": 4,
                                "upDownTime": 1694127109.561448,
                                "underMaintenance": False,
                                "peerState": "Established",
                            }
                        },
                    }
                }
            },
            {"vrfs": {}},
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following failure(s) occured: "
                "{'VRF(s) not configured': ['DEV'], "
                "'Peer(s) issues': [{'default': {'10.1.255.6': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}], "
                "'Peer(s) not configured': {'PROD': ['10.1.254.2']}}"
            ],
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
]
