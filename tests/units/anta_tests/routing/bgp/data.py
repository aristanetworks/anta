"""Test inputs for anta.tests.routing.bgp"""

from typing import Any, Dict, List

INPUT_BGP_IPV4_UNICAST_STATE: List[Dict[str, Any]] = [
    {
        "name": "success-no-vrf",
        "eos_data": [{"vrfs": {}}],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-vrfs",
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
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            (
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'7.7.7.7': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}},"
                " 'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            )
        ],
    },
]

INPUT_BGP_IPV4_UNICAST_COUNT: List[Dict[str, Any]] = [
    {
        "name": "success-vrfs",
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
        "side_effect": {"template_params": [{"vrf": "BLAH"}, {"vrf": "BLIH"}], "number": 1},
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-count",
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
        "side_effect": {"template_params": [{"vrf": "BLAH"}], "number": 2},
        "expected_result": "failure",
        "expected_messages": ["Expecting 2 BGP peer in vrf BLAH and got 1"],
    },
    {
        "name": "failure-Established",
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
        "side_effect": {"template_params": [{"vrf": "BLAH"}], "number": 1},
        "expected_result": "failure",
        "expected_messages": ["The following IPv4 peers are not established: {'BLAH': {'8.8.8.8': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"],
    },
    {
        "name": "error-no-template-params",
        "eos_data": [{"vrfs": {}}],
        "side_effect": {"template_params": None, "number": 1},
        "expected_result": "error",
        "expected_messages": ["Command has template but no params were given"],
    },
    {
        "name": "error-empty-template-params",
        "eos_data": [{"vrfs": {}}],
        "side_effect": {"template_params": [], "number": 1},
        "expected_result": "error",
        "expected_messages": ["Test initialization error: Trying to save more data than there are commands for the test"],
    },
    {
        "name": "skipped-number",
        "eos_data": [{"vrfs": {}}],
        "side_effect": {"template_params": [{"vrf": "BLAH"}], "number": None},
        "expected_result": "skipped",
        "expected_messages": ["VerifyBGPIPv4UnicastCount could not run because number was not supplied"],
    },
]

INPUT_BGP_IPV6_UNICAST_STATE: List[Dict[str, Any]] = [
    {
        "name": "success-no-vrf",
        "eos_data": [{"vrfs": {}}],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "success-vrfs",
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
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": [
            (
                "Some IPv4 Unicast BGP Peer are not up: {'default': {'2001:db8::cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}, "
                "'BLAH': {'2001:db8::beef:cafe': {'peerState': 'Idle', 'inMsgQueue': 0, 'outMsgQueue': 0}}}"
            )
        ],
    },
]

INPUT_BGP_EVPN_STATE: List[Dict[str, Any]] = [
    {
        "name": "success",
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
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["The following EVPN peers are not established: ['7.7.7.7']"],
    },
]

INPUT_BGP_EVPN_COUNT: List[Dict[str, Any]] = [
    {
        "name": "success-vrfs",
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
        "side_effect": {"number": 1},
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-count",
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
        "side_effect": {"number": 2},
        "expected_result": "failure",
        "expected_messages": ["Expecting 2 BGP EVPN peers and got 1"],
    },
    {
        "name": "failure-Established",
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
        "side_effect": {"number": 1},
        "expected_result": "failure",
        "expected_messages": ["The following EVPN peers are not established: ['8.8.8.8']"],
    },
    {
        "name": "skipped-number",
        "eos_data": [{"vrfs": {}}],
        "side_effect": {"number": None},
        "expected_result": "skipped",
        "expected_messages": ["VerifyBGPEVPNCount could not run because number was not supplied."],
    },
]

INPUT_BGP_RTC_STATE: List[Dict[str, Any]] = [
    {
        "name": "success-vrfs",
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
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure",
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
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["The following RTC peers are not established: ['7.7.7.7']"],
    },
]

INPUT_BGP_RTC_COUNT: List[Dict[str, Any]] = [
    {
        "name": "success-vrfs",
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
        "side_effect": {"number": 1},
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-count",
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
        "side_effect": {"number": 2},
        "expected_result": "failure",
        "expected_messages": ["Expecting 2 BGP RTC peers and got 1"],
    },
    {
        "name": "failure-Established",
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
        "side_effect": {"number": 1},
        "expected_result": "failure",
        "expected_messages": ["The following RTC peers are not established: ['8.8.8.8']"],
    },
    {
        "name": "skipped-number",
        "eos_data": [{"vrfs": {}}],
        "side_effect": {"number": None},
        "expected_result": "skipped",
        "expected_messages": ["VerifyBGPRTCCount could not run because number was not supplied"],
    },
]
