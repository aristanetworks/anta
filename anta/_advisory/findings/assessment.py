# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared assessment steps for structured advisory findings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.models import Fact, FactProblemKind, UnavailableFact
from anta._advisory.findings.models import EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation

if TYPE_CHECKING:
    from collections.abc import Sequence

    from anta._advisory.eos_versions import VersionRule
    from anta._eos.version import EOSVersion


def assess_eos_scope(
    vulnerability_id: str,
    version: Fact[EOSVersion],
    affected_versions: Sequence[VersionRule],
) -> EosReleaseAssessment | ErrorResult | NotAffectedResult:
    """Return an affected EOS assessment or a terminal error or not-affected result."""
    release = assess_eos_version(version, affected_versions)
    if isinstance(release, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(release,))
    if release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(release,))
    return release


def assess_eos_version(
    version: Fact[EOSVersion],
    affected_versions: Sequence[VersionRule],
) -> EosReleaseAssessment | UnavailableFact[EOSVersion]:
    """Interpret an EOS version fact without making a terminal vulnerability decision."""
    if isinstance(version, UnavailableFact):
        return version

    evaluation = evaluate_version(version.value, affected_versions)
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        return version.definition.unavailable(FactProblemKind.INVALID, version.source)

    relation = VersionRelation.AFFECTED if evaluation.affected_status is AffectedStatus.AFFECTED else VersionRelation.OUTSIDE_SCOPE
    return EosReleaseAssessment(version, relation)
