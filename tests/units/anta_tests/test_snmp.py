# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.snmp.py."""

from __future__ import annotations

from typing import Any

from anta.tests.snmp import VerifySnmpContact, VerifySnmpIPv4Acl, VerifySnmpIPv6Acl, VerifySnmpLocation, VerifySNMPNotificationHost, VerifySnmpStatus
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
        "test": VerifySNMPNotificationHost,
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v3",
                        "v3Params": {"user": "public", "securityLevel": "authNoPriv"},
                    },
                    {
                        "hostname": "192.168.1.101",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v2c",
                        "v1v2cParams": {"communityString": "public"},
                    },
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifySNMPNotificationHost,
        "eos_data": [{"hosts": []}],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": "failure", "messages": ["No SNMP host is configured."]},
    },
    {
        "name": "failure-details-not-found",
        "test": VerifySNMPNotificationHost,
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v3",
                        "v3Params": {"user": "public", "securityLevel": "authNoPriv"},
                    },
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": "failure", "messages": ["SNMP host '192.168.1.101' is not configured.\n"]},
    },
    {
        "name": "failure-incorrect-config",
        "test": VerifySNMPNotificationHost,
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 163,
                        "vrf": "",
                        "notificationType": "inform",
                        "protocolVersion": "v3",
                        "v3Params": {"user": "public1", "securityLevel": "authNoPriv"},
                    },
                    {
                        "hostname": "192.168.1.101",
                        "port": 163,
                        "vrf": "MGMT",
                        "notificationType": "inform",
                        "protocolVersion": "v2c",
                        "v1v2cParams": {"communityString": "public1"},
                    },
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "For SNMP host 192.168.1.100:\n"
                "Expected `trap` as the notification type, but found `inform` instead.\n"
                "Expected `162` as the udp port, but found `163` instead.\n"
                "Expected `public` as the user, but found `public1` instead.\n"
                "For SNMP host 192.168.1.101:\n"
                "Expected `default` as the vrf, but found `MGMT` instead.\n"
                "Expected `trap` as the notification type, but found `inform` instead.\n"
                "Expected `162` as the udp port, but found `163` instead.\n"
                "Expected `public` as the community_string, but found `public1` instead.\n"
            ],
        },
    },
]
