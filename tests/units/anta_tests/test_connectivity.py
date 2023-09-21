# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.connectivity.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.connectivity import VerifyLLDPNeighbors, VerifyReachability
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success-ip",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "10.0.0.5"}, {"destination": "10.0.0.2", "source": "10.0.0.5"}]},
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.1 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "success-interface",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0"}, {"destination": "10.0.0.2", "source": "Management0"}]},
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.1 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "success-repeat",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 1}]},
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms

                --- 10.0.0.1 ping statistics ---
                1 packets transmitted, 1 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "failure-ip",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.11", "source": "10.0.0.5"}, {"destination": "10.0.0.2", "source": "10.0.0.5"}]},
        "eos_data": [
            {
                "messages": [
                    """ping: sendmsg: Network is unreachable
                ping: sendmsg: Network is unreachable
                PING 10.0.0.11 (10.0.0.11) from 10.0.0.5 : 72(100) bytes of data.

                --- 10.0.0.11 ping statistics ---
                2 packets transmitted, 0 received, 100% packet loss, time 10ms


                """
                ]
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
        ],
        "expected": {"result": "failure", "messages": ["Connectivity test failed for the following source-destination pairs: [('10.0.0.5', '10.0.0.11')]"]},
    },
    {
        "name": "failure-interface",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.11", "source": "Management0"}, {"destination": "10.0.0.2", "source": "Management0"}]},
        "eos_data": [
            {
                "messages": [
                    """ping: sendmsg: Network is unreachable
                ping: sendmsg: Network is unreachable
                PING 10.0.0.11 (10.0.0.11) from 10.0.0.5 : 72(100) bytes of data.

                --- 10.0.0.11 ping statistics ---
                2 packets transmitted, 0 received, 100% packet loss, time 10ms


                """
                ]
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """
                ]
            },
        ],
        "expected": {"result": "failure", "messages": ["Connectivity test failed for the following source-destination pairs: [('Management0', '10.0.0.11')]"]},
    },
    {
        "name": "success",
        "test": VerifyLLDPNeighbors,
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "eos_data": [
            {
                "lldpNeighbors": {
                    "Ethernet1": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73a0.fc18",
                                "systemName": "DC1-SPINE1",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet1"',
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet1",
                                },
                            }
                        ]
                    },
                    "Ethernet2": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73f7.d138",
                                "systemName": "DC1-SPINE2",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet1"',
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-neighbor",
        "test": VerifyLLDPNeighbors,
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "eos_data": [
            {
                "lldpNeighbors": {
                    "Ethernet1": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73a0.fc18",
                                "systemName": "DC1-SPINE1",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet1"',
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet1",
                                },
                            }
                        ]
                    },
                    "Ethernet2": {"lldpNeighborInfo": []},
                }
            }
        ],
        "expected": {"result": "failure", "messages": ["The following port(s) have no LLDP neighbor: ['Ethernet2']"]},
    },
    {
        "name": "failure-wrong-neighbor",
        "test": VerifyLLDPNeighbors,
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "eos_data": [
            {
                "lldpNeighbors": {
                    "Ethernet1": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73a0.fc18",
                                "systemName": "DC1-SPINE1",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet1"',
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet1",
                                },
                            }
                        ]
                    },
                    "Ethernet2": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73f7.d138",
                                "systemName": "DC1-SPINE2",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet2"',
                                    "interfaceId_v2": "Ethernet2",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "expected": {"result": "failure", "messages": ["The following port(s) have the wrong LLDP neighbor: ['Ethernet2']"]},
    },
    {
        "name": "failure-wrong-and-no-neighbor",
        "test": VerifyLLDPNeighbors,
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "eos_data": [
            {
                "lldpNeighbors": {
                    "Ethernet1": {
                        "lldpNeighborInfo": [
                            {
                                "chassisIdType": "macAddress",
                                "chassisId": "001c.73a0.fc18",
                                "systemName": "DC1-SPINE1",
                                "neighborInterfaceInfo": {
                                    "interfaceIdType": "interfaceName",
                                    "interfaceId": '"Ethernet2"',
                                    "interfaceId_v2": "Ethernet2",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet1",
                                },
                            }
                        ]
                    },
                    "Ethernet2": {"lldpNeighborInfo": []},
                }
            }
        ],
        "expected": {
            "result": "failure",
            "messages": [
                "The following port(s) have no LLDP neighbor: ['Ethernet2']",
                "The following port(s) have the wrong LLDP neighbor: ['Ethernet1']",
            ],
        },
    },
]
