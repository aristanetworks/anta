# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.bgp.py
"""
# pylint: disable=C0302
from __future__ import annotations

from typing import Any

# pylint: disable=C0413
# because of the patch above
from anta.tests.routing.bgp import VerifyBGPExchangedRoutes, VerifyBGPPeerCount, VerifyBGPPeersHealth, VerifyBGPSpecificPeers  # noqa: E402
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

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
                            }
                        },
                    }
                }
            },
        ],
        "inputs": {
            "bgp_neighbors": [
                {
                    "neighbor": "172.30.11.1",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32"],
                    "received_routes": ["192.0.254.3/32"],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-routes",
        "test": VerifyBGPExchangedRoutes,
        "eos_data": [
            {"vrfs": {"default": {"vrf": "default", "routerId": "192.0.255.1", "asn": "65001", "bgpRouteEntries": {}}}},
            {"vrfs": {"default": {"vrf": "default", "routerId": "192.0.255.1", "asn": "65001", "bgpRouteEntries": {}}}},
        ],
        "inputs": {
            "bgp_neighbors": [
                {
                    "neighbor": "172.30.11.11",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32"],
                    "received_routes": ["192.0.255.3/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["BGP routes are not found for neighbor `172.30.11.11`."],
        },
    },
    {
        "name": "failure-no-neighbor",
        "test": VerifyBGPExchangedRoutes,
        "eos_data": [{"vrfs": {}}, {"vrfs": {}}],
        "inputs": {
            "bgp_neighbors": [
                {
                    "neighbor": "172.30.11.11",
                    "vrf": "MGMT",
                    "advertised_routes": ["192.0.254.3/32"],
                    "received_routes": ["192.0.255.3/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["BGP neighbor 172.30.11.11 is not configured for `MGMT` VRF."],
        },
    },
    {
        "name": "failure-missing-routes",
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
                            }
                        },
                    }
                }
            },
        ],
        "inputs": {
            "bgp_neighbors": [
                {
                    "neighbor": "172.30.11.1",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.31/32"],
                    "received_routes": ["192.0.255.31/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BGP neighbors are not ok: {'advertised_routes': {'default': {'172.30.11.1': {'missing_routes': ['192.0.254.31/32']}}}, "
                "'revevied_routes': {'default': {'172.30.11.1': {'missing_routes': ['192.0.255.31/32']}}}}"
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
                                            "active": False,
                                        },
                                    }
                                ],
                            }
                        },
                    }
                }
            },
        ],
        "inputs": {
            "bgp_neighbors": [
                {
                    "neighbor": "172.30.11.1",
                    "vrf": "default",
                    "advertised_routes": ["192.0.254.3/32"],
                    "received_routes": ["192.0.255.3/32"],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Following BGP neighbors are not ok: {'advertised_routes': {'default': {'172.30.11.1': {'invalid_or_inactive_routes': ['192.0.254.3/32']}}}, "
                "'revevied_routes': {'default': {'172.30.11.1': {'missing_routes': ['192.0.255.3/32']}}}}"
            ],
        },
    },
]
