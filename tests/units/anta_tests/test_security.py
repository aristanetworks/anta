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
                        "version": 3,
                        "serialNumber": 169201860180484611559425663013039682076,
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496268302,
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                            "modulus": 169201860180484611559425663013039682076,
                            "publicExponent": 65537,
                        },
                        "extension": {
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "subjectKeyIdentifier": {"value": "2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "version": 3,
                        "serialNumber": 490616394385765815676041936146238775981244419,
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496271268,
                        "notAfter": 1811804668,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256, "modulus": 0, "ellipticCurve": "prime256v1"},
                        "extension": {
                            "subjectKeyIdentifier": {"value": "73:B5:D7:47:5B:24:B8:4D:18:96:A4:B4:51:DC:1A:97:65:3F:7D:4A", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "authorityKeyIdentifier": {"value": "keyid:2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "crlDistributionPoints": {
                                "value": "Full Name:\n  URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOT.crl\n",
                                "critical": False,
                            },
                            "authorityInfoAccess": {
                                "value": "CA Issuers - URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOTArista%20Networks%20Internal%20IT%20Root%20Cert",
                                "critical": False,
                            },
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
                "timezone": "UTC",
                "localTime": {
                    "year": 2023,
                    "month": 12,
                    "dayOfMonth": 11,
                    "hour": 9,
                    "min": 54,
                    "sec": 27,
                    "dayOfWeek": 0,
                    "dayOfYear": 345,
                    "daylightSavingsAdjust": 0,
                },
                "clockSource": {"local": False, "ntpServer": "10.88.21.235"},
            },
        ],
        "inputs": {
            "certificate": "ARISTA_ROOT_CA.crt",
            "expiry_limit": 30,
            "subject_name": "Arista Networks Internal IT Root Cert Authority",
            "encryption": "RSA",
            "size": 4096,
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-wrong-subject-name",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "version": 3,
                        "serialNumber": 169201860180484611559425663013039682076,
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496268302,
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                            "modulus": 169201860180484611559425663013039682076,
                            "publicExponent": 65537,
                        },
                        "extension": {
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "subjectKeyIdentifier": {"value": "2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "version": 3,
                        "serialNumber": 490616394385765815676041936146238775981244419,
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496271268,
                        "notAfter": 1811804668,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256, "modulus": 0, "ellipticCurve": "prime256v1"},
                        "extension": {
                            "subjectKeyIdentifier": {"value": "73:B5:D7:47:5B:24:B8:4D:18:96:A4:B4:51:DC:1A:97:65:3F:7D:4A", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "authorityKeyIdentifier": {"value": "keyid:2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "crlDistributionPoints": {
                                "value": "Full Name:\n  URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOT.crl\n",
                                "critical": False,
                            },
                            "authorityInfoAccess": {
                                "value": "CA Issuers - URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOTArista%20Networks%20Internal%20IT%20Root%20Cert",
                                "critical": False,
                            },
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
                "timezone": "UTC",
                "localTime": {
                    "year": 2023,
                    "month": 12,
                    "dayOfMonth": 11,
                    "hour": 9,
                    "min": 54,
                    "sec": 27,
                    "dayOfWeek": 0,
                    "dayOfYear": 345,
                    "daylightSavingsAdjust": 0,
                },
                "clockSource": {"local": False, "ntpServer": "10.88.21.235"},
            },
        ],
        "inputs": {"certificate": "ARISTA_ROOT_CA.crt", "expiry_limit": 30, "subject_name": "self.signed", "encryption": "RSA", "size": 4096},
        "expected": {
            "result": "failure",
            "messages": [
                "The SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n"
                "Expected subject.commonName is `self.signed` however in actual found as `Arista Networks Internal IT Root Cert Authority`."
            ],
        },
    },
    {
        "name": "failure-wrong-encryption-type",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "version": 3,
                        "serialNumber": 169201860180484611559425663013039682076,
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496268302,
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                            "modulus": 169201860180484611559425663013039682076,
                            "publicExponent": 65537,
                        },
                        "extension": {
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "subjectKeyIdentifier": {"value": "2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "version": 3,
                        "serialNumber": 490616394385765815676041936146238775981244419,
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496271268,
                        "notAfter": 1811804668,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256, "modulus": 0, "ellipticCurve": "prime256v1"},
                        "extension": {
                            "subjectKeyIdentifier": {"value": "73:B5:D7:47:5B:24:B8:4D:18:96:A4:B4:51:DC:1A:97:65:3F:7D:4A", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "authorityKeyIdentifier": {"value": "keyid:2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "crlDistributionPoints": {
                                "value": "Full Name:\n  URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOT.crl\n",
                                "critical": False,
                            },
                            "authorityInfoAccess": {
                                "value": "CA Issuers - URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOTArista%20Networks%20Internal%20IT%20Root%20Cert",
                                "critical": False,
                            },
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
                "timezone": "UTC",
                "localTime": {
                    "year": 2023,
                    "month": 12,
                    "dayOfMonth": 11,
                    "hour": 9,
                    "min": 54,
                    "sec": 27,
                    "dayOfWeek": 0,
                    "dayOfYear": 345,
                    "daylightSavingsAdjust": 0,
                },
                "clockSource": {"local": False, "ntpServer": "10.88.21.235"},
            },
        ],
        "inputs": {
            "certificate": "ARISTA_ROOT_CA.crt",
            "expiry_limit": 30,
            "subject_name": "Arista Networks Internal IT Root Cert Authority",
            "encryption": "ECDSA",
            "size": 4096,
        },
        "expected": {
            "result": "failure",
            "messages": [
                "The SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n"
                "Expected publicKey.encryptionAlgorithm is `ECDSA` however in actual found as `RSA`."
            ],
        },
    },
    {
        "name": "failure-wrong-encryption-size",
        "test": VerifyAPISSLCertificate,
        "eos_data": [
            {
                "certificates": {
                    "ARISTA_ROOT_CA.crt": {
                        "version": 3,
                        "serialNumber": 169201860180484611559425663013039682076,
                        "subject": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496268302,
                        "notAfter": 2127420899,
                        "publicKey": {
                            "encryptionAlgorithm": "RSA",
                            "size": 4096,
                            "modulus": 169201860180484611559425663013039682076,
                            "publicExponent": 65537,
                        },
                        "extension": {
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "subjectKeyIdentifier": {"value": "2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                        },
                    },
                    "ARISTA_SIGNING_CA.crt": {
                        "version": 3,
                        "serialNumber": 490616394385765815676041936146238775981244419,
                        "subject": {"commonName": "AristaIT-ICA ECDSA Issuing Cert Authority"},
                        "issuer": {"commonName": "Arista Networks Internal IT Root Cert Authority"},
                        "notBefore": 1496271268,
                        "notAfter": 1811804668,
                        "publicKey": {"encryptionAlgorithm": "ECDSA", "size": 256, "modulus": 0, "ellipticCurve": "prime256v1"},
                        "extension": {
                            "subjectKeyIdentifier": {"value": "73:B5:D7:47:5B:24:B8:4D:18:96:A4:B4:51:DC:1A:97:65:3F:7D:4A", "critical": False},
                            "certificatePolicies": {
                                "value": "Policy: 1.3.6.1.2.1.17.7.1.4.2.1.3\n  CPS: http://it-pki.aristanetworks.com/pki/cps.html",
                                "critical": False,
                            },
                            "keyUsage": {"value": "Digital Signature, Certificate Sign, CRL Sign", "critical": False},
                            "basicConstraints": {"value": "CA:TRUE", "critical": True},
                            "authorityKeyIdentifier": {"value": "keyid:2D:EF:DA:E6:EF:CF:1C:77:51:BF:5A:02:A9:28:CD:94:00:AD:E1:CA", "critical": False},
                            "crlDistributionPoints": {
                                "value": "Full Name:\n  URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOT.crl\n",
                                "critical": False,
                            },
                            "authorityInfoAccess": {
                                "value": "CA Issuers - URI:http://it-pki.aristanetworks.com/pki/AristaIT-ROOTArista%20Networks%20Internal%20IT%20Root%20Cert",
                                "critical": False,
                            },
                        },
                    },
                }
            },
            {
                "utcTime": 1702288467.6736515,
                "timezone": "UTC",
                "localTime": {
                    "year": 2023,
                    "month": 12,
                    "dayOfMonth": 11,
                    "hour": 9,
                    "min": 54,
                    "sec": 27,
                    "dayOfWeek": 0,
                    "dayOfYear": 345,
                    "daylightSavingsAdjust": 0,
                },
                "clockSource": {"local": False, "ntpServer": "10.88.21.235"},
            },
        ],
        "inputs": {
            "certificate": "ARISTA_ROOT_CA.crt",
            "expiry_limit": 30,
            "subject_name": "Arista Networks Internal IT Root Cert Authority",
            "encryption": "RSA",
            "size": 2048,
        },
        "expected": {
            "result": "failure",
            "messages": [
                "The SSL certificate `ARISTA_ROOT_CA.crt` is not configured properly:\n" "Expected publicKey.size is `2048` however in actual found as `4096`."
            ],
        },
    },
]
