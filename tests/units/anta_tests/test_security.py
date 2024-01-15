# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

from typing import Any

from anta.tests.security import (
    VerifyAPIHttpsSSL,
    VerifyAPIHttpStatus,
    VerifyAPIIPv4Acl,
    VerifyAPIIPv6Acl,
    VerifyAPISSLCertificate,
    VerifyHostname,
    VerifySSHIPv4Acl,
    VerifySSHIPv6Acl,
    VerifySSHStatus,
    VerifyTelnetStatus,
)
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifySSHStatus,
        "eos_data": ["SSHD status for Default VRF is disabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySSHStatus,
        "eos_data": ["SSHD status for Default VRF is enabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["SSHD status for Default VRF is enabled"]},
    },
    {
        "name": "success",
        "test": VerifySSHIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SSH", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifySSHIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 SSH IPv4 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifySSHIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SSH", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["SSH IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_SSH']"]},
    },
    {
        "name": "success",
        "test": VerifySSHIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SSH", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifySSHIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 SSH IPv6 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifySSHIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SSH", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["SSH IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_SSH']"]},
    },
    {
        "name": "success",
        "test": VerifyTelnetStatus,
        "eos_data": [{"serverState": "disabled", "vrfName": "default", "maxTelnetSessions": 20, "maxTelnetSessionsPerHost": 20}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyTelnetStatus,
        "eos_data": [{"serverState": "enabled", "vrfName": "default", "maxTelnetSessions": 20, "maxTelnetSessionsPerHost": 20}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Telnet status for Default VRF is enabled"]},
    },
    {
        "name": "success",
        "test": VerifyAPIHttpStatus,
        "eos_data": [
            {
                "enabled": True,
                "httpServer": {"configured": False, "running": False, "port": 80},
                "localHttpServer": {"configured": False, "running": False, "port": 8080},
                "httpsServer": {"configured": True, "running": True, "port": 443},
                "unixSocketServer": {"configured": False, "running": False},
                "sslProfile": {"name": "API_SSL_Profile", "configured": True, "state": "valid"},
                "tlsProtocol": ["1.2"],
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyAPIHttpStatus,
        "eos_data": [
            {
                "enabled": True,
                "httpServer": {"configured": True, "running": True, "port": 80},
                "localHttpServer": {"configured": False, "running": False, "port": 8080},
                "httpsServer": {"configured": True, "running": True, "port": 443},
                "unixSocketServer": {"configured": False, "running": False},
                "sslProfile": {"name": "API_SSL_Profile", "configured": True, "state": "valid"},
                "tlsProtocol": ["1.2"],
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["eAPI HTTP server is enabled globally"]},
    },
    {
        "name": "success",
        "test": VerifyAPIHttpsSSL,
        "eos_data": [
            {
                "enabled": True,
                "httpServer": {"configured": False, "running": False, "port": 80},
                "localHttpServer": {"configured": False, "running": False, "port": 8080},
                "httpsServer": {"configured": True, "running": True, "port": 443},
                "unixSocketServer": {"configured": False, "running": False},
                "sslProfile": {"name": "API_SSL_Profile", "configured": True, "state": "valid"},
                "tlsProtocol": ["1.2"],
            }
        ],
        "inputs": {"profile": "API_SSL_Profile"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyAPIHttpsSSL,
        "eos_data": [
            {
                "enabled": True,
                "httpServer": {"configured": True, "running": True, "port": 80},
                "localHttpServer": {"configured": False, "running": False, "port": 8080},
                "httpsServer": {"configured": True, "running": True, "port": 443},
                "unixSocketServer": {"configured": False, "running": False},
                "tlsProtocol": ["1.2"],
            }
        ],
        "inputs": {"profile": "API_SSL_Profile"},
        "expected": {"result": "failure", "messages": ["eAPI HTTPS server SSL profile (API_SSL_Profile) is not configured"]},
    },
    {
        "name": "failure-misconfigured-invalid",
        "test": VerifyAPIHttpsSSL,
        "eos_data": [
            {
                "enabled": True,
                "httpServer": {"configured": True, "running": True, "port": 80},
                "localHttpServer": {"configured": False, "running": False, "port": 8080},
                "httpsServer": {"configured": True, "running": True, "port": 443},
                "unixSocketServer": {"configured": False, "running": False},
                "sslProfile": {"name": "Wrong_SSL_Profile", "configured": True, "state": "valid"},
                "tlsProtocol": ["1.2"],
            }
        ],
        "inputs": {"profile": "API_SSL_Profile"},
        "expected": {"result": "failure", "messages": ["eAPI HTTPS server SSL profile (API_SSL_Profile) is misconfigured or invalid"]},
    },
    {
        "name": "success",
        "test": VerifyAPIIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_API", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifyAPIIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 eAPI IPv4 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifyAPIIPv4Acl,
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_API", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["eAPI IPv4 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV4_API']"]},
    },
    {
        "name": "success",
        "test": VerifyAPIIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_API", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-number",
        "test": VerifyAPIIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Expected 1 eAPI IPv6 ACL(s) in vrf MGMT but got 0"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifyAPIIPv6Acl,
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_API", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["eAPI IPv6 ACL(s) not configured or active in vrf MGMT: ['ACL_IPV6_API']"]},
    },
    {
        "name": "success",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "ECDSA",
                            "size": 256,
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-certificate-not-configured",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "ECDSA",
                            "size": 256,
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["SSL certificate 'ARISTA_ROOT_CA.crt', is not configured.\n"],
        },
    },
    {
        "name": "failure-certificate-expired",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 1702533518,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                        },
                    },
                }
            },
            {
                "utcTime": 1702622372.2240553,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["SSL certificate 'ARISTA_SIGNING_CA.crt', is not configured.\n", "SSL certificate `ARISTA_ROOT_CA.crt` is expired.\n"],
        },
    },
    {
        "name": "failure-certificate-about-to-expire",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 1704782709,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 1702533518,
                        "publicKey": {
                            "encryptionAlgorithm": "ECDSA",
                            "size": 256,
                        },
                    },
                }
            },
            {
                "utcTime": 1702622372.2240553,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["SSL certificate `ARISTA_SIGNING_CA.crt` is expired.\n", "SSL certificate `ARISTA_ROOT_CA.crt` is about to expire in 25 days."],
        },
    },
    {
        "name": "failure-wrong-subject-name",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "Arista ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "ECDSA",
                            "size": 256,
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "SSL certificate `ARISTA_SIGNING_CA.crt` is not configured properly:\n"
                "Expected `AristaIT-ICA ECDSA Issuing Cert Authority` as the subject.commonName, but found "
                "`Arista ECDSA Issuing Cert Authority` instead.\n",
                "SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n"
                "Expected `Arista Networks Internal IT Root Cert Authority` as the subject.commonName, "
                "but found `AristaIT-ICA Networks Internal IT Root Cert Authority` instead.\n",
            ],
        },
    },
    {
        "name": "failure-wrong-encryption-type-and-size",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "ECDSA",
                            "size": 256,
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "SSL certificate `ARISTA_SIGNING_CA.crt` is not configured properly:\n"
                "Expected `ECDSA` as the publicKey.encryptionAlgorithm, but found `RSA` instead.\n"
                "Expected `256` as the publicKey.size, but found `4096` instead.\n",
                "SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n"
                "Expected `RSA` as the publicKey.encryptionAlgorithm, but found `ECDSA` instead.\n"
                "Expected `4096` as the publicKey.size, but found `256` instead.\n",
            ],
        },
    },
    {
        "name": "failure-missing-actual-output",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
            },
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "SSL certificate `ARISTA_SIGNING_CA.crt` is not configured properly:\n"
                "Expected `ECDSA` as the publicKey.encryptionAlgorithm, but it was not found in the actual output.\n"
                "Expected `256` as the publicKey.size, but it was not found in the actual output.\n",
                "SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n"
                "Expected `RSA` as the publicKey.encryptionAlgorithm, but it was not found in the actual output.\n"
                "Expected `4096` as the publicKey.size, but it was not found in the actual output.\n",
            ],
        },
    },
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
]
