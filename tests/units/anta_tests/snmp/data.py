# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.snmp"""

from typing import Any, Dict, List

INPUT_SNMP_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['MGMT', 'default']},
                'enabled': True
            }
        ],
        "inputs": "MGMT",
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': True
            }
        ],
        "inputs": "MGMT",
        "expected": {"result": "failure", "messages": ["SNMP agent disabled in vrf MGMT"]}
    },
    {
        "name": "failure-disabled",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': False
            }
        ],
        "inputs": "default",
        "expected": {"result": "failure", "messages": ["SNMP agent disabled in vrf default"]}
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': True
            }
        ],
        "inputs": None,
        "expected_result": "skipped", "messages": ["VerifySnmpStatus did not run because vrf was not supplied"]
    },
]

INPUT_SNMP_IPV4_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": []
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "failure", "messages": ["Expected 1 SNMP IPv4 ACL(s) in vrf MGMT but got 0"]}
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SNMP",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "failure", "messages": ["SNMP IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_SNMP']"]}
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (1, None),
        "expected_result": "skipped", "messages": ["VerifySnmpIPv4Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (None, "MGMT"),
        "expected_result": "skipped", "messages": ["VerifySnmpIPv4Acl did not run because number or vrf was not supplied"]
    }
]

INPUT_SNMP_IPV6_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": []
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "failure", "messages": ["Expected 1 SNMP IPv6 ACL(s) in vrf MGMT but got 0"]}
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SNMP",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "inputs": (1, "MGMT"),
        "expected": {"result": "failure", "messages": ["SNMP IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_SNMP']"]}
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (1, None),
        "expected_result": "skipped", "messages": ["VerifySnmpIPv6Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SNMP",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "inputs": (None, "MGMT"),
        "expected_result": "skipped", "messages": ["VerifySnmpIPv6Acl did not run because number or vrf was not supplied"]
    }
]
