# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.services.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.tests.services import VerifyDNSLookup, VerifyDNSServers, VerifyErrdisableRecovery, VerifyHostname
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from anta.models import AntaTest
    from tests.units.anta_tests import AntaUnitTest

DATA: dict[tuple[type[AntaTest], str], AntaUnitTest] = {
    (VerifyHostname, "success"): {
        "eos_data": [{"hostname": "s1-spine1", "fqdn": "s1-spine1.fun.aristanetworks.com"}],
        "inputs": {"hostname": "s1-spine1"},
        "expected": {"result": "success"},
    },
    (VerifyHostname, "failure-incorrect-hostname"): {
        "eos_data": [{"hostname": "s1-spine2", "fqdn": "s1-spine1.fun.aristanetworks.com"}],
        "inputs": {"hostname": "s1-spine1"},
        "expected": {"result": "failure", "messages": ["Incorrect Hostname - Expected: s1-spine1 Actual: s1-spine2"]},
    },
    (VerifyDNSLookup, "success"): {
        "eos_data": [
            {
                "messages": [
                    "Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\tarista.com\nAddress: 151.101.130.132\n"
                    "Name:\tarista.com\nAddress: 151.101.2.132\nName:\tarista.com\nAddress: 151.101.194.132\nName:\tarista.com\nAddress: 151.101.66.132\n\n"
                ]
            },
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.com", "www.google.com"]},
        "expected": {"result": "success"},
    },
    (VerifyDNSLookup, "failure"): {
        "eos_data": [
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\n*** Can't find arista.ca: No answer\n\n"]},
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\nName:\twww.google.com\nAddress: 172.217.12.100\n\n"]},
            {"messages": ["Server:\t\t127.0.0.1\nAddress:\t127.0.0.1#53\n\nNon-authoritative answer:\n*** Can't find google.ca: No answer\n\n"]},
        ],
        "inputs": {"domain_names": ["arista.ca", "www.google.com", "google.ca"]},
        "expected": {"result": "failure", "messages": ["The following domain(s) are not resolved to an IP address: arista.ca, google.ca"]},
    },
    (VerifyDNSServers, "success"): {
        "eos_data": [
            {
                "nameServerConfigs": [
                    {"ipAddr": "10.14.0.1", "vrf": "default", "priority": 0},
                    {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1},
                    {"ipAddr": "fd12:3456:789a::1", "vrf": "default", "priority": 0},
                ]
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
    (VerifyDNSServers, "failure-no-dns-found"): {
        "eos_data": [{"nameServerConfigs": []}],
        "inputs": {
            "dns_servers": [{"server_address": "10.14.0.10", "vrf": "default", "priority": 0}, {"server_address": "10.14.0.21", "vrf": "MGMT", "priority": 1}]
        },
        "expected": {
            "result": "failure",
            "messages": ["Server 10.14.0.10 VRF: default Priority: 0 - Not configured", "Server 10.14.0.21 VRF: MGMT Priority: 1 - Not configured"],
        },
    },
    (VerifyDNSServers, "failure-incorrect-dns-details"): {
        "eos_data": [{"nameServerConfigs": [{"ipAddr": "10.14.0.1", "vrf": "CS", "priority": 1}, {"ipAddr": "10.14.0.11", "vrf": "MGMT", "priority": 1}]}],
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
                "Server 10.14.0.1 VRF: CS Priority: 0 - Incorrect priority - Priority: 1",
                "Server 10.14.0.11 VRF: default Priority: 0 - Not configured",
                "Server 10.14.0.110 VRF: MGMT Priority: 0 - Not configured",
            ],
        },
    },
    (VerifyErrdisableRecovery, "success"): {
        "eos_data": [
            "\n                Errdisable Reason              Timer Status   Timer Interval\n                ------------------------------"
            " ----------------- --------------\n                acl                            Enabled                  300\n\n "
            "               bpduguard                      Enabled                  300\n                arp-inspection  "
            "               Enabled                  30\n            "
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "bpduguard", "interval": 300}]},
        "expected": {"result": "success"},
    },
    (VerifyErrdisableRecovery, "failure-reason-missing"): {
        "eos_data": [
            "\n                Errdisable Reason              Timer Status   Timer Interval\n                ------------------------------"
            " ----------------- --------------\n                acl                            Enabled                  300\n         "
            "       bpduguard                      Enabled                  300\n                arp-inspection                 Enabled"
            "                  30\n            "
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}, {"reason": "tapagg", "interval": 30}]},
        "expected": {"result": "failure", "messages": ["Reason: tapagg Status: Enabled Interval: 30 - Not found"]},
    },
    (VerifyErrdisableRecovery, "failure-reason-disabled"): {
        "eos_data": [
            "\n                Errdisable Reason              Timer Status   Timer Interval\n                ------------------------------ "
            "----------------- --------------\n                acl                            Disabled                 300\n                "
            "bpduguard                      Enabled                  300\n                arp-inspection                 Enabled"
            "                  30\n            "
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 300}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {"result": "failure", "messages": ["Reason: acl Status: Enabled Interval: 300 - Incorrect configuration - Status: Disabled Interval: 300"]},
    },
    (VerifyErrdisableRecovery, "failure-interval-not-ok"): {
        "eos_data": [
            "\n                Errdisable Reason              Timer Status   Timer Interval\n                ------------------------------ "
            "----------------- --------------\n                acl                            Enabled                  300\n                "
            "bpduguard                      Enabled                  300\n                arp-inspection                 Enabled   "
            "               30\n            "
        ],
        "inputs": {"reasons": [{"reason": "acl", "interval": 30}, {"reason": "arp-inspection", "interval": 30}]},
        "expected": {"result": "failure", "messages": ["Reason: acl Status: Enabled Interval: 30 - Incorrect configuration - Status: Enabled Interval: 300"]},
    },
    (VerifyErrdisableRecovery, "failure-all-type"): {
        "eos_data": [
            "\n                Errdisable Reason              Timer Status   Timer Interval\n                ------------------------------ "
            "----------------- --------------\n                acl                            Disabled                 300\n                "
            "bpduguard                      Enabled                  300\n                arp-inspection                 Enabled             "
            "     30\n            "
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
}
