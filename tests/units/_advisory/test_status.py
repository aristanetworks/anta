# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for semantic advisory-status projection."""

from __future__ import annotations

from datetime import date

import pytest

from anta._advisory.models import _AdvisoryMetadata
from anta._advisory.remediation import FixedRelease, RemediationGuidance, RemediationPlan, consolidate_remediations, software_version_plan
from anta._advisory.results import _AdvisoryTestResult
from anta._advisory.status import AdvisoryStatus, project_advisory_status
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus

ADVISORY = _AdvisoryMetadata(
    sa_number="TBD",
    title="Projection test",
    last_updated=date(2026, 1, 1),
    vulnerabilities=(),
    url="TBD",
    description="Projection test advisory.",
)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        pytest.param(AdvisoryStatus.NOT_AFFECTED, AntaTestStatus.SUCCESS, id="not-affected"),
        pytest.param(AdvisoryStatus.AFFECTED, AntaTestStatus.FAILURE, id="affected"),
        pytest.param(AdvisoryStatus.MITIGATED, AntaTestStatus.INCONCLUSIVE, id="mitigated"),
        pytest.param(AdvisoryStatus.INCONCLUSIVE, AntaTestStatus.INCONCLUSIVE, id="inconclusive"),
        pytest.param(AdvisoryStatus.ERROR, AntaTestStatus.ERROR, id="error"),
    ],
)
def test_project_advisory_status(status: AdvisoryStatus, expected: AntaTestStatus) -> None:
    """Verify every semantic status projects to its current ANTA status."""
    parent = _AdvisoryTestResult(name="unit-test", test="VerifyAdvisory", categories=[], description="", advisory=ADVISORY)
    atomic_result = parent.add("issue")

    remediation = (
        software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F"))
        if status not in {AdvisoryStatus.NOT_AFFECTED, AdvisoryStatus.ERROR}
        else None
    )
    project_advisory_status(atomic_result, status, "Assessment message.", remediation)

    assert atomic_result.result is expected
    assert parent.result is expected
    assert atomic_result.messages == ["Assessment message."]
    assert atomic_result.remediation == remediation
    expected_guidance = (
        frozenset({RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS, RemediationGuidance.UNRESOLVED_CONDITIONS})
        if status is AdvisoryStatus.INCONCLUSIVE
        else frozenset({RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS})
        if remediation is not None
        else frozenset()
    )
    assert atomic_result.remediation_guidance == expected_guidance


def test_project_advisory_status_consolidates_parent_remediations() -> None:
    """Verify repeated atomic plans are derived once from the parent result."""
    parent = _AdvisoryTestResult(name="unit-test", test="VerifyAdvisory", categories=[], description="", advisory=ADVISORY)
    remediation = software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F"))
    for issue in ("issue one", "issue two"):
        project_advisory_status(parent.add(issue), AdvisoryStatus.AFFECTED, f"{issue} is affected.", remediation)

    consolidated = consolidate_remediations(parent)
    assert len(consolidated) == 1
    assert consolidated[0].plan == remediation


@pytest.mark.parametrize(
    ("status", "remediation", "message"),
    [
        pytest.param(AdvisoryStatus.AFFECTED, None, "requires a remediation plan", id="affected-without-remediation"),
        pytest.param(
            AdvisoryStatus.NOT_AFFECTED,
            software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F")),
            "must not include a remediation plan",
            id="not-affected-with-remediation",
        ),
        pytest.param(
            AdvisoryStatus.ERROR,
            software_version_plan((FixedRelease(EOSVersion(4, 36, 3, suffix="F")),), current_version=EOSVersion(4, 35, 1, suffix="F")),
            "must not include a remediation plan",
            id="error-with-remediation",
        ),
    ],
)
def test_project_advisory_status_enforces_remediation_ownership(
    status: AdvisoryStatus,
    remediation: RemediationPlan | None,
    message: str,
) -> None:
    """Reject status and remediation combinations outside the advisory contract."""
    parent = _AdvisoryTestResult(name="unit-test", test="VerifyAdvisory", categories=[], description="", advisory=ADVISORY)

    with pytest.raises(ValueError, match=message):
        project_advisory_status(parent.add("issue"), status, "Assessment message.", remediation)
