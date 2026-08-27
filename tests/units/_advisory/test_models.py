# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anta._advisory.models import (
    AdvisoryCVE,
    AdvisoryCVSSScore,
    AdvisoryMetadata,
    AdvisoryMitigation,
    AdvisoryResolution,
    AdvisorySeverity,
)
from tests.units._advisory.conftest import ADVISORY

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


def test_advisory_metadata_is_immutable() -> None:
    """Verify advisory metadata and its nested models are immutable."""
    assert {severity.value for severity in AdvisorySeverity} == {"unknown", "low", "medium", "high", "critical"}
    assert AdvisoryResolution(name="Upgrade", details="Upgrade to a fixed release.").url is None
    assert AdvisoryMitigation(name="Configuration change", details="Apply the workaround.").url is None

    with pytest.raises(ValidationError, match="Instance is frozen"):
        ADVISORY.title = "Changed title"
    with pytest.raises(ValidationError, match="Instance is frozen"):
        ADVISORY.cves[0].severity = AdvisorySeverity.CRITICAL
    with pytest.raises(ValidationError, match="Instance is frozen"):
        ADVISORY.cves[0].cvss_scores[0].score = 10.0
    with pytest.raises(ValidationError, match="Instance is frozen"):
        ADVISORY.resolutions[0].details = "Changed details"
    with pytest.raises(ValidationError, match="Instance is frozen"):
        ADVISORY.mitigations[0].details = "Changed details"


@pytest.mark.parametrize("score", [-0.1, 10.1])
def test_advisory_cvss_score_range(score: float) -> None:
    """Verify CVSS base scores are constrained to the published range."""
    with pytest.raises(ValidationError):
        AdvisoryCVSSScore(version="3.1", score=score, vector="CVSS:3.1/TEST")


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
    with pytest.raises(ValidationError, match="cannot be below CVE 'CVE-2026-0002' severity 'high'"):
        AdvisoryMetadata(
            **_BASE_ADVISORY_FIELDS,
            severity=AdvisorySeverity.MEDIUM,
            cves=(
                AdvisoryCVE(cve_id="CVE-2026-0001", severity=AdvisorySeverity.MEDIUM),
                AdvisoryCVE(cve_id="CVE-2026-0002", severity=AdvisorySeverity.HIGH),
            ),
        )


def test_advisory_metadata_allows_empty_cve_list() -> None:
    """Verify advisory severity is not validated when no CVEs are included."""
    AdvisoryMetadata(
        **_BASE_ADVISORY_FIELDS,
        severity=AdvisorySeverity.LOW,
        cves=(),
    )
