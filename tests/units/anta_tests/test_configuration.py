# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

from typing import Any

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "disabled"}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyZeroTouch,
        "eos_data": [{"mode": "enabled"}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["ZTP is NOT disabled"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigDiffs,
        "eos_data": [""],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigDiffs,
        "eos_data": ["blah blah"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["blah blah"]},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["blah blah"],
        "inputs": {"regex_patterns": ["blah"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyRunningConfigLines,
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": "failure", "messages": ["Regex pattern: bla - Not found", "Regex pattern: bleh - Not found"]},
    },
    {
        "name": "success-section",
        "test": VerifyRunningConfigLines,
        "eos_data": [
            "interface Ethernet1\n   description Ethernet1- s1\n   switchport mode trunk\n   channel-group 1 mode active\ninterface Ethernet10\n   "
            "ip address 9.11.1.2/31\ninterface Ethernet100\n   ip address 10.11.19.3/31\nrouter bgp 65101\n   router-id 10.111.254.1\n   "
            "maximum-paths 2\n   neighbor SPINE peer group\n   neighbor SPINE remote-as 65100\n   "
            "neighbor SPINE send-community standard extended\n   neighbor 10.111.1.0 peer group SPINE\n   neighbor 10.111.2.0 peer group SPINE\n   "
            "neighbor 10.255.255.2 remote-as 65101\n   neighbor 10.255.255.2 next-hop-self\n   network 10.111.112.0/24\n   network 10.111.254.1/32\n"
        ],
        "inputs": {
            "sections": [
                {"section": "^interface ethernet1$", "regex_patterns": ["switchport mode trunk"]},
                {"section": "router bgp 65101", "regex_patterns": ["router-id 10.111.254.1", "neighbor SPINE*"]},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-both-section-regex-pattern",
        "test": VerifyRunningConfigLines,
        "eos_data": [
            "interface Ethernet1\n   description Ethernet1- s1\n   switchport mode trunk\n   channel-group 1 mode active\ninterface Ethernet10\n   "
            "ip address 9.11.1.2/31\ninterface Ethernet100\n   ip address 10.11.19.3/31\nrouter bgp 65101\n   router-id 10.111.254.1\n   "
            "maximum-paths 2\n   neighbor SPINE peer group\n   neighbor SPINE remote-as 65100\n   "
            "neighbor SPINE send-community standard extended\n   neighbor 10.111.1.0 peer group SPINE\n   neighbor 10.111.2.0 peer group SPINE\n   "
            "neighbor 10.255.255.2 remote-as 65101\n   neighbor 10.255.255.2 next-hop-self\n   network 10.111.112.0/24\n   network 10.111.254.1/32\n"
            "enable password something\nsome other line"
        ],
        "inputs": {
            "sections": [
                {"section": "^interface ethernet1$", "regex_patterns": ["switchport mode trunk"]},
                {"section": "router bgp 65101", "regex_patterns": ["router-id 10.111.254.1", "neighbor SPINE*"]},
            ],
            "regex_patterns": ["^enable password .*$", "^.*other line$"],
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-section-regex-match",
        "test": VerifyRunningConfigLines,
        "eos_data": [
            "interface Ethernet1\n   description MLAG Peer-link - s1-leaf1\n   no switchport\n   no switchport\n   ip address 10.0.12.2/24\n"
            "   channel-group 1mode active\n   isis enable 1\nrouter bgp 65101\n   router-id 10.111.254.1\n   maximum-paths 2\n   "
            "neighbor SPINE peer group\n   neighbor SPINE remote-as 65100\n   "
            "neighbor SPINE send-community standard extended\n   neighbor 10.111.1.0 peer group SPINE\n   neighbor 10.111.2.0 peer group SPINE\n   "
            "neighbor 10.255.255.2 remote-as 65101\n   neighbor 10.255.255.2 next-hop-self\n   network 10.111.112.0/24\n   network 10.111.254.1/32\n",
        ],
        "inputs": {
            "sections": [
                {"section": "^interface Ethernet1$", "regex_patterns": ["switchport mode trunk"]},
                {"section": "router bgp 65101", "regex_patterns": ["router-id 10.111.255.12", "network 10.110.254.1"]},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Section: ^interface Ethernet1$ Regex pattern: switchport mode trunk - Not found",
                "Section: router bgp 65101 Regex pattern: router-id 10.111.255.12 - Not found",
                "Section: router bgp 65101 Regex pattern: network 10.110.254.1 - Not found",
            ],
        },
    },
    {
        "name": "failure-both-section-regex-match",
        "test": VerifyRunningConfigLines,
        "eos_data": [
            "router bgp 65101\n   router-id 10.111.254.1\n   maximum-paths 2\n   neighbor SPINE peer group\n   neighbor SPINE remote-as 65100\n   "
            "neighbor SPINE send-community standard extended\n   neighbor 10.111.1.0 peer group SPINE\n   neighbor 10.111.2.0 peer group SPINE\n   "
            "neighbor 10.255.255.2 remote-as 65101\n   neighbor 10.255.255.2 next-hop-self\n   network 10.111.112.0/24\n   network 10.111.254.1/32\n"
            "router isis 1\n   net 49.0001.0000.0000.0002.00\n   !\n   address-family ipv4 unicast\n!\nrouter multicast\n   ipv4\n"
            "      software-forwarding kernel\n"
            "   !\n   ipv6\nsoftware-forwarding kernel\n"
        ],
        "inputs": {
            "sections": [{"section": "router bgp 65101", "regex_patterns": ["router-id 10.111.255.12", "network 10.110.254.1"]}],
            "regex_patterns": ["^router isis 2 vrf TEST1$", "mlag configuration"],
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Regex pattern: ^router isis 2 vrf TEST1$ - Not found",
                "Regex pattern: mlag configuration - Not found",
                "Section: router bgp 65101 Regex pattern: router-id 10.111.255.12 - Not found",
                "Section: router bgp 65101 Regex pattern: network 10.110.254.1 - Not found",
            ],
        },
    },
]
