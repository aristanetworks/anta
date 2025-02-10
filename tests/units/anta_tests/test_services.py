# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.services.py."""

from __future__ import annotations

from typing import Any

from anta.tests.services import VerifyDNSLookup, VerifyDNSServers, VerifyErrdisableRecovery, VerifyHostname
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyHostname,
        "eos_data": [{"hostname": "s1-spine1", "fqdn": "s1-spine1.fun.aristanetworks.com"}],
        "inputs": {"hostname": "s1-spine1"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-hostname",
        "test": VerifyHostname,
        "eos_data": [{"hostname": "s1-spine2", "fqdn": "s1-spine1.fun.aristanetworks.com"}],
        "inputs": {"hostname": "s1-spine1"},
        "expected": {
            "result": "failure",
            "messages": ["Expected `s1-spine1` as the hostname, but found `s1-spine2` instead."],
        },
    },
    {
        "name": "success",
        "test": VerifyDNSLookup,
        "eos_data": [
            {
                "messages": [
                    "Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\tarista.com\nAddress: 151.101.130.132\nName:\tarista.com\n"
                    "Address: 151.101.2.132\nName:\tarista.com\nAddress: 151.101.194.132\nName:\tarista.com\nAddress: 151.101.66.132\n\n"
                ]
            },
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.com", "www.google.com"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyDNSLookup,
        "eos_data": [
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\n*** Can't find arista.ca: No answer\n\n"]},
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\n*** Can't find google.ca: No answer\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.ca", "www.google.com", "google.ca"]},
        "expected": {"result": "failure", "messages": ["The following domain(s) are not resolved to an IP address: arista.ca, google.ca"]},
    },
    {
        "name": "success",
        "test": VerifyDNSServers,
        "eos_data": [
            {
                "nameServerConfigs": [
                    {"ipAddr": "10.14.0.1", "vrf": "default", "priority": 0},
                    {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1},
                    {"ipAddr": "fd12:3456:789a::1", "vrf": "default", "priority": 0},
                ],
            }
        ],
        "inputs": {
            "dns_servers": [
                {"server_address": "10.14.0.1", "vrf": "default", "priority": 0},
                {"server_address": "10.14.0.11", "vrf": "MGMT", "priority": 1},
                {"server_address": "fd12:3456:789a::1", "vrf": "default", "priority": 0},
            ]
        },
        "expected": {"result": "success"},
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
            "messages": ["Server 10.14.0.10 (VRF: default, Priority: 0) - Not configured", "Server 10.14.0.21 (VRF: MGMT, Priority: 1) - Not configured"],
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
                "Server 10.14.0.1 (VRF: CS, Priority: 0) - Incorrect priority - Priority: 1",
                "Server 10.14.0.11 (VRF: default, Priority: 0) - Not configured",
                "Server 10.14.0.110 (VRF: MGMT, Priority: 0) - Not configured",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            # Adding empty line on purpose to verify they are skipped
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300

                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "bpduguard", "interval": 300}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-reason-missing",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}, {"reason": "tapagg", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": ["Reason: tapagg Status: Enabled Interval: 30 - Not found"],
        },
    },
    {
        "name": "failure-reason-disabled",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Disabled                 300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": ["Reason: acl Status: Enabled Interval: 300 - Incorrect configuration - Status: Disabled Interval: 300"],
        },
    },
    {
        "name": "failure-interval-not-ok",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Enabled                  300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 30}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Reason: acl Status: Enabled Interval: 30 - Incorrect configuration - Status: Enabled Interval: 300",
            ],
        },
    },
    {
        "name": "failure-all-type",
        "test": VerifyErrdisableRecovery,
        "eos_data": [
            """
                Errdisable Reason              Timer Status   Timer Interval
                ------------------------------ ----------------- --------------
                acl                            Disabled                 300
                bpduguard                      Enabled                  300
                arp-inspection                 Enabled                  30
            """
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 30}, {"reason": "arp-inspection", "interval": 300}, {"reason": "tapagg", "interval": 30}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Reason: acl Status: Enabled Interval: 30 - Incorrect configuration - Status: Disabled Interval: 300",
                "Reason: arp-inspection Status: Enabled Interval: 300 - Incorrect configuration - Status: Enabled Interval: 30",
                "Reason: tapagg Status: Enabled Interval: 30 - Not found",
            ],
        },
    },
]
