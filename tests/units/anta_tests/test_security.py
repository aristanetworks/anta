# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.security.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
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

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifySSHStatus, "success"): {
        "eos_data": ["SSHD status for Default VRF is disabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySSHStatus, "error-missing-ssh-status"): {
        "eos_data": ["SSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Could not find SSH status in returned output"]},
    },
    (VerifySSHStatus, "failure-ssh-enabled"): {
        "eos_data": ["SSHD status for Default VRF is enabled\nSSH connection limit is 50\nSSH per host connection limit is 20\nFIPS status: disabled\n\n"],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SSHD status for Default VRF is enabled"]},
    },
    (VerifySSHStatus, "success-4.32"): {
        "eos_data": [
            "User certificate authentication methods: none (neither trusted CA nor SSL profile configured)\n"
            "SSHD status for Default VRF: disabled\nSSH connection limit: 50\nSSH per host connection limit: 20\nFIPS status: disabled\n\n"
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySSHStatus, "failure-ssh-enabled-4.32"): {
        "eos_data": [
            "User certificate authentication methods: none (neither trusted CA nor SSL profile configured)\nSSHD status for Default VRF: enabled\n"
            "SSH connection limit: 50\nSSH per host connection limit: 20\nFIPS status: disabled\n\n"
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["SSHD status for Default VRF: enabled"]},
    },
    (VerifySSHIPv4Acl, "success"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SSH", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySSHIPv4Acl, "failure-wrong-number"): {
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - SSH IPv4 ACL(s) count mismatch - Expected: 1 Actual: 0"]},
    },
    (VerifySSHIPv4Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_SSH", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following SSH IPv4 ACL(s) not configured or active: ACL_IPV4_SSH"]},
    },
    (VerifySSHIPv6Acl, "success"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SSH", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySSHIPv6Acl, "failure-wrong-number"): {
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - SSH IPv6 ACL(s) count mismatch - Expected: 1 Actual: 0"]},
    },
    (VerifySSHIPv6Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_SSH", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following SSH IPv6 ACL(s) not configured or active: ACL_IPV6_SSH"]},
    },
    (VerifyTelnetStatus, "success"): {
        "eos_data": [{"serverState": "disabled", "vrfName": "default", "maxTelnetSessions": 20, "maxTelnetSessionsPerHost": 20}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTelnetStatus, "failure"): {
        "eos_data": [{"serverState": "enabled", "vrfName": "default", "maxTelnetSessions": 20, "maxTelnetSessionsPerHost": 20}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Telnet status for Default VRF is enabled"]},
    },
    (VerifyAPIHttpStatus, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAPIHttpStatus, "failure"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["eAPI HTTP server is enabled globally"]},
    },
    (VerifyAPIHttpsSSL, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAPIHttpsSSL, "failure-not-configured"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["eAPI HTTPS server SSL profile API_SSL_Profile is not configured"]},
    },
    (VerifyAPIHttpsSSL, "failure-misconfigured-invalid"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["eAPI HTTPS server SSL profile API_SSL_Profile is misconfigured or invalid"]},
    },
    (VerifyAPIIPv4Acl, "success"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_API", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAPIIPv4Acl, "failure-wrong-number"): {
        "eos_data": [{"ipAclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - eAPI IPv4 ACL(s) count mismatch - Expected: 1 Actual: 0"]},
    },
    (VerifyAPIIPv4Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipAclList": {"aclList": [{"type": "Ip4Acl", "name": "ACL_IPV4_API", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following eAPI IPv4 ACL(s) not configured or active: ACL_IPV4_API"]},
    },
    (VerifyAPIIPv6Acl, "success"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_API", "configuredVrfs": ["MGMT"], "activeVrfs": ["MGMT"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAPIIPv6Acl, "failure-wrong-number"): {
        "eos_data": [{"ipv6AclList": {"aclList": []}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - eAPI IPv6 ACL(s) count mismatch - Expected: 1 Actual: 0"]},
    },
    (VerifyAPIIPv6Acl, "failure-wrong-vrf"): {
        "eos_data": [{"ipv6AclList": {"aclList": [{"type": "Ip6Acl", "name": "ACL_IPV6_API", "configuredVrfs": ["default"], "activeVrfs": ["default"]}]}}],
        "inputs": {"number": 1, "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Following eAPI IPv6 ACL(s) not configured or active: ACL_IPV6_API"]},
    },
    (VerifyAPISSLCertificate, "success"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "RSA", "size": 4096},
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256},
                    },
                }
            },
            {"utcTime": 1702288467.6736515},
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAPISSLCertificate, "failure-certificate-not-configured"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256},
                    }
                }
            },
            {"utcTime": 1702288467.6736515},
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Certificate: ARISTA_ROOT_CA.crt - Not found"]},
    },
    (VerifyAPISSLCertificate, "failure-certificate-expired"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 1702533518,
                        "publicKey": {"encryptionAlgorithm": "RSA", "size": 4096},
                    }
                }
            },
            {"utcTime": 1702622372.2240553},
        ],
        "inputs": {
            "certificates": [
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                }
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Certificate: ARISTA_ROOT_CA.crt - certificate expired"]},
    },
    (VerifyAPISSLCertificate, "failure-certificate-about-to-expire"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 1704782709,
                        "publicKey": {"encryptionAlgorithm": "RSA", "size": 4096},
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 1705992709,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256},
                    },
                }
            },
            {"utcTime": 1702622372.2240553},
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
            "result": AntaTestStatus.FAILURE,
            "messages": ["Certificate: ARISTA_ROOT_CA.crt - set to expire within the threshold - Threshold: 30 days Actual: 25 days"],
        },
    },
    (VerifyAPISSLCertificate, "failure-wrong-subject-name"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "RSA", "size": 4096},
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "Arista ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256},
                    },
                }
            },
            {"utcTime": 1702288467.6736515},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Certificate: ARISTA_SIGNING_CA.crt - incorrect common name - "
                "Expected: AristaIT-ICA ECDSA Issuing Cert Authority Actual: Arista ECDSA Issuing Cert Authority",
                "Certificate: ARISTA_ROOT_CA.crt - incorrect common name - Expected: Arista Networks Internal IT "
                "Root Cert Authority Actual: AristaIT-ICA Networks Internal IT Root Cert Authority",
            ],
        },
    },
    (VerifyAPISSLCertificate, "failure-wrong-encryption-type-and-size"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256},
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "notAfter": 2127420899,
                        "publicKey": {"encryptionAlgorithm": "RSA", "size": 4096},
                    },
                }
            },
            {"utcTime": 1702288467.6736515},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Certificate: ARISTA_SIGNING_CA.crt - incorrect encryption algorithm - Expected: ECDSA Actual: RSA",
                "Certificate: ARISTA_SIGNING_CA.crt - incorrect public key - Expected: 256 Actual: 4096",
                "Certificate: ARISTA_ROOT_CA.crt - incorrect encryption algorithm - Expected: RSA Actual: ECDSA",
                "Certificate: ARISTA_ROOT_CA.crt - incorrect public key - Expected: 4096 Actual: 256",
            ],
        },
    },
    (VerifyAPISSLCertificate, "failure-missing-algorithm-details"): {
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {"subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"}, "notAfter": 2127420899},
                    "ARISTA_SIGNING_CA.crt": {"subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"}, "notAfter": 2127420899},
                }
            },
            {"utcTime": 1702288467.6736515},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Certificate: ARISTA_SIGNING_CA.crt - incorrect encryption algorithm - Expected: ECDSA Actual: Not found",
                "Certificate: ARISTA_SIGNING_CA.crt - incorrect public key - Expected: 256 Actual: Not found",
                "Certificate: ARISTA_ROOT_CA.crt - incorrect encryption algorithm - Expected: RSA Actual: Not found",
                "Certificate: ARISTA_ROOT_CA.crt - incorrect public key - Expected: 4096 Actual: Not found",
            ],
        },
    },
    (VerifyBannerLogin, "success"): {
        "eos_data": [
            {
                "loginBanner": (
                    "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0"
                    "\nthat can be found in the LICENSE file.\n"
                )
            }
        ],
        "inputs": {
            "login_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.\n"
            )
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerLogin, "success-multiline"): {
        "eos_data": [
            {
                "loginBanner": (
                    "Copyright (c) 2023-2024 Arista Networks, Inc.\n"
                    "                            Use of this source code is governed by the Apache License 2.0\n"
                    "                            that can be found in the LICENSE file.\n"
                )
            }
        ],
        "inputs": {
            "login_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\n                            "
                "Use of this source code is governed by the Apache License 2.0\n                            that can be found in the LICENSE file.\n"
            )
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerLogin, "success-leading-whitespaces"): {
        "eos_data": [{"loginBanner": "    Copyright (c) 2023-2024 Arista Networks, Inc.\n"}],
        "inputs": {"login_banner": "    Copyright (c) 2023-2024 Arista Networks, Inc.\n"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerLogin, "failure-incorrect-login-banner"): {
        "eos_data": [
            {
                "loginBanner": (
                    "Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                    "that can be found in the LICENSE file.\n"
                )
            }
        ],
        "inputs": {
            "login_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.\n"
            )
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                (
                    "Incorrect login banner configured - Expected: 'Copyright (c) 2023-2024 Arista Networks, Inc.\n"
                    "Use of this source code is governed by the Apache License 2.0\nthat can be found in the LICENSE file.\n'"
                    " Actual: 'Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0"
                    "\nthat can be found in the LICENSE file.\n'"
                )
            ],
        },
    },
    (VerifyBannerLogin, "failure-login-banner-not-configured"): {
        "eos_data": [{"loginBanner": ""}],
        "inputs": {
            "login_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.\n"
            )
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Login banner is not configured"]},
    },
    (VerifyBannerMotd, "success"): {
        "eos_data": [
            {
                "motd": (
                    "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                    "that can be found in the LICENSE file."
                )
            }
        ],
        "inputs": {
            "motd_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            )
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerMotd, "success-multiline"): {
        "eos_data": [
            {
                "motd": (
                    "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                    "that can be found in the LICENSE file.\n"
                )
            }
        ],
        "inputs": {
            "motd_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed "
                "by the Apache License 2.0\nthat can be found in the LICENSE file.\n"
            )
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerMotd, "success-leading-whitespaces"): {
        "eos_data": [{"motd": "    Copyright (c) 2023-2024 Arista Networks, Inc.\n"}],
        "inputs": {"motd_banner": ("    Copyright (c) 2023-2024 Arista Networks, Inc.\n")},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyBannerMotd, "failure-incorrect-motd-banner"): {
        "eos_data": [
            {
                "motd": (
                    "Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                    "that can be found in the LICENSE file.\n"
                )
            }
        ],
        "inputs": {
            "motd_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file.\n"
            )
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                (
                    "Incorrect MOTD banner configured - Expected: 'Copyright (c) 2023-2024 Arista Networks, Inc.\n"
                    "Use of this source code is governed by the Apache License 2.0\nthat can be found in the LICENSE file.\n' "
                    "Actual: 'Copyright (c) 2023 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                    "that can be found in the LICENSE file.\n'"
                )
            ],
        },
    },
    (VerifyBannerMotd, "failure-leading-whitespaces"): {
        "eos_data": [{"motd": "Copyright (c) 2023 Arista Networks, Inc.\n"}],
        "inputs": {"motd_banner": ("    Copyright (c) 2023-2024 Arista Networks, Inc.\n")},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                (
                    "Incorrect MOTD banner configured - Expected: '    Copyright (c) 2023-2024 Arista Networks, Inc.\n' "
                    "Actual: 'Copyright (c) 2023 Arista Networks, Inc.\n'"
                )
            ],
        },
    },
    (VerifyBannerMotd, "failure-login-banner-not-configured"): {
        "eos_data": [{"motd": ""}],
        "inputs": {
            "motd_banner": (
                "Copyright (c) 2023-2024 Arista Networks, Inc.\nUse of this source code is governed by the Apache License 2.0\n"
                "that can be found in the LICENSE file."
            )
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["MOTD banner is not configured"]},
    },
    (VerifyIPv4ACL, "success"): {
        "eos_data": [
            {
                "aclList": [
                    {
                        "name": "default-control-plane-acl",
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 30},
                        ],
                    },
                    {
                        "name": "LabTest",
                        "sequence": [{"text": "permit icmp any any", "sequenceNumber": 10}, {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 20}],
                    },
                ]
            }
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPv4ACL, "failure-no-acl-list"): {
        "eos_data": [{"aclList": []}],
        "inputs": {"ipv4_access_lists": [{"name": "default-control-plane-acl", "entries": [{"sequence": 10, "action": "permit icmp any any"}]}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No Access Control List (ACL) configured"]},
    },
    (VerifyIPv4ACL, "failure-acl-not-found"): {
        "eos_data": [
            {
                "aclList": [
                    {
                        "name": "default-control-plane-acl",
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 30},
                        ],
                    }
                ]
            }
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["ACL name: LabTest - Not configured"]},
    },
    (VerifyIPv4ACL, "failure-sequence-not-found"): {
        "eos_data": [
            {
                "aclList": [
                    {
                        "name": "default-control-plane-acl",
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 40},
                        ],
                    },
                    {
                        "name": "LabTest",
                        "sequence": [{"text": "permit icmp any any", "sequenceNumber": 10}, {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30}],
                    },
                ]
            }
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
            "result": AntaTestStatus.FAILURE,
            "messages": ["ACL name: default-control-plane-acl Sequence: 30 - Not configured", "ACL name: LabTest Sequence: 20 - Not configured"],
        },
    },
    (VerifyIPv4ACL, "failure-action-not-match"): {
        "eos_data": [
            {
                "aclList": [
                    {
                        "name": "default-control-plane-acl",
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 20},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30},
                        ],
                    },
                    {
                        "name": "LabTest",
                        "sequence": [{"text": "permit icmp any any", "sequenceNumber": 10}, {"text": "permit udp any any eq bfd ttl eq 255", "sequenceNumber": 20}],
                    },
                ]
            }
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "ACL name: default-control-plane-acl Sequence: 30 - action mismatch - "
                "Expected: permit udp any any eq bfd ttl eq 255 Actual: permit tcp any any range 5900 5910",
                "ACL name: LabTest Sequence: 20 - action mismatch - Expected: permit tcp any any range 5900 5910 Actual: permit udp any any eq bfd ttl eq 255",
            ],
        },
    },
    (VerifyIPv4ACL, "failure-all-type"): {
        "eos_data": [
            {
                "aclList": [
                    {
                        "name": "default-control-plane-acl",
                        "sequence": [
                            {"text": "permit icmp any any", "sequenceNumber": 10},
                            {"text": "permit ip any any tracked", "sequenceNumber": 40},
                            {"text": "permit tcp any any range 5900 5910", "sequenceNumber": 30},
                        ],
                    }
                ]
            }
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "ACL name: default-control-plane-acl Sequence: 20 - Not configured",
                "ACL name: default-control-plane-acl Sequence: 30 - action mismatch - "
                "Expected: permit udp any any eq bfd ttl eq 255 Actual: permit tcp any any range 5900 5910",
                "ACL name: LabTest - Not configured",
            ],
        },
    },
    (VerifyIPSecConnHealth, "success"): {
        "eos_data": [
            {
                "connections": {
                    "default-172.18.3.2-172.18.5.2-srcUnused-0": {"pathDict": {"path9": "Established"}},
                    "default-100.64.3.2-100.64.5.2-srcUnused-0": {"pathDict": {"path10": "Established"}},
                }
            }
        ],
        "inputs": {},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyIPSecConnHealth, "failure-no-connection"): {
        "eos_data": [{"connections": {}}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No IPv4 security connection configured"]},
    },
    (VerifyIPSecConnHealth, "failure-not-established"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Source: 172.18.3.2 Destination: 172.18.2.2 VRF: default - IPv4 security connection not established",
                "Source: 100.64.3.2 Destination: 100.64.5.2 VRF: Guest - IPv4 security connection not established",
            ],
        },
    },
    (VerifySpecificIPSecConn, "success-with-connection"): {
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
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Peer: 10.255.0.1 VRF: Guest Source: 100.64.3.2 Destination: 100.64.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Peer: 10.255.0.1 VRF: Guest Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifySpecificIPSecConn, "success-with-description"): {
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
                    "description": "Datacenter IPsec tunnel",
                    "vrf": "Guest",
                    "connections": [
                        {"source_address": "100.64.3.2", "destination_address": "100.64.2.2"},
                        {"source_address": "172.18.3.2", "destination_address": "172.18.2.2"},
                    ],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Peer: 10.255.0.1 (Datacenter IPsec tunnel) VRF: Guest Source: 100.64.3.2 Destination: 100.64.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Peer: 10.255.0.1 (Datacenter IPsec tunnel) VRF: Guest Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifySpecificIPSecConn, "success-without-connection"): {
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
        "inputs": {"ip_security_connections": [{"peer": "10.255.0.1", "vrf": "default"}]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 100.64.3.2 Destination: 100.64.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifySpecificIPSecConn, "failure-no-connection"): {
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
                {"peer": "10.255.0.1", "vrf": "default"},
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Peer: 10.255.0.1 VRF: default - Not configured"],
            "atomic_results": [
                {"description": "Peer: 10.255.0.1 VRF: default", "result": AntaTestStatus.FAILURE, "messages": ["Not configured"]},
                {
                    "description": "Peer: 10.255.0.2 VRF: DATA Source: 100.64.3.2 Destination: 100.64.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
                {
                    "description": "Peer: 10.255.0.2 VRF: DATA Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.SUCCESS,
                },
            ],
        },
    },
    (VerifySpecificIPSecConn, "failure-not-established"): {
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
                }
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
                {"peer": "10.255.0.1", "vrf": "default"},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Peer: 10.255.0.1 VRF: default Source: 172.18.3.2 Destination: 172.18.2.2 - Connection down - Expected: Established Actual: Idle",
                "Peer: 10.255.0.1 VRF: default Source: 100.64.2.2 Destination: 100.64.1.2 - Connection down - Expected: Established Actual: Idle",
                "Peer: 10.255.0.2 VRF: MGMT Source: 100.64.2.2 Destination: 100.64.1.2 - Connection down - Expected: Established Actual: Idle",
                "Peer: 10.255.0.2 VRF: MGMT Source: 172.18.2.2 Destination: 172.18.1.2 - Connection down - Expected: Established Actual: Idle",
            ],
            "atomic_results": [
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 100.64.2.2 Destination: 100.64.1.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
                {
                    "description": "Peer: 10.255.0.2 VRF: MGMT Source: 100.64.2.2 Destination: 100.64.1.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
                {
                    "description": "Peer: 10.255.0.2 VRF: MGMT Source: 172.18.2.2 Destination: 172.18.1.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
            ],
        },
    },
    (VerifySpecificIPSecConn, "failure-missing-connection"): {
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
                }
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
                {"peer": "10.255.0.1", "vrf": "default"},
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Peer: 10.255.0.1 VRF: default Source: 172.18.3.2 Destination: 172.18.2.2 - Connection down - Expected: Established Actual: Idle",
                "Peer: 10.255.0.1 VRF: default Source: 100.64.3.2 Destination: 100.64.2.2 - Connection down - Expected: Established Actual: Idle",
                "Peer: 10.255.0.2 VRF: default Source: 100.64.4.2 Destination: 100.64.1.2 - Connection not found",
                "Peer: 10.255.0.2 VRF: default Source: 172.18.4.2 Destination: 172.18.1.2 - Connection not found",
            ],
            "atomic_results": [
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 172.18.3.2 Destination: 172.18.2.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
                {
                    "description": "Peer: 10.255.0.1 VRF: default Source: 100.64.3.2 Destination: 100.64.2.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection down - Expected: Established Actual: Idle"],
                },
                {
                    "description": "Peer: 10.255.0.2 VRF: default Source: 100.64.4.2 Destination: 100.64.1.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection not found"],
                },
                {
                    "description": "Peer: 10.255.0.2 VRF: default Source: 172.18.4.2 Destination: 172.18.1.2",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Connection not found"],
                },
            ],
        },
    },
    (VerifyHardwareEntropy, "success"): {
        "eos_data": [{"cpuModel": "2.20GHz", "cryptoModule": "Crypto Module v3.0", "hardwareEntropyEnabled": True, "blockedNetworkProtocols": []}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyHardwareEntropy, "failure"): {
        "eos_data": [{"cpuModel": "2.20GHz", "cryptoModule": "Crypto Module v3.0", "hardwareEntropyEnabled": False, "blockedNetworkProtocols": []}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Hardware entropy generation is disabled"]},
    },
}


class TestAPISSLCertificate:
    """Test anta.tests.security.VerifyAPISSLCertificate.Input.APISSLCertificate."""

    @pytest.mark.parametrize(
        ("model_params", "error"),
        [
            pytest.param(
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 256,
                },
                "Value error, `ARISTA_ROOT_CA.crt` key size 256 is invalid for RSA encryption. Allowed sizes are (2048, 3072, 4096).",
                id="RSA_wrong_size",
            ),
            pytest.param(
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 2048,
                },
                "Value error, `ARISTA_SIGNING_CA.crt` key size 2048 is invalid for ECDSA encryption. Allowed sizes are (256, 384, 512).",
                id="ECDSA_wrong_size",
            ),
        ],
    )
    def test_invalid(self, model_params: dict[str, Any], error: str) -> None:
        """Test invalid inputs for anta.tests.security.VerifyAPISSLCertificate.Input.APISSLCertificate."""
        with pytest.raises(ValidationError) as exec_info:
            VerifyAPISSLCertificate.Input.APISSLCertificate.model_validate(model_params)
        assert error == exec_info.value.errors()[0]["msg"]

    @pytest.mark.parametrize(
        "model_params",
        [
            pytest.param(
                {
                    "certificate_name": "ARISTA_SIGNING_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "AristaIT-ICA ECDSA Issuing Cert Authority",
                    "encryption_algorithm": "ECDSA",
                    "key_size": 256,
                },
                id="ECDSA",
            ),
            pytest.param(
                {
                    "certificate_name": "ARISTA_ROOT_CA.crt",
                    "expiry_threshold": 30,
                    "common_name": "Arista Networks Internal IT Root Cert Authority",
                    "encryption_algorithm": "RSA",
                    "key_size": 4096,
                },
                id="RSA",
            ),
        ],
    )
    def test_valid(self, model_params: dict[str, Any]) -> None:
        """Test valid inputs for anta.tests.security.VerifyAPISSLCertificate.Input.APISSLCertificate."""
        VerifyAPISSLCertificate.Input.APISSLCertificate.model_validate(model_params)
