# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anta._advisory.models import (
    AdvisoryCVE,
    AdvisoryMetadata,
    AdvisoryResolution,
    AdvisorySeverity,
)

_BASE_ADVISORY_FIELDS = {
    "sa_number": "0001",
    "title": "Test advisory",
    "url": "https://example.com/advisory",
    "description": "Test advisory description.",
    "resolutions": (
        AdvisoryResolution(
            name="Upgrade",
            details="Upgrade to a fixed release.",
            url="https://example.com/resolution",
        ),
    ),
}


def test_advisory_metadata_accepts_severity_at_or_above_cve_severity() -> None:
    """Verify advisory severity may match or exceed the highest CVE severity."""
    AdvisoryMetadata(
        **_BASE_ADVISORY_FIELDS,
        severity=AdvisorySeverity.HIGH,
        cves=(
            AdvisoryCVE(cve_id="CVE-2026-0001", severity=AdvisorySeverity.MEDIUM),
            AdvisoryCVE(cve_id="CVE-2026-0002", severity=AdvisorySeverity.HIGH),
        ),
    )


def test_advisory_metadata_rejects_severity_below_cve_severity() -> None:
    """Verify advisory severity cannot be lower than an included CVE."""
    cve1 = AdvisoryCVE(cve_id="CVE-2026-0001", severity=AdvisorySeverity.MEDIUM)
    cve2 = AdvisoryCVE(cve_id="CVE-2026-0002", severity=AdvisorySeverity.HIGH)
    with pytest.raises(ValidationError, match=f"cannot be below CVE '{cve2.cve_id}' severity '{cve2.severity.value}'"):
        AdvisoryMetadata(**_BASE_ADVISORY_FIELDS, severity=AdvisorySeverity.MEDIUM, cves=(cve1, cve2))


def test_advisory_metadata_allows_empty_cve_list() -> None:
    """Verify advisory severity is not validated when no CVEs are included."""
    AdvisoryMetadata(
        **_BASE_ADVISORY_FIELDS,
        severity=AdvisorySeverity.LOW,
        cves=(),
    )
