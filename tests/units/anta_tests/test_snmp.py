# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.snmp.py."""

from __future__ import annotations

from typing import Any

from anta.tests.snmp import VerifySnmpContact, VerifySnmpErrors, VerifySnmpIPv4Acl, VerifySnmpIPv6Acl, VerifySnmpLocation, VerifySnmpStatus
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifySnmpStatus,
        "eos_data": [{"vrfs": {"snmpVrfs": ["MGMT", "default"]}, "enabled": True}],
        "inputs": {"vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifySnmpStatus,
        "eos_data": [{"vrfs": {"snmpVrfs": ["default"]}, "enabled": True}],
        "inputs": {"vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["SNMP agent disabled in vrf MGMT"]},
    },
    {
        "name": "failure-disabled",
        "test": VerifySnmpStatus,
        "eos_data": [{"vrfs": {"snmpVrfs": ["default"]}, "enabled": False}],
        "inputs": {"vrf": "default"},
        "expected": {"result": "failure", "messages": ["SNMP agent disabled in vrf default"]},
    },
    {
        "name": "success",
        "test": VerifySnmpIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SNMP", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifySnmpIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 SNMP IPv4 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifySnmpIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SNMP", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["SNMP IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_SNMP']"]},
    },
    {
        "name": "success",
        "test": VerifySnmpIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SNMP", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifySnmpIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 SNMP IPv6 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifySnmpIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SNMP", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["SNMP IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_SNMP']"]},
    },
    {
        "name": "success",
        "test": VerifySnmpLocation,
        "eos_data": [
            {
                "location": {"location": "New York"},
            }
        ],
        "inputs": {"location": "New York"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-location",
        "test": VerifySnmpLocation,
        "eos_data": [
            {
                "location": {"location": "Europe"},
            }
        ],
        "inputs": {"location": "New York"},
        "expected": {
            "result": "failure",
            "messages": ["Expected `New York` as the location, but found `Europe` instead."],
        },
    },
    {
        "name": "failure-details-not-configured",
        "test": VerifySnmpLocation,
        "eos_data": [
            {
                "location": {"location": ""},
            }
        ],
        "inputs": {"location": "New York"},
        "expected": {
            "result": "failure",
            "messages": ["SNMP location is not configured."],
        },
    },
    {
        "name": "success",
        "test": VerifySnmpContact,
        "eos_data": [
            {
                "contact": {"contact": "Jon@example.com"},
            }
        ],
        "inputs": {"contact": "Jon@example.com"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-contact",
        "test": VerifySnmpContact,
        "eos_data": [
            {
                "contact": {"contact": "Jon@example.com"},
            }
        ],
        "inputs": {"contact": "Bob@example.com"},
        "expected": {
            "result": "failure",
            "messages": ["Expected `Bob@example.com` as the contact, but found `Jon@example.com` instead."],
        },
    },
    {
        "name": "failure-details-not-configured",
        "test": VerifySnmpContact,
        "eos_data": [
            {
                "contact": {"contact": ""},
            }
        ],
        "inputs": {"contact": "Bob@example.com"},
        "expected": {
            "result": "failure",
            "messages": ["SNMP contact is not configured."],
        },
    },
    {
        "name": "success",
        "test": VerifySnmpErrors,
        "eos_data": [
            {
                "counters": {
                    "inVersionErrs": 0,
                    "inBadCommunityNames": 0,
                    "inBadCommunityUses": 0,
                    "inParseErrs": 0,
                    "outTooBigErrs": 0,
                    "outNoSuchNameErrs": 0,
                    "outBadValueErrs": 0,
                    "outGeneralErrs": 0,
                },
            }
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "success-specific-counters",
        "test": VerifySnmpErrors,
        "eos_data": [
            {
                "counters": {
                    "inVersionErrs": 0,
                    "inBadCommunityNames": 0,
                    "inBadCommunityUses": 0,
                    "inParseErrs": 0,
                    "outTooBigErrs": 5,
                    "outNoSuchNameErrs": 0,
                    "outBadValueErrs": 10,
                    "outGeneralErrs": 1,
                },
            }
        ],
        "inputs": {"error_counters": ["inVersionErrs", "inParseErrs"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-counters-not-found",
        "test": VerifySnmpErrors,
        "eos_data": [
            {
                "counters": {},
            }
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["SNMP counter details are not found."]},
    },
    {
        "name": "failure-incorrect-counters",
        "test": VerifySnmpErrors,
        "eos_data": [
            {
                "counters": {
                    "inVersionErrs": 1,
                    "inBadCommunityNames": 0,
                    "inBadCommunityUses": 0,
                    "inParseErrs": 2,
                    "outTooBigErrs": 0,
                    "outNoSuchNameErrs": 0,
                    "outBadValueErrs": 2,
                    "outGeneralErrs": 0,
                },
            }
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "The following SNMP error counter(s) are not found or have non-zero counter:\n{'inVersionErrs': 1, 'inParseErrs': 2, 'outBadValueErrs': 2}"
            ],
        },
    },
]
