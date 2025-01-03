# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.connectivity.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.connectivity import VerifyLLDPNeighbors, VerifyReachability
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
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

                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "success",
            "atomic_results": [
                {
                    "result": "success",
                    "description": "Destination 10.0.0.1 from 10.0.0.5 in VRF default",
                    "inputs": {"destination": "10.0.0.1", "source": "10.0.0.5", "vrf": "default", "repeat": 2, "size": 100, "df_bit": False},
                },
                {
                    "description": "Destination 10.0.0.2 from 10.0.0.5 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "10.0.0.5",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
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

                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "success",
            "atomic_results": [
                {
                    "result": "success",
                    "description": "Destination 10.0.0.1 from Management0 in VRF default",
                    "inputs": {"destination": "10.0.0.1", "source": "Management0", "vrf": "default", "repeat": 2, "size": 100, "df_bit": False},
                },
                {
                    "description": "Destination 10.0.0.2 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
    },
    {
        "name": "success-description",
        "test": VerifyReachability,
        "inputs": {
            "hosts": [
                {"description": "spine1 Ethernet49/1", "destination": "10.0.0.1", "source": "Management0"},
                {"destination": "10.0.0.2", "source": "Management0"},
            ]
        },
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.1 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "success",
            "atomic_results": [
                {
                    "result": "success",
                    "description": "Destination 10.0.0.1 (spine1 Ethernet49/1) from Management0 in VRF default",
                    "inputs": {
                        "description": "spine1 Ethernet49/1",
                        "destination": "10.0.0.1",
                        "source": "Management0",
                        "vrf": "default",
                        "repeat": 2,
                        "size": 100,
                        "df_bit": False,
                    },
                },
                {
                    "description": "Destination 10.0.0.2 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
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

                """,
                ],
            },
        ],
        "expected": {
            "result": "success",
            "atomic_results": [
                {
                    "description": "Destination 10.0.0.1 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.1",
                        "df_bit": False,
                        "repeat": 1,
                        "size": 100,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
    },
    {
        "name": "success-df-bit-size",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 5, "size": 1500, "df_bit": True}]},
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 172.20.20.6 : 1472(1500) bytes of data.
                1480 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.085 ms
                1480 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.020 ms
                1480 bytes from 10.0.0.1: icmp_seq=3 ttl=64 time=0.019 ms
                1480 bytes from 10.0.0.1: icmp_seq=4 ttl=64 time=0.018 ms
                1480 bytes from 10.0.0.1: icmp_seq=5 ttl=64 time=0.017 ms

                --- 10.0.0.1 ping statistics ---
                5 packets transmitted, 5 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.017/0.031/0.085/0.026 ms, ipg/ewma 0.061/0.057 ms""",
                ],
            },
        ],
        "expected": {
            "result": "success",
            "atomic_results": [
                {
                    "description": "Destination 10.0.0.1 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.1",
                        "df_bit": True,
                        "repeat": 5,
                        "size": 1500,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
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


                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "failure",
            "messages": ["Unreachable Destination 10.0.0.11 from 10.0.0.5 in VRF default"],
            "atomic_results": [
                {
                    "result": "failure",
                    "description": "Destination 10.0.0.11 from 10.0.0.5 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.11",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "10.0.0.5",
                        "vrf": "default",
                    },
                    "messages": ["Unreachable Destination 10.0.0.11 from 10.0.0.5 in VRF default"],
                },
                {
                    "description": "Destination 10.0.0.2 from 10.0.0.5 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "10.0.0.5",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
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


                """,
                ],
            },
            {
                "messages": [
                    """PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.
                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms
                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms

                --- 10.0.0.2 ping statistics ---
                2 packets transmitted, 2 received, 0% packet loss, time 0ms
                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms

                """,
                ],
            },
        ],
        "expected": {
            "result": "failure",
            "messages": ["Unreachable Destination 10.0.0.11 from Management0 in VRF default"],
            "atomic_results": [
                {
                    "description": "Destination 10.0.0.11 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.11",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "messages": ["Unreachable Destination 10.0.0.11 from Management0 in VRF default"],
                    "result": "failure",
                },
                {
                    "description": "Destination 10.0.0.2 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.2",
                        "df_bit": False,
                        "repeat": 2,
                        "size": 100,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "result": "success",
                },
            ],
        },
    },
    {
        "name": "failure-size",
        "test": VerifyReachability,
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 5, "size": 1501, "df_bit": True}]},
        "eos_data": [
            {
                "messages": [
                    """PING 10.0.0.1 (10.0.0.1) from 172.20.20.6 : 1473(1501) bytes of data.
                ping: local error: message too long, mtu=1500
                ping: local error: message too long, mtu=1500
                ping: local error: message too long, mtu=1500
                ping: local error: message too long, mtu=1500
                ping: local error: message too long, mtu=1500

                --- 10.0.0.1 ping statistics ---
                5 packets transmitted, 0 received, +5 errors, 100% packet loss, time 40ms
                """,
                ],
            },
        ],
        "expected": {
            "result": "failure",
            "messages": ["Unreachable Destination 10.0.0.1 from Management0 in VRF default"],
            "atomic_results": [
                {
                    "description": "Destination 10.0.0.1 from Management0 in VRF default",
                    "inputs": {
                        "destination": "10.0.0.1",
                        "df_bit": True,
                        "repeat": 5,
                        "size": 1501,
                        "source": "Management0",
                        "vrf": "default",
                    },
                    "messages": ["Unreachable Destination 10.0.0.1 from Management0 in VRF default"],
                    "result": "failure",
                },
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyLLDPNeighbors,
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
                            },
                        ],
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
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiple-neighbors",
        "test": VerifyLLDPNeighbors,
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
                            },
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
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-port-not-configured",
        "test": VerifyLLDPNeighbors,
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
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Port Ethernet2 (Neighbor: DC1-SPINE2, Neighbor Port: Ethernet1) - Port not found"]},
    },
    {
        "name": "failure-no-neighbor",
        "test": VerifyLLDPNeighbors,
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
                            },
                        ],
                    },
                    "Ethernet2": {"lldpNeighborInfo": []},
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {"result": "failure", "messages": ["Port Ethernet2 (Neighbor: DC1-SPINE2, Neighbor Port: Ethernet1) - No LLDP neighbors"]},
    },
    {
        "name": "failure-wrong-neighbor",
        "test": VerifyLLDPNeighbors,
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
                            },
                        ],
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
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {
            "result": "failure",
            "messages": ["Port Ethernet2 (Neighbor: DC1-SPINE2, Neighbor Port: Ethernet1) - Wrong LLDP neighbors: DC1-SPINE2/Ethernet2"],
        },
    },
    {
        "name": "failure-multiple",
        "test": VerifyLLDPNeighbors,
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
                            },
                        ],
                    },
                    "Ethernet2": {"lldpNeighborInfo": []},
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet3", "neighbor_device": "DC1-SPINE3", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Port Ethernet1 (Neighbor: DC1-SPINE1, Neighbor Port: Ethernet1) - Wrong LLDP neighbors: DC1-SPINE1/Ethernet2",
                "Port Ethernet2 (Neighbor: DC1-SPINE2, Neighbor Port: Ethernet1) - No LLDP neighbors",
                "Port Ethernet3 (Neighbor: DC1-SPINE3, Neighbor Port: Ethernet1) - Port not found",
            ],
        },
    },
    {
        "name": "failure-multiple-neighbors",
        "test": VerifyLLDPNeighbors,
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
                            },
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
                            },
                        ],
                    },
                },
            },
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE3", "neighbor_port": "Ethernet1"},
            ],
        },
        "expected": {
            "result": "failure",
            "messages": ["Port Ethernet1 (Neighbor: DC1-SPINE3, Neighbor Port: Ethernet1) - Wrong LLDP neighbors: DC1-SPINE1/Ethernet1, DC1-SPINE2/Ethernet1"],
        },
    },
]
