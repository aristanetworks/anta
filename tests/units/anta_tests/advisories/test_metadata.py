# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Validate metadata shared by the security-advisory tests."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.reporter.reporting import _get_advisory_severity
from anta.tests.advisories import _ADVISORY_TESTS
from anta.tests.advisories.sa_117 import SA117
from anta.tests.advisories.sa_140 import SA140
from anta.tests.advisories.sa_142 import SA142
from anta.tests.advisories.sa_146 import SA146
from anta.tests.advisories.sa_147 import SA147

if TYPE_CHECKING:
    import pytest

    from anta.device import AntaDevice


def test_published_advisory_metadata() -> None:
    """Verify stable identifiers, URLs, descriptions, and vulnerability metadata."""
    cases = (
        (
            SA117,
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
            SA140,
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
            SA142,
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
            SA146,
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
            SA147,
            "0147",
            "24515-security-advisory-0147",
            date(2026, 8, 31),
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
        assert test_class.description == f"Verify whether the device is impacted by Security Advisory {sa_number}."
        assert test_class.advisory.sa_number == sa_number
        assert test_class.advisory.title == f"Security Advisory {sa_number}"
        assert test_class.advisory.url.endswith(url_suffix)
        assert test_class.advisory.last_updated == last_updated
        assert test_class.advisory.description
        assert tuple((item.id, item.severity, item.description) for item in test_class.advisory.vulnerabilities) == expected_vulnerabilities


def test_published_advisories_emit_one_shared_preview_warning(caplog: pytest.LogCaptureFixture, device: AntaDevice) -> None:
    """Verify advisory tests emit one shared preview warning."""
    caplog.set_level(logging.WARNING)

    for test_class in _ADVISORY_TESTS:
        test_class(device)

    assert caplog.messages == ["Security Advisory tests are in preview"]


def test_sa148_advance_notice_severities() -> None:
    """Verify advisory severities for SA149-SA178 match the SA148 advance notice."""
    expected = {
        "0149": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0150": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0151": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0152": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0153": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0154": _AdvisoryVulnerabilitySeverity.HIGH,
        "0155": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0156": _AdvisoryVulnerabilitySeverity.CRITICAL,
        "0157": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0158": _AdvisoryVulnerabilitySeverity.CRITICAL,
        "0159": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0160": _AdvisoryVulnerabilitySeverity.HIGH,
        "0161": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0162": _AdvisoryVulnerabilitySeverity.CRITICAL,
        "0163": _AdvisoryVulnerabilitySeverity.HIGH,
        "0164": _AdvisoryVulnerabilitySeverity.HIGH,
        "0165": _AdvisoryVulnerabilitySeverity.HIGH,
        "0166": _AdvisoryVulnerabilitySeverity.HIGH,
        "0167": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0168": _AdvisoryVulnerabilitySeverity.HIGH,
        "0169": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0170": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0171": _AdvisoryVulnerabilitySeverity.HIGH,
        "0172": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0173": _AdvisoryVulnerabilitySeverity.HIGH,
        "0174": _AdvisoryVulnerabilitySeverity.CRITICAL,
        "0175": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0176": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0177": _AdvisoryVulnerabilitySeverity.MEDIUM,
        "0178": _AdvisoryVulnerabilitySeverity.MEDIUM,
    }
    actual = {
        test_class.advisory.sa_number: _get_advisory_severity(test_class.advisory)
        for test_class in _ADVISORY_TESTS
        if "0149" <= test_class.advisory.sa_number <= "0178"
    }

    assert actual == expected
