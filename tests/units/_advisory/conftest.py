# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures and constants for ANTA security advisory unit tests."""

from __future__ import annotations

from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0001",
    title="Test advisory",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-0001",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="CVE-2026-0001 Test vulnerability affecting the management API.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-0002",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="CVE-2026-0002 Test vulnerability affecting access controls.",
        ),
    ),
    url="https://example.com/advisory",
    description="Test advisory description.",
)
