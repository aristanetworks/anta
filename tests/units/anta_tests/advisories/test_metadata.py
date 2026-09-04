# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Validate metadata shared by the published security-advisory tests."""

from datetime import date

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta.tests.advisories.sa_117 import VerifySA117
from anta.tests.advisories.sa_140 import VerifySA140
from anta.tests.advisories.sa_142 import VerifySA142
from anta.tests.advisories.sa_146 import VerifySA146
from anta.tests.advisories.sa_147 import VerifySA147


def test_published_advisory_metadata() -> None:
    """Verify stable identifiers, URLs, descriptions, and vulnerability metadata."""
    cases = (
        (
            VerifySA117,
            "0117",
            "21394-security-advisory-0117",
            date(2025, 5, 20),
            (
                (
                    "CVE-2025-0936",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "gNOI TransferToRemote credential exposure through OpenConfig accounting or tracing.",
                ),
            ),
        ),
        (
            VerifySA140,
            "0140",
            "24074-security-advisory-0140",
            date(2026, 6, 3),
            (
                (
                    "CVE-2026-10040",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "Secure Boot Software Image verification bypass.",
                ),
            ),
        ),
        (
            VerifySA142,
            "0142",
            "24111-security-advisory-0142",
            date(2026, 8, 10),
            (
                (
                    "CVE-2026-12546",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "Next-hop redirection bypass for packets requiring exception handling.",
                ),
            ),
        ),
        (
            VerifySA146,
            "0146",
            "24500-security-advisory-0146",
            date(2026, 8, 19),
            (
                (
                    "GHSA-hrxh-6v49-42gf",
                    _AdvisoryVulnerabilitySeverity.HIGH,
                    "HTTP/2 Rapid Reset denial-of-service rate-limit bypass in affected gRPC servers.",
                ),
            ),
        ),
        (
            VerifySA147,
            "0147",
            "24515-security-advisory-0147",
            date(2026, 9, 3),
            (
                (
                    "CVE-2026-59995",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "SFTP client issue when connecting to an untrusted server.",
                ),
                (
                    "CVE-2026-59996",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "SCP remote-to-remote client issue involving an untrusted server.",
                ),
                (
                    "CVE-2026-60001",
                    _AdvisoryVulnerabilitySeverity.MEDIUM,
                    "OpenSSH server issue affecting accepted SSH connections.",
                ),
                (
                    "CVE-2026-60002",
                    _AdvisoryVulnerabilitySeverity.CRITICAL,
                    "SSH client issue when connecting to a malicious or compromised server.",
                ),
            ),
        ),
    )

    for test_class, sa_number, url_suffix, last_updated, expected_vulnerabilities in cases:
        assert issubclass(test_class, _AntaAdvisoryTest)
        assert test_class.description == f"Verify whether the device is impacted by SA {sa_number}."
        assert test_class.advisory.sa_number == sa_number
        assert test_class.advisory.title == f"Security Advisory {sa_number}"
        assert test_class.advisory.url.endswith(url_suffix)
        assert test_class.advisory.last_updated == last_updated
        assert test_class.advisory.description
        assert tuple((item.id, item.severity, item.description) for item in test_class.advisory.vulnerabilities) == expected_vulnerabilities
