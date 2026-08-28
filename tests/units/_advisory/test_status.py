# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for semantic advisory-status projection."""

from __future__ import annotations

import pytest

from anta._advisory.models import _AdvisoryMetadata
from anta._advisory.results import _AdvisoryTestResult
from anta._advisory.status import AdvisoryStatus, project_advisory_status
from anta.result_manager.models import AntaTestStatus

ADVISORY = _AdvisoryMetadata(sa_number="TBD", title="Projection test", vulnerabilities=(), url="TBD", description="Projection test advisory.")


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

    project_advisory_status(atomic_result, status, "Assessment message.", "Remediate it.")

    assert atomic_result.result is expected
    assert parent.result is expected
    assert atomic_result.messages == ["Assessment message."]
    assert atomic_result.remediations == ["Remediate it."]
    assert parent.remediations == ["Remediate it."]


def test_project_advisory_status_deduplicates_parent_remediations() -> None:
    """Verify repeated atomic guidance appears once on the parent result."""
    parent = _AdvisoryTestResult(name="unit-test", test="VerifyAdvisory", categories=[], description="", advisory=ADVISORY)
    for issue in ("issue one", "issue two"):
        project_advisory_status(parent.add(issue), AdvisoryStatus.AFFECTED, f"{issue} is affected.", "Apply the shared remediation.")

    assert parent.remediations == ["Apply the shared remediation."]
