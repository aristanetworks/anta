# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures and constants for ANTA security advisory unit tests."""

from __future__ import annotations

from anta._advisory.models import (
    AdvisoryCVE,
    AdvisoryCVSSScore,
    AdvisoryMetadata,
    AdvisoryMitigation,
    AdvisoryResolution,
    AdvisorySeverity,
)

ADVISORY = AdvisoryMetadata(
    sa_number="0001",
    title="Test advisory",
    severity=AdvisorySeverity.HIGH,
    cves=(
        AdvisoryCVE(
            cve_id="CVE-2026-0001",
            severity=AdvisorySeverity.MEDIUM,
            cvss_scores=(
                AdvisoryCVSSScore(version="3.1", score=6.5, vector="CVSS:3.1/TEST"),
                AdvisoryCVSSScore(version="4.0", score=7.0, vector="CVSS:4.0/TEST"),
            ),
        ),
        AdvisoryCVE(
            cve_id="CVE-2026-0002",
            severity=AdvisorySeverity.HIGH,
        ),
    ),
    url="https://example.com/advisory",
    description="Test advisory description.",
    resolutions=(
        AdvisoryResolution(
            name="Upgrade",
            details="Upgrade to a fixed release.",
            url="https://example.com/resolution",
        ),
    ),
    mitigations=(
        AdvisoryMitigation(
            name="Workaround",
            details="Apply the temporary workaround.",
            url="https://example.com/mitigation",
        ),
    ),
)
