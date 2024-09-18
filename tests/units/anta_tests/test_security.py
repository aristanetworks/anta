# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.security.py."""

from __future__ import annotations

from typing import Any

from anta.tests.security import (
    VerifyAPIHttpsSSL,
    VerifyAPIHttpStatus,
    VerifyAPIIPv4Acl,
    VerifyAPIIPv6Acl,
    VerifyAPISSLCertificate,
    VerifyBannerLogin,
    VerifyBannerMotd,
    VerifyHardwareEntropy,
    VerifyIPSecConnHealth,
    VerifyIPv4ACL,
    VerifySpecificIPSecConn,
    VerifySSHIPv4Acl,
    VerifySSHIPv6Acl,
    VerifySSHStatus,
    VerifyTelnetStatus,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifySSHStatus,
        "eos_data": ["SSHD status for Default VRF is disabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "error-missing-ssh-status",
        "test": VerifySSHStatus,
        "eos_data": ["SSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "inputs": None,
        "expected": {"result": "error", "messages": ["Could not find SSH status in returned output."]},
    },
    {
        "name": "failure-ssh-disabled",
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
            },
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
            },
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
            },
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
            },
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
            },
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
        "name": "error-wrong-input-rsa",
        "test": VerifyAPISSLCertificate,
        "eos_data": [],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 256,
                },
            ]
        },
        "expected": {"result": "error", "messages": ["Allowed sizes are (2048, 3072, 4096)."]},
    },
    {
        "name": "error-wrong-input-ecdsa",
        "test": VerifyAPISSLCertificate,
        "eos_data": [],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 2048,
                },
            ]
        },
        "expected": {"result": "error", "messages": ["Allowed sizes are (256, 384, 512)."]},
    },
    {
        "name": "success",
        "test": VerifyBannerLogin,
        "eos_data": [
            {
                "loginBanner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "login_banner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
            "that can be found in the LICENSE file."
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiline",
        "test": VerifyBannerLogin,
        "eos_data": [
            {
                "loginBanner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "login_banner": """Copyright (c) 2023-2024 Arista Networks, Inc.
                            Use of this source code is governed by the Apache License 2.0
                            that can be found in the LICENSE file."""
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-login-banner",
        "test": VerifyBannerLogin,
        "eos_data": [
            {
                "loginBanner": "Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "login_banner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
            "that can be found in the LICENSE file."
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Expected `Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.` as the login banner, but found `Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is "
                "governed by the Apache License 2.0\nthat can be found in the LICENSE file.` instead."
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyBannerMotd,
        "eos_data": [
            {
                "motd": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "motd_banner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
            "that can be found in the LICENSE file."
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-multiline",
        "test": VerifyBannerMotd,
        "eos_data": [
            {
                "motd": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "motd_banner": """Copyright (c) 2023-2024 Arista Networks, Inc.
                            Use of this source code is governed by the Apache License 2.0
                            that can be found in the LICENSE file."""
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-motd-banner",
        "test": VerifyBannerMotd,
        "eos_data": [
            {
                "motd": "Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            }
        ],
        "inputs": {
            "motd_banner": "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
            "that can be found in the LICENSE file."
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Expected `Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.` as the motd banner, but found `Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is "
                "governed by the Apache License 2.0\nthat can be found in the LICENSE file.` instead."
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyIPv4ACL,
        "eos_data": [
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 30},
                        ],
                    }
                ]
            },
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 20},
                        ],
                    }
                ]
            },
        ],
        "inputs": {
            "ipv4_access_lists": [
                {
                    "name": "default-control-plane-acl",
                    "entries": [
                        {"sequence": 10, "action": "permit icmp any any"},
                        {"sequence": 20, "action": "permit ip any any tracked"},
                        {"sequence": 30, "action": "permit udp any any eq bfd ttl eq 255"},
                    ],
                },
                {
                    "name": "LabTest",
                    "entries": [{"sequence": 10, "action": "permit icmp any any"}, {"sequence": 20, "action": "permit tcp any any range 5900 5910"}],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-acl-not-found",
        "test": VerifyIPv4ACL,
        "eos_data": [
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 30},
                        ],
                    }
                ]
            },
            {"aclList": []},
        ],
        "inputs": {
            "ipv4_access_lists": [
                {
                    "name": "default-control-plane-acl",
                    "entries": [
                        {"sequence": 10, "action": "permit icmp any any"},
                        {"sequence": 20, "action": "permit ip any any tracked"},
                        {"sequence": 30, "action": "permit udp any any eq bfd ttl eq 255"},
                    ],
                },
                {
                    "name": "LabTest",
                    "entries": [{"sequence": 10, "action": "permit icmp any any"}, {"sequence": 20, "action": "permit tcp any any range 5900 5910"}],
                },
            ]
        },
        "expected": {"result": "failure", "messages": ["LabTest: Not found"]},
    },
    {
        "name": "failure-sequence-not-found",
        "test": VerifyIPv4ACL,
        "eos_data": [
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 40},
                        ],
                    }
                ]
            },
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30},
                        ],
                    }
                ]
            },
        ],
        "inputs": {
            "ipv4_access_lists": [
                {
                    "name": "default-control-plane-acl",
                    "entries": [
                        {"sequence": 10, "action": "permit icmp any any"},
                        {"sequence": 20, "action": "permit ip any any tracked"},
                        {"sequence": 30, "action": "permit udp any any eq bfd ttl eq 255"},
                    ],
                },
                {
                    "name": "LabTest",
                    "entries": [{"sequence": 10, "action": "permit icmp any any"}, {"sequence": 20, "action": "permit tcp any any range 5900 5910"}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["default-control-plane-acl:\nSequence number `30` is not found.\n", "LabTest:\nSequence number `20` is not found.\n"],
        },
    },
    {
        "name": "failure-action-not-match",
        "test": VerifyIPv4ACL,
        "eos_data": [
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30},
                        ],
                    }
                ]
            },
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 20},
                        ],
                    }
                ]
            },
        ],
        "inputs": {
            "ipv4_access_lists": [
                {
                    "name": "default-control-plane-acl",
                    "entries": [
                        {"sequence": 10, "action": "permit icmp any any"},
                        {"sequence": 20, "action": "permit ip any any tracked"},
                        {"sequence": 30, "action": "permit udp any any eq bfd ttl eq 255"},
                    ],
                },
                {
                    "name": "LabTest",
                    "entries": [{"sequence": 10, "action": "permit icmp any any"}, {"sequence": 20, "action": "permit tcp any any range 5900 5910"}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "default-control-plane-acl:\n"
                "Expected `permit udp any any eq bfd ttl eq 255` as sequence number 30 action but found `permit tcp any any range 5900 5910` instead.\n",
                "LabTest:\nExpected `permit tcp any any range 5900 5910` as sequence number 20 action but found `permit udp any any eq bfd ttl eq 255` instead.\n",
            ],
        },
    },
    {
        "name": "failure-all-type",
        "test": VerifyIPv4ACL,
        "eos_data": [
            {
                "aclList": [
                    {
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 40},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30},
                        ],
                    }
                ]
            },
            {"aclList": []},
        ],
        "inputs": {
            "ipv4_access_lists": [
                {
                    "name": "default-control-plane-acl",
                    "entries": [
                        {"sequence": 10, "action": "permit icmp any any"},
                        {"sequence": 20, "action": "permit ip any any tracked"},
                        {"sequence": 30, "action": "permit udp any any eq bfd ttl eq 255"},
                    ],
                },
                {
                    "name": "LabTest",
                    "entries": [{"sequence": 10, "action": "permit icmp any any"}, {"sequence": 20, "action": "permit tcp any any range 5900 5910"}],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "default-control-plane-acl:\nSequence number `20` is not found.\n"
                "Expected `permit udp any any eq bfd ttl eq 255` as sequence number 30 action but found `permit tcp any any range 5900 5910` instead.\n",
                "LabTest: Not found",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyIPSecConnHealth,
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.5.2-srcUnused-0": {
                        "pathDict": {"path9": "Established"},
                    },
                    "default-100.64.3.2-100.64.5.2-srcUnused-0": {
                        "pathDict": {"path10": "Established"},
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-connection",
        "test": VerifyIPSecConnHealth,
        "eos_data": [{"connections": {}}],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["No IPv4 security connection configured."]},
    },
    {
        "name": "failure-not-established",
        "test": VerifyIPSecConnHealth,
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.5.2-srcUnused-0": {
                        "pathDict": {"path9": "Idle"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "default",
                    },
                    "Guest-100.64.3.2-100.64.5.2-srcUnused-0": {"pathDict": {"path10": "Idle"}, "saddr": "100.64.3.2", "daddr": "100.64.5.2", "tunnelNs": "Guest"},
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "The following IPv4 security connections are not established:\n"
                "source:172.18.3.2 destination:172.18.2.2 vrf:default\n"
                "source:100.64.3.2 destination:100.64.5.2 vrf:Guest."
            ],
        },
    },
    {
        "name": "success-with-connection",
        "test": VerifySpecificIPSecConn,
        "eos_data": [
            {
                "connections": {
                    "Guest-172.18.3.2-172.18.2.2-srcUnused-0": {
                        "pathDict": {"path9": "Established"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "Guest",
                    },
                    "Guest-100.64.3.2-100.64.2.2-srcUnused-0": {
                        "pathDict": {"path10": "Established"},
                        "saddr": "100.64.3.2",
                        "daddr": "100.64.2.2",
                        "tunnelNs": "Guest",
                    },
                }
            }
        ],
        "inputs": {
            "ip_security_connections": [
                {
                    "peer": "10.255.0.1",
                    "vrf": "Guest",
                    "connections": [
                        {"source_address": "100.64.3.2", "destination_address": "100.64.2.2"},
                        {"source_address": "172.18.3.2", "destination_address": "172.18.2.2"},
                    ],
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "success-without-connection",
        "test": VerifySpecificIPSecConn,
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.2.2-srcUnused-0": {
                        "pathDict": {"path9": "Established"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "default",
                    },
                    "default-100.64.3.2-100.64.2.2-srcUnused-0": {"pathDict": {"path10": "Established"}, "saddr": "100.64.3.2", "daddr": "100.64.2.2"},
                }
            }
        ],
        "inputs": {
            "ip_security_connections": [
                {
                    "peer": "10.255.0.1",
                    "vrf": "default",
                },
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-connection",
        "test": VerifySpecificIPSecConn,
        "eos_data": [
            {"connections": {}},
            {
                "connections": {
                    "DATA-172.18.3.2-172.18.2.2-srcUnused-0": {
                        "pathDict": {"path9": "Established"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "DATA",
                    },
                    "DATA-100.64.3.2-100.64.2.2-srcUnused-0": {
                        "pathDict": {"path10": "Established"},
                        "saddr": "100.64.3.2",
                        "daddr": "100.64.2.2",
                        "tunnelNs": "DATA",
                    },
                }
            },
        ],
        "inputs": {
            "ip_security_connections": [
                {
                    "peer": "10.255.0.1",
                    "vrf": "default",
                },
                {
                    "peer": "10.255.0.2",
                    "vrf": "DATA",
                    "connections": [
                        {"source_address": "100.64.3.2", "destination_address": "100.64.2.2"},
                        {"source_address": "172.18.3.2", "destination_address": "172.18.2.2"},
                    ],
                },
            ]
        },
        "expected": {"result": "failure", "messages": ["No IPv4 security connection configured for peer `10.255.0.1`."]},
    },
    {
        "name": "failure-not-established",
        "test": VerifySpecificIPSecConn,
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.5.2-srcUnused-0": {
                        "pathDict": {"path9": "Idle"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "default",
                    },
                    "default-100.64.3.2-100.64.5.2-srcUnused-0": {
                        "pathDict": {"path10": "Idle"},
                        "saddr": "100.64.2.2",
                        "daddr": "100.64.1.2",
                        "tunnelNs": "default",
                    },
                },
            },
            {
                "connections": {
                    "MGMT-172.18.2.2-172.18.1.2-srcUnused-0": {"pathDict": {"path9": "Idle"}, "saddr": "172.18.2.2", "daddr": "172.18.1.2", "tunnelNs": "MGMT"},
                    "MGMT-100.64.2.2-100.64.1.2-srcUnused-0": {"pathDict": {"path10": "Idle"}, "saddr": "100.64.2.2", "daddr": "100.64.1.2", "tunnelNs": "MGMT"},
                }
            },
        ],
        "inputs": {
            "ip_security_connections": [
                {
                    "peer": "10.255.0.1",
                    "vrf": "default",
                },
                {
                    "peer": "10.255.0.2",
                    "vrf": "MGMT",
                    "connections": [
                        {"source_address": "100.64.2.2", "destination_address": "100.64.1.2"},
                        {"source_address": "172.18.2.2", "destination_address": "172.18.1.2"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Expected state of IPv4 security connection `source:172.18.3.2 destination:172.18.2.2 vrf:default` for peer `10.255.0.1` is `Established` "
                "but found `Idle` instead.",
                "Expected state of IPv4 security connection `source:100.64.2.2 destination:100.64.1.2 vrf:default` for peer `10.255.0.1` is `Established` "
                "but found `Idle` instead.",
                "Expected state of IPv4 security connection `source:100.64.2.2 destination:100.64.1.2 vrf:MGMT` for peer `10.255.0.2` is `Established` "
                "but found `Idle` instead.",
                "Expected state of IPv4 security connection `source:172.18.2.2 destination:172.18.1.2 vrf:MGMT` for peer `10.255.0.2` is `Established` "
                "but found `Idle` instead.",
            ],
        },
    },
    {
        "name": "failure-missing-connection",
        "test": VerifySpecificIPSecConn,
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.5.2-srcUnused-0": {
                        "pathDict": {"path9": "Idle"},
                        "saddr": "172.18.3.2",
                        "daddr": "172.18.2.2",
                        "tunnelNs": "default",
                    },
                    "default-100.64.3.2-100.64.5.2-srcUnused-0": {
                        "pathDict": {"path10": "Idle"},
                        "saddr": "100.64.3.2",
                        "daddr": "100.64.2.2",
                        "tunnelNs": "default",
                    },
                },
            },
            {
                "connections": {
                    "default-172.18.2.2-172.18.1.2-srcUnused-0": {
                        "pathDict": {"path9": "Idle"},
                        "saddr": "172.18.2.2",
                        "daddr": "172.18.1.2",
                        "tunnelNs": "default",
                    },
                    "default-100.64.2.2-100.64.1.2-srcUnused-0": {
                        "pathDict": {"path10": "Idle"},
                        "saddr": "100.64.2.2",
                        "daddr": "100.64.1.2",
                        "tunnelNs": "default",
                    },
                }
            },
        ],
        "inputs": {
            "ip_security_connections": [
                {
                    "peer": "10.255.0.1",
                    "vrf": "default",
                },
                {
                    "peer": "10.255.0.2",
                    "vrf": "default",
                    "connections": [
                        {"source_address": "100.64.4.2", "destination_address": "100.64.1.2"},
                        {"source_address": "172.18.4.2", "destination_address": "172.18.1.2"},
                    ],
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Expected state of IPv4 security connection `source:172.18.3.2 destination:172.18.2.2 vrf:default` for peer `10.255.0.1` is `Established` "
                "but found `Idle` instead.",
                "Expected state of IPv4 security connection `source:100.64.3.2 destination:100.64.2.2 vrf:default` for peer `10.255.0.1` is `Established` "
                "but found `Idle` instead.",
                "IPv4 security connection `source:100.64.4.2 destination:100.64.1.2 vrf:default` for peer `10.255.0.2` is not found.",
                "IPv4 security connection `source:172.18.4.2 destination:172.18.1.2 vrf:default` for peer `10.255.0.2` is not found.",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyHardwareEntropy,
        "eos_data": [{"cpuModel": "2.20GHz", "cryptoModule": "Crypto Module v3.0", "hardwareEntropyEnabled": True, "blockedNetworkProtocols": []}],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyHardwareEntropy,
        "eos_data": [{"cpuModel": "2.20GHz", "cryptoModule": "Crypto Module v3.0", "hardwareEntropyEnabled": False, "blockedNetworkProtocols": []}],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["Hardware entropy generation is disabled."]},
    },
]
