"""Data for testing anta.tests.security"""

from typing import Any, Dict, List

INPUT_SSH_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            "SSHD status for Default VRF is disabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            "SSHD status for Default VRF is enabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["SSHD status for Default VRF is enabled"]
    },
]

INPUT_SSH_IPV4_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SSH",
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
        "expected_messages": ["Expected 1 SSH IPv4 ACL(s) in vrf MGMT but got 0"]
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SSH",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["SSH IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_SSH']"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SSH",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifySSHIPv4Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_SSH",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifySSHIPv4Acl did not run because number or vrf was not supplied"]
    }
]

INPUT_SSH_IPV6_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SSH",
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
        "expected_messages": ["Expected 1 SSH IPv6 ACL(s) in vrf MGMT but got 0"]
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SSH",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["SSH IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_SSH']"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SSH",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifySSHIPv6Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_SSH",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifySSHIPv6Acl did not run because number or vrf was not supplied"]
    }
]

INPUT_TELNET_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                'serverState': 'disabled',
                'vrfName': 'default',
                'maxTelnetSessions': 20,
                'maxTelnetSessionsPerHost': 20
            }
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
                'serverState': 'enabled',
                'vrfName': 'default',
                'maxTelnetSessions': 20,
                'maxTelnetSessionsPerHost': 20
            }
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["Telnet status for Default VRF is enabled"]
    },
]

INPUT_HTTP_STATUS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': False, 'running': False, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'sslProfile': {'name': 'API_SSL_Profile', 'configured': True, 'state': 'valid'},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": None,
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': True, 'running': True, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'sslProfile': {'name': 'API_SSL_Profile', 'configured': True, 'state': 'valid'},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": None,
        "expected_result": "failure",
        "expected_messages": ["eAPI HTTP server is enabled globally"]
    },
]

INPUT_HTTPS_SSL_PROFILE: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': False, 'running': False, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'sslProfile': {'name': 'API_SSL_Profile', 'configured': True, 'state': 'valid'},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": "API_SSL_Profile",
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': True, 'running': True, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": "API_SSL_Profile",
        "expected_result": "failure",
        "expected_messages": ["eAPI HTTPS server SSL profile (API_SSL_Profile) is not configured"]
    },
    {
        "name": "failure-misconfigured-invalid",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': True, 'running': True, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'sslProfile': {'name': 'Wrong_SSL_Profile', 'configured': True, 'state': 'valid'},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": "API_SSL_Profile",
        "expected_result": "failure",
        "expected_messages": ["eAPI HTTPS server SSL profile (API_SSL_Profile) is misconfigured or invalid"]
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                'enabled': True,
                'httpServer': {'configured': True, 'running': True, 'port': 80},
                'localHttpServer': {'configured': False, 'running': False, 'port': 8080},
                'httpsServer': {'configured': True, 'running': True, 'port': 443},
                'unixSocketServer': {'configured': False, 'running': False},
                'sslProfile': {'name': 'API_SSL_Profile', 'configured': True, 'state': 'valid'},
                'tlsProtocol': ['1.2']
            }
        ],
        "side_effect": None,
        "expected_result": "skipped",
        "expected_messages": ["VerifyAPIHttpsSSL did not run because profile was not supplied"]
    },
]

INPUT_API_IPV4_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_API",
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
        "expected_messages": ["Expected 1 eAPI IPv4 ACL(s) in vrf MGMT but got 0"]
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_API",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["eAPI IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_API']"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_API",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAPIIPv4Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipAclList": {
                    "aclList": [{
                        "type": "Ip4Acl",
                        "name": "ACL_IPV4_API",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAPIIPv4Acl did not run because number or vrf was not supplied"]
    }
]

INPUT_API_IPV6_ACL: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_API",
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
        "expected_messages": ["Expected 1 eAPI IPv6 ACL(s) in vrf MGMT but got 0"]
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_API",
                        "configuredVrfs": ["default"],
                        "activeVrfs": ["default"]
                    }]
                }
            }
        ],
        "side_effect": (1, "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["eAPI IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_API']"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_API",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (1, None),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAPIIPv6Acl did not run because number or vrf was not supplied"]
    },
    {
        "name": "skipped-no-number",
        "eos_data": [
            {
                "ipv6AclList": {
                    "aclList": [{
                        "type": "Ip6Acl",
                        "name": "ACL_IPV6_API",
                        "configuredVrfs": ["MGMT"],
                        "activeVrfs": ["MGMT"]
                    }]
                }
            }
        ],
        "side_effect": (None, "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAPIIPv6Acl did not run because number or vrf was not supplied"]
    }
]
