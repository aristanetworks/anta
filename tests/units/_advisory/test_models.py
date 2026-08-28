# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anta._advisory.models import (
    _AdvisoryCVE,
    _AdvisoryCVESeverity,
    _AdvisoryMetadata,
)

_BASE_ADVISORY_FIELDS = {
    "sa_number": "0001",
    "title": "Test advisory",
    "url": "https://example.com/advisory",
    "description": "Test advisory description.",
}


def test_advisory_metadata_rejects_duplicate_cve_ids() -> None:
    """Verify an advisory cannot declare the same CVE more than once."""
    cve = _AdvisoryCVE(
        cve_id="CVE-2026-0001",
        severity=_AdvisoryCVESeverity.MEDIUM,
        description="CVE-2026-0001 Test vulnerability description.",
    )

    with pytest.raises(ValidationError, match="Advisory CVE IDs must be unique"):
        _AdvisoryMetadata(**_BASE_ADVISORY_FIELDS, cves=(cve, cve))


def test_advisory_metadata_allows_empty_cve_tuple() -> None:
    """Verify advisory accepts empty CVE tuple."""
    _AdvisoryMetadata(
        **_BASE_ADVISORY_FIELDS,
        cves=(),
    )
