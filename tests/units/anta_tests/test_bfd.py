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
from anta.tests.bfd import VerifyBFDPeersHealth  # noqa: E402
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
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
                    }
                }
            },
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": {"last_down": 2},
        "expected": {"result": "success"},
    },
    {
        "name": "success-no-peer",
        "test": VerifyBFDPeersHealth,
        "eos_data": [
            {"vrfs": {}},
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
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
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {
                "utcTime": 1703658481.8778424,
            },
        ],
        "inputs": {"last_down": 2},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers are not up:\n192.0.255.7 is down in default VRF with remote disc 0."],
        },
    },
    {
        "name": "failure-session-down-l3intf",
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
        "inputs": {"last_down": 2},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers are not up:\n192.0.255.7 is down in default VRF with peer layer3 interface Ethernet2 and remote disc 0."],
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
            "messages": ["Following BFD peers were down:\n192.0.255.7 in default VRF has remote disc 0 with peer layer3 interface Ethernet2."],
        },
    },
    {
        "name": "failure-last-down-l3intf",
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
                "utcTime": 1703667348.111288,
            },
        ],
        "inputs": {"last_down": 2},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers were down:\n192.0.255.7 in default VRF was down 3 hours ago with peer layer3 interface Ethernet2."],
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
                        },
                        "ipv6Neighbors": {},
                    }
                }
            },
            {
                "utcTime": 1703667348.111288,
            },
        ],
        "inputs": {"last_down": 2},
        "expected": {
            "result": "failure",
            "messages": ["Following BFD peers were down:\n192.0.255.7 in default VRF was down 3 hours ago."],
        },
    },
]
