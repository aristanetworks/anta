# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory models."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)

_BASE_ADVISORY_FIELDS = {
    "sa_number": "0001",
    "title": "Test advisory",
    "last_updated": date(2026, 1, 1),
    "url": "https://example.com/advisory",
    "description": "Test advisory description.",
}


def test_advisory_metadata_rejects_duplicate_vulnerability_ids() -> None:
    """Verify vulnerability IDs are unique within an advisory regardless of case."""
    vulnerability = _AdvisoryVulnerability(
        id="provider-2026-0001",
        severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
        description="Test vulnerability description.",
    )
    duplicate = vulnerability.model_copy(update={"id": vulnerability.id.upper()})

    with pytest.raises(ValidationError, match="Advisory vulnerability IDs must be unique"):
        _AdvisoryMetadata(**_BASE_ADVISORY_FIELDS, vulnerabilities=(vulnerability, duplicate))


def test_advisory_metadata_allows_empty_vulnerability_tuple() -> None:
    """Verify advisory metadata accepts an empty vulnerability tuple."""
    _AdvisoryMetadata(
        **_BASE_ADVISORY_FIELDS,
        vulnerabilities=(),
    )


def test_generic_vulnerability_defaults() -> None:
    """Verify provider-neutral vulnerabilities allow omitted optional metadata."""
    vulnerability = _AdvisoryVulnerability(id="PROVIDER-0001", description="Provider vulnerability.")

    assert vulnerability.severity is _AdvisoryVulnerabilitySeverity.UNKNOWN


@pytest.mark.parametrize("field", ["id", "description"])
def test_vulnerability_rejects_empty_required_text(field: str) -> None:
    """Verify vulnerability IDs and descriptions cannot be empty."""
    data = {"id": "PROVIDER-0001", "description": "Provider vulnerability.", field: " "}

    with pytest.raises(ValidationError, match="at least 1 character"):
        _AdvisoryVulnerability(**data)  # pyright: ignore[reportArgumentType]
