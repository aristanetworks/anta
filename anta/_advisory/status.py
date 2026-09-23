# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Semantic advisory statuses and their ANTA projection."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, TypeAlias

from anta._advisory.remediation import RemediationGuidance, RemediationPlan

if TYPE_CHECKING:
    from anta._advisory.results import _AdvisoryAtomicTestResult


class AdvisoryStatus(str, Enum):
    """Security-advisory conclusions independent of ANTA's current result model."""

    NOT_AFFECTED = "not_affected"
    AFFECTED = "affected"
    MITIGATED = "mitigated"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


AdvisoryAssessment: TypeAlias = tuple[AdvisoryStatus, str, RemediationPlan | None]
"""Semantic status, final assessment message, and optional remediation plan."""


def project_advisory_status(
    result: _AdvisoryAtomicTestResult,
    status: AdvisoryStatus,
    message: str,
    remediation: RemediationPlan | None,
) -> None:
    """Retain an advisory status, attach remediation, and project it onto ANTA."""
    requires_remediation = status in {AdvisoryStatus.AFFECTED, AdvisoryStatus.MITIGATED, AdvisoryStatus.INCONCLUSIVE}
    if requires_remediation != (remediation is not None):
        requirement = "requires" if requires_remediation else "must not include"
        msg = f"{status.value} advisory status {requirement} a remediation plan"
        raise ValueError(msg)

    if remediation is not None:
        result.remediation = remediation
        guidance = {RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS}
        if status is AdvisoryStatus.INCONCLUSIVE:
            guidance.add(RemediationGuidance.UNRESOLVED_CONDITIONS)
        result.remediation_guidance = frozenset(guidance)

    result.advisory_status = status

    if status in {AdvisoryStatus.NOT_AFFECTED, AdvisoryStatus.MITIGATED}:
        result.is_success(message)
    elif status in {AdvisoryStatus.AFFECTED, AdvisoryStatus.INCONCLUSIVE}:
        result.is_failure(message)
    elif status is AdvisoryStatus.ERROR:
        result.is_error(message)
    else:
        msg = f"Unsupported advisory status: {status!r}"
        raise ValueError(msg)
