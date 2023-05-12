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
        "side_effect": "MGMT",
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': True
            }
        ],
        "side_effect": "MGMT",
        "expected_result": "failure",
        "expected_messages": ["SNMP agent disabled in vrf MGMT"]
    },
    {
        "name": "failure-disabled",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': False
            }
        ],
        "side_effect": "default",
        "expected_result": "failure",
        "expected_messages": ["SNMP agent disabled in vrf default"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                'vrfs': {'snmpVrfs': ['default']},
                'enabled': True
            }
        ],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifySnmpStatus did not run because vrf was not supplied"]
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
        "side_effect": (1, "MGMT"),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Expected 1 SNMP IPv4 ACL(s) in vrf MGMT but got 0"]
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
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["SNMP IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_SNMP']"]
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
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifySnmpIPv4Acl did not run because number or vrf was not supplied"]
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
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifySnmpIPv4Acl did not run because number or vrf was not supplied"]
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
        "side_effect": (1, "MGMT"),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Expected 1 SNMP IPv6 ACL(s) in vrf MGMT but got 0"]
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
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["SNMP IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_SNMP']"]
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
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifySnmpIPv6Acl did not run because number or vrf was not supplied"]
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
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifySnmpIPv6Acl did not run because number or vrf was not supplied"]
    }
]
