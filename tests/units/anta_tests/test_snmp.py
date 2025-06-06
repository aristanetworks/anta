# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.snmp.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.snmp import (
    VerifySnmpContact,
    VerifySnmpErrorCounters,
    VerifySnmpGroup,
    VerifySnmpHostLogging,
    VerifySnmpIPv4Acl,
    VerifySnmpIPv6Acl,
    VerifySnmpLocation,
    VerifySnmpNotificationHost,
    VerifySnmpPDUCounters,
    VerifySnmpSourceInterface,
    VerifySnmpStatus,
    VerifySnmpUser,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifySnmpStatus, "success"): {
        "eos_data": [{"vrfs": {"snmpVrfs": ["MGMT", "default"]}, "enabled": True}],
        "inputs": {"vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpStatus, "failure-wrong-vrf"): {
        "eos_data": [{"vrfs": {"snmpVrfs": ["default"]}, "enabled": True}],
        "inputs": {"vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - SNMP agent disabled"]},
    },
    (VerifySnmpStatus, "failure-disabled"): {
        "eos_data": [{"vrfs": {"snmpVrfs": ["default"]}, "enabled": False}],
        "inputs": {"vrf": "default"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: default - SNMP agent disabled"]},
    },
    (VerifySnmpIPv4Acl, "success"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SNMP", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpIPv4Acl, "failure-wrong-number"): {
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Incorrect SNMP IPv4 ACL(s) - Expected: 1 Actual: 0"]},
    },
    (VerifySnmpIPv4Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SNMP", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following SNMP IPv4 ACL(s) not configured or active: ACL_IPV4_SNMP"]},
    },
    (VerifySnmpIPv6Acl, "success"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SNMP", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpIPv6Acl, "failure-wrong-number"): {
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Incorrect SNMP IPv6 ACL(s) - Expected: 1 Actual: 0"]},
    },
    (VerifySnmpIPv6Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SNMP", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following SNMP IPv6 ACL(s) not configured or active: ACL_IPV6_SNMP"]},
    },
    (VerifySnmpLocation, "success"): {
        "eos_data": [{"location": {"location": "New York"}}],
        "inputs": {"location": "New York"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpLocation, "failure-incorrect-location"): {
        "eos_data": [{"location": {"location": "Europe"}}],
        "inputs": {"location": "New York"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Incorrect SNMP location - Expected: New York Actual: Europe"]},
    },
    (VerifySnmpLocation, "failure-details-not-configured"): {
        "eos_data": [{"location": {"location": ""}}],
        "inputs": {"location": "New York"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP location is not configured"]},
    },
    (VerifySnmpContact, "success"): {
        "eos_data": [{"contact": {"contact": "Jon@example.com"}}],
        "inputs": {"contact": "Jon@example.com"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpContact, "failure-incorrect-contact"): {
        "eos_data": [{"contact": {"contact": "Jon@example.com"}}],
        "inputs": {"contact": "Bob@example.com"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Incorrect SNMP contact - Expected: Bob@example.com Actual: Jon@example.com"]},
    },
    (VerifySnmpContact, "failure-details-not-configured"): {
        "eos_data": [{"contact": {"contact": ""}}],
        "inputs": {"contact": "Bob@example.com"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP contact is not configured"]},
    },
    (VerifySnmpPDUCounters, "success"): {
        "eos_data": [{"counters": {"inGetPdus": 3, "inGetNextPdus": 2, "inSetPdus": 3, "outGetResponsePdus": 3, "outTrapPdus": 9}}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpPDUCounters, "success-specific-pdus"): {
        "eos_data": [{"counters": {"inGetPdus": 3, "inGetNextPdus": 0, "inSetPdus": 0, "outGetResponsePdus": 0, "outTrapPdus": 9}}],
        "inputs": {"pdus": ["inGetPdus", "outTrapPdus"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpPDUCounters, "failure-counters-not-found"): {
        "eos_data": [{"counters": {}}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP counters not found"]},
    },
    (VerifySnmpPDUCounters, "failure-incorrect-counters"): {
        "eos_data": [{"counters": {"inGetPdus": 0, "inGetNextPdus": 2, "inSetPdus": 0, "outGetResponsePdus": 3, "outTrapPdus": 9}}],
        "inputs": {},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["The following SNMP PDU counters are not found or have zero PDU counters: inGetPdus, inSetPdus"],
        },
    },
    (VerifySnmpPDUCounters, "failure-pdu-not-found"): {
        "eos_data": [{"counters": {"inGetNextPdus": 0, "inSetPdus": 0, "outGetResponsePdus": 0}}],
        "inputs": {"pdus": ["inGetPdus", "outTrapPdus"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["The following SNMP PDU counters are not found or have zero PDU counters: inGetPdus, outTrapPdus"],
        },
    },
    (VerifySnmpErrorCounters, "success"): {
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
                }
            }
        ],
        "inputs": {},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpErrorCounters, "success-specific-counters"): {
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
                }
            }
        ],
        "inputs": {"error_counters": ["inVersionErrs", "inParseErrs"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpErrorCounters, "failure-counters-not-found"): {
        "eos_data": [{"counters": {}}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP counters not found"]},
    },
    (VerifySnmpErrorCounters, "failure-incorrect-counters"): {
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
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["The following SNMP error counters are not found or have non-zero error counters: inParseErrs, inVersionErrs, outBadValueErrs"],
        },
    },
    (VerifySnmpHostLogging, "success"): {
        "eos_data": [
            {
                "logging": {
                    "loggingEnabled": True,
                    "hosts": {
                        "192.168.1.100": {"port": 162, "vrf": ""},
                        "192.168.1.101": {"port": 162, "vrf": "MGMT"},
                        "snmp-server-01": {"port": 162, "vrf": "default"},
                    },
                }
            }
        ],
        "inputs": {
            "hosts": [
                {"hostname": "192.168.1.100", "vrf": "default"},
                {"hostname": "192.168.1.101", "vrf": "MGMT"},
                {"hostname": "snmp-server-01", "vrf": "default"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpHostLogging, "failure-logging-disabled"): {
        "eos_data": [{"logging": {"loggingEnabled": False}}],
        "inputs": {"hosts": [{"hostname": "192.168.1.100", "vrf": "default"}, {"hostname": "192.168.1.101", "vrf": "MGMT"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP logging is disabled"]},
    },
    (VerifySnmpHostLogging, "failure-mismatch-vrf"): {
        "eos_data": [{"logging": {"loggingEnabled": True, "hosts": {"192.168.1.100": {"port": 162, "vrf": "MGMT"}, "192.168.1.101": {"port": 162, "vrf": "Test"}}}}],
        "inputs": {"hosts": [{"hostname": "192.168.1.100", "vrf": "default"}, {"hostname": "192.168.1.101", "vrf": "MGMT"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Host: 192.168.1.100 VRF: default - Incorrect VRF - Actual: MGMT", "Host: 192.168.1.101 VRF: MGMT - Incorrect VRF - Actual: Test"],
        },
    },
    (VerifySnmpHostLogging, "failure-host-not-configured"): {
        "eos_data": [{"logging": {"loggingEnabled": True, "hosts": {"192.168.1.100": {"port": 162, "vrf": "MGMT"}, "192.168.1.103": {"port": 162, "vrf": "Test"}}}}],
        "inputs": {"hosts": [{"hostname": "192.168.1.101", "vrf": "default"}, {"hostname": "192.168.1.102", "vrf": "MGMT"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Host: 192.168.1.101 VRF: default - Not configured", "Host: 192.168.1.102 VRF: MGMT - Not configured"],
        },
    },
    (VerifySnmpUser, "success"): {
        "eos_data": [
            {
                "usersByVersion": {
                    "v1": {"users": {"Test1": {"groupName": "TestGroup1"}}},
                    "v2c": {"users": {"Test2": {"groupName": "TestGroup2"}}},
                    "v3": {
                        "users": {
                            "Test3": {"groupName": "TestGroup3", "v3Params": {"authType": "SHA-384", "privType": "AES-128"}},
                            "Test4": {"groupName": "TestGroup3", "v3Params": {"authType": "SHA-512", "privType": "AES-192"}},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "snmp_users": [
                {"username": "Test1", "group_name": "TestGroup1", "version": "v1"},
                {"username": "Test2", "group_name": "TestGroup2", "version": "v2c"},
                {"username": "Test3", "group_name": "TestGroup3", "version": "v3", "auth_type": "SHA-384", "priv_type": "AES-128"},
                {"username": "Test4", "group_name": "TestGroup3", "version": "v3", "auth_type": "SHA-512", "priv_type": "AES-192"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpUser, "failure-not-configured"): {
        "eos_data": [{"usersByVersion": {"v3": {"users": {"Test3": {"groupName": "TestGroup3", "v3Params": {"authType": "SHA-384", "privType": "AES-128"}}}}}}],
        "inputs": {
            "snmp_users": [
                {"username": "Test1", "group_name": "TestGroup1", "version": "v1"},
                {"username": "Test2", "group_name": "TestGroup2", "version": "v2c"},
                {"username": "Test3", "group_name": "TestGroup3", "version": "v3", "auth_type": "SHA-384", "priv_type": "AES-128"},
                {"username": "Test4", "group_name": "TestGroup3", "version": "v3", "auth_type": "SHA-512", "priv_type": "AES-192"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "User: Test1 Group: TestGroup1 Version: v1 - Not found",
                "User: Test2 Group: TestGroup2 Version: v2c - Not found",
                "User: Test4 Group: TestGroup3 Version: v3 - Not found",
            ],
        },
    },
    (VerifySnmpUser, "failure-incorrect-group"): {
        "eos_data": [
            {"usersByVersion": {"v1": {"users": {"Test1": {"groupName": "TestGroup2"}}}, "v2c": {"users": {"Test2": {"groupName": "TestGroup1"}}}, "v3": {}}}
        ],
        "inputs": {
            "snmp_users": [{"username": "Test1", "group_name": "TestGroup1", "version": "v1"}, {"username": "Test2", "group_name": "TestGroup2", "version": "v2c"}]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "User: Test1 Group: TestGroup1 Version: v1 - Incorrect user group - Actual: TestGroup2",
                "User: Test2 Group: TestGroup2 Version: v2c - Incorrect user group - Actual: TestGroup1",
            ],
        },
    },
    (VerifySnmpUser, "failure-incorrect-auth-encryption"): {
        "eos_data": [
            {
                "usersByVersion": {
                    "v1": {"users": {"Test1": {"groupName": "TestGroup1"}}},
                    "v2c": {"users": {"Test2": {"groupName": "TestGroup2"}}},
                    "v3": {
                        "users": {
                            "Test3": {"groupName": "TestGroup3", "v3Params": {"authType": "SHA-512", "privType": "AES-192"}},
                            "Test4": {"groupName": "TestGroup4", "v3Params": {"authType": "SHA-384", "privType": "AES-128"}},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "snmp_users": [
                {"username": "Test1", "group_name": "TestGroup1", "version": "v1"},
                {"username": "Test2", "group_name": "TestGroup2", "version": "v2c"},
                {"username": "Test3", "group_name": "TestGroup3", "version": "v3", "auth_type": "SHA-384", "priv_type": "AES-128"},
                {"username": "Test4", "group_name": "TestGroup4", "version": "v3", "auth_type": "SHA-512", "priv_type": "AES-192"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "User: Test3 Group: TestGroup3 Version: v3 - Incorrect authentication type - Expected: SHA-384 Actual: SHA-512",
                "User: Test3 Group: TestGroup3 Version: v3 - Incorrect privacy type - Expected: AES-128 Actual: AES-192",
                "User: Test4 Group: TestGroup4 Version: v3 - Incorrect authentication type - Expected: SHA-512 Actual: SHA-384",
                "User: Test4 Group: TestGroup4 Version: v3 - Incorrect privacy type - Expected: AES-192 Actual: AES-128",
            ],
        },
    },
    (VerifySnmpNotificationHost, "success"): {
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
                        "vrf": "MGMT",
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
                {"hostname": "192.168.1.101", "vrf": "MGMT", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpNotificationHost, "failure-not-configured"): {
        "eos_data": [{"hosts": []}],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No SNMP host is configured"]},
    },
    (VerifySnmpNotificationHost, "failure-details-host-not-found"): {
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
                    }
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Host: 192.168.1.101 VRF: default Version: v2c - Not configured"]},
    },
    (VerifySnmpNotificationHost, "failure-incorrect-notification-type"): {
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
                        "notificationType": "inform",
                        "protocolVersion": "v2c",
                        "v1v2cParams": {"communityString": "public"},
                    },
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "inform", "version": "v3", "udp_port": 162, "user": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: 192.168.1.100 VRF: default - Incorrect notification type - Expected: inform Actual: trap",
                "Host: 192.168.1.101 VRF: default - Incorrect notification type - Expected: trap Actual: inform",
            ],
        },
    },
    (VerifySnmpNotificationHost, "failure-incorrect-udp-port"): {
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 163,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v3",
                        "v3Params": {"user": "public", "securityLevel": "authNoPriv"},
                    },
                    {
                        "hostname": "192.168.1.101",
                        "port": 164,
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: 192.168.1.100 VRF: default - Incorrect UDP port - Expected: 162 Actual: 163",
                "Host: 192.168.1.101 VRF: default - Incorrect UDP port - Expected: 162 Actual: 164",
            ],
        },
    },
    (VerifySnmpNotificationHost, "failure-incorrect-community-string-version-v1-v2c"): {
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v1",
                        "v1v2cParams": {"communityString": "private"},
                    },
                    {
                        "hostname": "192.168.1.101",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v2c",
                        "v1v2cParams": {"communityString": "private"},
                    },
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [
                {"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v1", "udp_port": 162, "community_string": "public"},
                {"hostname": "192.168.1.101", "vrf": "default", "notification_type": "trap", "version": "v2c", "udp_port": 162, "community_string": "public"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Host: 192.168.1.100 VRF: default Version: v1 - Incorrect community string - Expected: public Actual: private",
                "Host: 192.168.1.101 VRF: default Version: v2c - Incorrect community string - Expected: public Actual: private",
            ],
        },
    },
    (VerifySnmpNotificationHost, "failure-incorrect-user-for-version-v3"): {
        "eos_data": [
            {
                "hosts": [
                    {
                        "hostname": "192.168.1.100",
                        "port": 162,
                        "vrf": "",
                        "notificationType": "trap",
                        "protocolVersion": "v3",
                        "v3Params": {"user": "private", "securityLevel": "authNoPriv"},
                    }
                ]
            }
        ],
        "inputs": {
            "notification_hosts": [{"hostname": "192.168.1.100", "vrf": "default", "notification_type": "trap", "version": "v3", "udp_port": 162, "user": "public"}]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Host: 192.168.1.100 VRF: default Version: v3 - Incorrect user - Expected: public Actual: private"],
        },
    },
    (VerifySnmpSourceInterface, "success"): {
        "eos_data": [{"srcIntf": {"sourceInterfaces": {"default": "Ethernet1", "MGMT": "Management0"}}}],
        "inputs": {"interfaces": [{"interface": "Ethernet1", "vrf": "default"}, {"interface": "Management0", "vrf": "MGMT"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpSourceInterface, "failure-not-configured"): {
        "eos_data": [{"srcIntf": {}}],
        "inputs": {"interfaces": [{"interface": "Ethernet1", "vrf": "default"}, {"interface": "Management0", "vrf": "MGMT"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SNMP source interface(s) not configured"]},
    },
    (VerifySnmpSourceInterface, "failure-incorrect-interfaces"): {
        "eos_data": [{"srcIntf": {"sourceInterfaces": {"default": "Management0"}}}],
        "inputs": {"interfaces": [{"interface": "Ethernet1", "vrf": "default"}, {"interface": "Management0", "vrf": "MGMT"}]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Source Interface: Ethernet1 VRF: default - Incorrect source interface - Actual: Management0",
                "Source Interface: Management0 VRF: MGMT - Not configured",
            ],
        },
    },
    (VerifySnmpGroup, "success"): {
        "eos_data": [
            {
                "groups": {
                    "Group1": {
                        "versions": {
                            "v1": {
                                "secModel": "v1",
                                "readView": "group_read_1",
                                "readViewConfig": True,
                                "writeView": "group_write_1",
                                "writeViewConfig": True,
                                "notifyView": "group_notify_1",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                    "Group2": {
                        "versions": {
                            "v2c": {
                                "secModel": "v2c",
                                "readView": "group_read_2",
                                "readViewConfig": True,
                                "writeView": "group_write_2",
                                "writeViewConfig": True,
                                "notifyView": "group_notify_2",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                    "Group3": {
                        "versions": {
                            "v3": {
                                "secModel": "v3Auth",
                                "readView": "group_read_3",
                                "readViewConfig": True,
                                "writeView": "group_write_3",
                                "writeViewConfig": True,
                                "notifyView": "group_notify_3",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "snmp_groups": [
                {"group_name": "Group1", "version": "v1", "read_view": "group_read_1", "write_view": "group_write_1", "notify_view": "group_notify_1"},
                {"group_name": "Group2", "version": "v2c", "read_view": "group_read_2", "write_view": "group_write_2", "notify_view": "group_notify_2"},
                {
                    "group_name": "Group3",
                    "version": "v3",
                    "read_view": "group_read_3",
                    "write_view": "group_write_3",
                    "notify_view": "group_notify_3",
                    "authentication": "auth",
                },
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySnmpGroup, "failure-incorrect-view"): {
        "eos_data": [
            {
                "groups": {
                    "Group1": {
                        "versions": {
                            "v1": {
                                "secModel": "v1",
                                "readView": "group_read",
                                "readViewConfig": True,
                                "writeView": "group_write",
                                "writeViewConfig": True,
                                "notifyView": "group_notify",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                    "Group2": {
                        "versions": {
                            "v2c": {
                                "secModel": "v2c",
                                "readView": "group_read",
                                "readViewConfig": True,
                                "writeView": "group_write",
                                "writeViewConfig": True,
                                "notifyView": "group_notify",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                    "Group3": {
                        "versions": {
                            "v3": {
                                "secModel": "v3NoAuth",
                                "readView": "group_read",
                                "readViewConfig": True,
                                "writeView": "group_write",
                                "writeViewConfig": True,
                                "notifyView": "group_notify",
                                "notifyViewConfig": True,
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "snmp_groups": [
                {"group_name": "Group1", "version": "v1", "read_view": "group_read_1", "write_view": "group_write_1", "notify_view": "group_notify_1"},
                {"group_name": "Group2", "version": "v2c", "read_view": "group_read_2", "notify_view": "group_notify_2"},
                {
                    "group_name": "Group3",
                    "version": "v3",
                    "read_view": "group_read_3",
                    "write_view": "group_write_3",
                    "notify_view": "group_notify_3",
                    "authentication": "noauth",
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Group: Group1 Version: v1 - Incorrect Read view - Expected: group_read_1 Actual: group_read",
                "Group: Group1 Version: v1 - Incorrect Write view - Expected: group_write_1 Actual: group_write",
                "Group: Group1 Version: v1 - Incorrect Notify view - Expected: group_notify_1 Actual: group_notify",
                "Group: Group2 Version: v2c - Incorrect Read view - Expected: group_read_2 Actual: group_read",
                "Group: Group2 Version: v2c - Incorrect Notify view - Expected: group_notify_2 Actual: group_notify",
                "Group: Group3 Version: v3 - Incorrect Read view - Expected: group_read_3 Actual: group_read",
                "Group: Group3 Version: v3 - Incorrect Write view - Expected: group_write_3 Actual: group_write",
                "Group: Group3 Version: v3 - Incorrect Notify view - Expected: group_notify_3 Actual: group_notify",
            ],
        },
    },
    (VerifySnmpGroup, "failure-view-config-not-found"): {
        "eos_data": [
            {
                "groups": {
                    "Group1": {
                        "versions": {
                            "v1": {
                                "secModel": "v1",
                                "readView": "group_read",
                                "readViewConfig": False,
                                "writeView": "group_write",
                                "writeViewConfig": False,
                                "notifyView": "group_notify",
                                "notifyViewConfig": False,
                            }
                        }
                    },
                    "Group2": {
                        "versions": {
                            "v2c": {
                                "secModel": "v2c",
                                "readView": "group_read",
                                "readViewConfig": False,
                                "writeView": "group_write",
                                "writeViewConfig": False,
                                "notifyView": "group_notify",
                                "notifyViewConfig": False,
                            }
                        }
                    },
                    "Group3": {
                        "versions": {
                            "v3": {
                                "secModel": "v3Priv",
                                "readView": "group_read",
                                "readViewConfig": False,
                                "writeView": "group_write",
                                "writeViewConfig": False,
                                "notifyView": "group_notify",
                                "notifyViewConfig": False,
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "snmp_groups": [
                {"group_name": "Group1", "version": "v1", "read_view": "group_read", "write_view": "group_write", "notify_view": "group_notify"},
                {"group_name": "Group2", "version": "v2c", "read_view": "group_read", "write_view": "group_write", "notify_view": "group_notify"},
                {"group_name": "Group3", "version": "v3", "write_view": "group_write", "notify_view": "group_notify", "authentication": "priv"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Group: Group1 Version: v1 Read View: group_read - Not configured",
                "Group: Group1 Version: v1 Write View: group_write - Not configured",
                "Group: Group1 Version: v1 Notify View: group_notify - Not configured",
                "Group: Group2 Version: v2c Read View: group_read - Not configured",
                "Group: Group2 Version: v2c Write View: group_write - Not configured",
                "Group: Group2 Version: v2c Notify View: group_notify - Not configured",
                "Group: Group3 Version: v3 Write View: group_write - Not configured",
                "Group: Group3 Version: v3 Notify View: group_notify - Not configured",
            ],
        },
    },
    (VerifySnmpGroup, "failure-group-version-not-configured"): {
        "eos_data": [{"groups": {"Group1": {"versions": {"v1": {}}}, "Group2": {"versions": {"v2c": {}}}, "Group3": {"versions": {"v3": {}}}}}],
        "inputs": {
            "snmp_groups": [
                {"group_name": "Group1", "version": "v1", "read_view": "group_read_1", "write_view": "group_write_1"},
                {"group_name": "Group2", "version": "v2c", "read_view": "group_read_2", "write_view": "group_write_2", "notify_view": "group_notify_2"},
                {
                    "group_name": "Group3",
                    "version": "v3",
                    "read_view": "group_read_3",
                    "write_view": "group_write_3",
                    "notify_view": "group_notify_3",
                    "authentication": "auth",
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Group: Group1 Version: v1 - Not configured", "Group: Group2 Version: v2c - Not configured", "Group: Group3 Version: v3 - Not configured"],
        },
    },
    (VerifySnmpGroup, "failure-incorrect-v3-auth-model"): {
        "eos_data": [
            {
                "groups": {
                    "Group3": {
                        "versions": {
                            "v3": {
                                "secModel": "v3Auth",
                                "readView": "group_read",
                                "readViewConfig": True,
                                "writeView": "group_write",
                                "writeViewConfig": True,
                                "notifyView": "group_notify",
                                "notifyViewConfig": True,
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {
            "snmp_groups": [
                {
                    "group_name": "Group3",
                    "version": "v3",
                    "read_view": "group_read",
                    "write_view": "group_write",
                    "notify_view": "group_notify",
                    "authentication": "priv",
                }
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Group: Group3 Version: v3 - Incorrect security model - Expected: v3Priv Actual: v3Auth"]},
    },
    (VerifySnmpGroup, "failure-view-not-configured"): {
        "eos_data": [
            {
                "groups": {
                    "Group3": {"versions": {"v3": {"secModel": "v3NoAuth", "readView": "group_read", "readViewConfig": True, "writeView": "", "notifyView": ""}}}
                }
            }
        ],
        "inputs": {"snmp_groups": [{"group_name": "Group3", "version": "v3", "read_view": "group_read", "write_view": "group_write", "authentication": "noauth"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Group: Group3 Version: v3 View: write - Not configured"]},
    },
}
