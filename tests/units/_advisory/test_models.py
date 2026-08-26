# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anta._advisory.models import (
    AdvisoryCVSSScore,
    AdvisoryMitigation,
    AdvisoryResolution,
    AdvisorySeverity,
)
from tests.units._advisory.conftest import ADVISORY


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
