# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.connectivity.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.connectivity import VerifyReachability
from tests.lib.anta import test  # noqa: F401

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
        "inputs": {"hosts": [{"destination": "10.0.0.1", "interface": "Management0"}, {"destination": "10.0.0.2", "interface": "Management0"}]},
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
        "inputs": {"hosts": [{"destination": "10.0.0.11", "interface": "Management0"}, {"destination": "10.0.0.2", "interface": "Management0"}]},
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
]
