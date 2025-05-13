# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.connectivity.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.connectivity import VerifyLLDPNeighbors, VerifyReachability
from tests.units.anta_tests import AntaUnitTest, test

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = type


AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
    (VerifyReachability, "success-ip"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "10.0.0.5"}, {"destination": "10.0.0.2", "source": "10.0.0.5"}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.1 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
            {
                "messages": [
                    "PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.2 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-expected-unreachable"): {
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.\n\n                --- 10.0.0.1 ping statistics ---\n"
                    "                2 packets transmitted, 0 received, 100% packet loss, time 10ms\n                "
                ]
            }
        ],
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "10.0.0.5", "reachable": False}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-ipv6"): {
        "eos_data": [
            {
                "messages": [
                    "PING fd12:3456:789a:1::2(fd12:3456:789a:1::2) from fd12:3456:789a:1::1 : 52 data bytes\n                60 bytes from fd12:3456:789a:1::2:"
                    " icmp_seq=1 ttl=64 time=0.097 ms\n                60 bytes from fd12:3456:789a:1::2: icmp_seq=2 ttl=64 time=0.033 ms\n\n"
                    "                --- fd12:3456:789a:1::2 ping statistics ---\n                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n"
                    "                rtt min/avg/max/mdev = 0.033/0.065/0.097/0.032 ms, ipg/ewma 0.148/0.089 ms\n                "
                ]
            }
        ],
        "inputs": {"hosts": [{"destination": "fd12:3456:789a:1::2", "source": "fd12:3456:789a:1::1"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-ipv6-vlan"): {
        "eos_data": [
            {
                "messages": [
                    "PING fd12:3456:789a:1::2(fd12:3456:789a:1::2) 52 data bytes\n                60 bytes from fd12:3456:789a:1::2: "
                    "icmp_seq=1 ttl=64 time=0.094 ms\n                60 bytes from fd12:3456:789a:1::2: icmp_seq=2 ttl=64 time=0.027 ms\n\n"
                    "                --- fd12:3456:789a:1::2 ping statistics ---\n                2 packets transmitted, 2 received, 0% packet loss,"
                    " time 0ms\n                rtt min/avg/max/mdev = 0.027/0.060/0.094/0.033 ms, ipg/ewma 0.152/0.085 ms\n                "
                ]
            }
        ],
        "inputs": {"hosts": [{"destination": "fd12:3456:789a:1::2", "source": "vl110"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-interface"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0"}, {"destination": "10.0.0.2", "source": "Management0"}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.1 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
            {
                "messages": [
                    "PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.2 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-repeat"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 1}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms\n\n"
                    "                --- 10.0.0.1 ping statistics ---\n                1 packets transmitted, 1 received, 0% packet loss, time 0ms\n"
                    "                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-df-bit-size"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 5, "size": 1500, "df_bit": True}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 172.20.20.6 : 1472(1500) bytes of data.\n                1480 bytes from 10.0.0.1: "
                    "icmp_seq=1 ttl=64 time=0.085 ms\n                1480 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.020 ms\n"
                    "                1480 bytes from 10.0.0.1: icmp_seq=3 ttl=64 time=0.019 ms\n                1480 bytes from 10.0.0.1:"
                    " icmp_seq=4 ttl=64 time=0.018 ms\n                1480 bytes from 10.0.0.1:"
                    " icmp_seq=5 ttl=64 time=0.017 ms\n\n                --- 10.0.0.1 ping statistics ---\n                5 packets transmitted,"
                    " 5 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.017/0.031/0.085/0.026 ms, ipg/ewma 0.061/0.057 ms"
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "success-without-source"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "repeat": 1}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) : 72(100) bytes of data.\n                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms\n\n"
                    "                --- 10.0.0.1 ping statistics ---\n                1 packets transmitted, 1 received, 0% packet loss, time 0ms\n"
                    "                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms, ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyReachability, "failure-ip"): {
        "inputs": {"hosts": [{"destination": "10.0.0.11", "source": "10.0.0.5"}, {"destination": "10.0.0.2", "source": "10.0.0.5"}]},
        "eos_data": [
            {
                "messages": [
                    "ping: sendmsg: Network is unreachable\n                ping: sendmsg: Network is unreachable\n                "
                    "PING 10.0.0.11 (10.0.0.11) from 10.0.0.5 : 72(100) bytes of data.\n\n                --- 10.0.0.11 ping statistics ---\n"
                    "                2 packets transmitted, 0 received, 100% packet loss, time 10ms\n\n\n                "
                ]
            },
            {
                "messages": [
                    "PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.2 ping statistics ---\n                "
                    "2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: 10.0.0.11 Source: 10.0.0.5 VRF: default - Unreachable"]},
    },
    (VerifyReachability, "failure-ipv6"): {
        "eos_data": [
            {
                "messages": [
                    "PING fd12:3456:789a:1::2(fd12:3456:789a:1::2) from fd12:3456:789a:1::1 : 52 data bytes\n\n                    --- fd12:3456:789a:1::3 "
                    "ping statistics ---\n                    2 packets transmitted, 0 received, 100% packet loss, time 10ms\n                "
                ]
            }
        ],
        "inputs": {"hosts": [{"destination": "fd12:3456:789a:1::2", "source": "fd12:3456:789a:1::1"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: fd12:3456:789a:1::2 Source: fd12:3456:789a:1::1 VRF: default - Unreachable"]},
    },
    (VerifyReachability, "failure-interface"): {
        "inputs": {"hosts": [{"destination": "10.0.0.11", "source": "Management0"}, {"destination": "10.0.0.2", "source": "Management0"}]},
        "eos_data": [
            {
                "messages": [
                    "ping: sendmsg: Network is unreachable\n                ping: sendmsg: Network is unreachable\n                "
                    "PING 10.0.0.11 (10.0.0.11) from 10.0.0.5 : 72(100) bytes of data.\n\n                --- 10.0.0.11 ping statistics ---\n"
                    "                2 packets transmitted, 0 received, 100% packet loss, time 10ms\n\n\n                "
                ]
            },
            {
                "messages": [
                    "PING 10.0.0.2 (10.0.0.2) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.2 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            },
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: 10.0.0.11 Source: Management0 VRF: default - Unreachable"]},
    },
    (VerifyReachability, "failure-size"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "Management0", "repeat": 5, "size": 1501, "df_bit": True}]},
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 172.20.20.6 : 1473(1501) bytes of data.\n                ping: local error: message too long, mtu=1500\n"
                    "                ping: local error: message too long, mtu=1500\n"
                    "                ping: local error: message too long, mtu=1500\n                ping: local error: message too long, mtu=1500\n"
                    "                ping: local error: message too long, mtu=1500\n\n                --- 10.0.0.1 ping statistics ---\n"
                    "                5 packets transmitted, 0 received, +5 errors, 100% packet loss, time 40ms\n                "
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: 10.0.0.1 Source: Management0 VRF: default - Unreachable"]},
    },
    (VerifyReachability, "failure-expected-unreachable"): {
        "eos_data": [
            {
                "messages": [
                    "PING 10.0.0.1 (10.0.0.1) from 10.0.0.5 : 72(100) bytes of data.\n                80 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=0.247 ms\n"
                    "                80 bytes from 10.0.0.1: icmp_seq=2 ttl=64 time=0.072 ms\n\n                --- 10.0.0.1 ping statistics ---\n"
                    "                2 packets transmitted, 2 received, 0% packet loss, time 0ms\n                rtt min/avg/max/mdev = 0.072/0.159/0.247/0.088 ms,"
                    " ipg/ewma 0.370/0.225 ms\n\n                "
                ]
            }
        ],
        "inputs": {"hosts": [{"destination": "10.0.0.1", "source": "10.0.0.5", "reachable": False}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Host: 10.0.0.1 Source: 10.0.0.5 VRF: default - Destination is expected to be unreachable but found reachable"],
        },
    },
    (VerifyReachability, "failure-without-source"): {
        "inputs": {"hosts": [{"destination": "10.0.0.1", "repeat": 1}]},
        "eos_data": [
            {
                "messages": [
                    "ping: sendmsg: Network is unreachable\n                PING 10.0.0.1 (10.0.0.1) : 72(100) bytes of data.\n\n"
                    "                --- 10.0.0.11 ping statistics ---\n                "
                    "2 packets transmitted, 0 received, 100% packet loss, time 10ms\n\n                "
                ]
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: 10.0.0.1 VRF: default - Unreachable"]},
    },
    (VerifyLLDPNeighbors, "success"): {
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
                                    "interfaceId": "Ethernet1",
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
                                    "interfaceId": "Ethernet1",
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLLDPNeighbors, "success-multiple-neighbors"): {
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
                                    "interfaceId": "Ethernet1",
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
                                    "interfaceId": "Ethernet1",
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            },
                        ]
                    }
                }
            }
        ],
        "inputs": {"neighbors": [{"port": "Ethernet1", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyLLDPNeighbors, "failure-port-not-configured"): {
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
                                    "interfaceId": "Ethernet1",
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet1",
                                },
                            }
                        ]
                    }
                }
            }
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - Port not found"]},
    },
    (VerifyLLDPNeighbors, "failure-no-neighbor"): {
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
                                    "interfaceId": "Ethernet1",
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
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - No LLDP neighbors"]},
    },
    (VerifyLLDPNeighbors, "failure-wrong-neighbor"): {
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
                                    "interfaceId": "Ethernet1",
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
                                    "interfaceId": "Ethernet2",
                                    "interfaceId_v2": "Ethernet2",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            }
                        ]
                    },
                }
            }
        ],
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: DC1-SPINE2/Ethernet2"],
        },
    },
    (VerifyLLDPNeighbors, "failure-multiple"): {
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
                                    "interfaceId": "Ethernet2",
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
        "inputs": {
            "neighbors": [
                {"port": "Ethernet1", "neighbor_device": "DC1-SPINE1", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet2", "neighbor_device": "DC1-SPINE2", "neighbor_port": "Ethernet1"},
                {"port": "Ethernet3", "neighbor_device": "DC1-SPINE3", "neighbor_port": "Ethernet1"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Port: Ethernet1 Neighbor: DC1-SPINE1 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: DC1-SPINE1/Ethernet2",
                "Port: Ethernet2 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet1 - No LLDP neighbors",
                "Port: Ethernet3 Neighbor: DC1-SPINE3 Neighbor Port: Ethernet1 - Port not found",
            ],
        },
    },
    (VerifyLLDPNeighbors, "failure-multiple-neighbors"): {
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
                                    "interfaceId": "Ethernet1",
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
                                    "interfaceId": "Ethernet1",
                                    "interfaceId_v2": "Ethernet1",
                                    "interfaceDescription": "P2P_LINK_TO_DC1-LEAF1A_Ethernet2",
                                },
                            },
                        ]
                    }
                }
            }
        ],
        "inputs": {"neighbors": [{"port": "Ethernet1", "neighbor_device": "DC1-SPINE3", "neighbor_port": "Ethernet1"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Port: Ethernet1 Neighbor: DC1-SPINE3 Neighbor Port: Ethernet1 - Wrong LLDP neighbors: DC1-SPINE1/Ethernet1, DC1-SPINE2/Ethernet1"],
        },
    },
}
