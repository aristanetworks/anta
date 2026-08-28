# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Semantic advisory statuses and their temporary ANTA projection."""

from __future__ import annotations

from enum import Enum
from typing import TypeAlias

from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult


class AdvisoryStatus(str, Enum):
    """Security-advisory conclusions independent of ANTA's current result model."""

    NOT_AFFECTED = "not_affected"
    AFFECTED = "affected"
    MITIGATED = "mitigated"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


AdvisoryAssessment: TypeAlias = tuple[AdvisoryStatus, str, str]
"""Semantic status, final assessment message, and remediation text."""


def project_advisory_status(
    result: _AdvisoryAtomicTestResult,
    status: AdvisoryStatus,
    message: str,
    remediation: str,
) -> None:
    """Attach remediation and project a semantic advisory status onto ANTA.

    MITIGATED remains distinct throughout assessment and is projected to INCONCLUSIVE only
    because ANTA does not yet expose a native mitigated status. When it does, this function
    is the single compatibility boundary that must change.
    """
    if remediation:
        result.remediations.append(remediation)
        parent = result.parent
        if isinstance(parent, _AdvisoryTestResult) and remediation not in parent.remediations:
            parent.remediations.append(remediation)

    if status is AdvisoryStatus.NOT_AFFECTED:
        result.is_success(message)
    elif status is AdvisoryStatus.AFFECTED:
        result.is_failure(message)
    elif status in {AdvisoryStatus.MITIGATED, AdvisoryStatus.INCONCLUSIVE}:
        result.is_inconclusive(message)
    elif status is AdvisoryStatus.ERROR:
        result.is_error(message)
    else:
        msg = f"Unsupported advisory status: {status!r}"
        raise ValueError(msg)
