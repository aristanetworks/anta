# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.services import VerifyDNSServers
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyDNSServers,
        "eos_data": [
            {
                "nameServerConfigs": [{"ipAddr": "10.14.0.1", "vrf": "default", "priority": 0}, {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1}],
            }
        ],
        "inputs": {
            "dns_servers": [{"server_address": "10.14.0.1", "vrf": "default", "priority": 0}, {"server_address": "10.14.0.11", "vrf": "MGMT", "priority": 1}]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-dns-missing",
        "test": VerifyDNSServers,
        "eos_data": [
            {
                "nameServerConfigs": [{"ipAddr": "10.14.0.1", "vrf": "default", "priority": 0}, {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1}],
            }
        ],
        "inputs": {
            "dns_servers": [{"server_address": "10.14.0.10", "vrf": "default", "priority": 0}, {"server_address": "10.14.0.21", "vrf": "MGMT", "priority": 1}]
        },
        "expected": {
            "result": "failure",
            "messages": ["DNS server `10.14.0.10` is not configured with any VRF.", "DNS server `10.14.0.21` is not configured with any VRF."],
        },
    },
    {
        "name": "failure-no-dns-found",
        "test": VerifyDNSServers,
        "eos_data": [
            {
                "nameServerConfigs": [],
            }
        ],
        "inputs": {
            "dns_servers": [{"server_address": "10.14.0.10", "vrf": "default", "priority": 0}, {"server_address": "10.14.0.21", "vrf": "MGMT", "priority": 1}]
        },
        "expected": {
            "result": "failure",
            "messages": ["DNS server `10.14.0.10` is not configured with any VRF.", "DNS server `10.14.0.21` is not configured with any VRF."],
        },
    },
    {
        "name": "failure-incorrect-dns-details",
        "test": VerifyDNSServers,
        "eos_data": [
            {
                "nameServerConfigs": [{"ipAddr": "10.14.0.1", "vrf": "CS", "priority": 1}, {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1}],
            }
        ],
        "inputs": {
            "dns_servers": [
                {"server_address": "10.14.0.1", "vrf": "CS", "priority": 0},
                {"server_address": "10.14.0.11", "vrf": "default", "priority": 0},
                {"server_address": "10.14.0.110", "vrf": "MGMT", "priority": 0},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For DNS server `10.14.0.1`, the expected priority is `0`, but `1` was found instead.",
                "DNS server `10.14.0.11` is not configured with VRF `default`.",
                "DNS server `10.14.0.110` is not configured with any VRF.",
            ],
        },
    },
]
