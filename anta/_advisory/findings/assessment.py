# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared assessment steps for structured advisory findings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.models import Fact, FactProblemKind, UnavailableFact
from anta._advisory.findings.models import EosReleaseAssessment, ErrorResult, NotAffectedResult, PlatformAssessment, PlatformRelation, VersionRelation
from anta._eos.platform import platform_matches_families

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from anta._advisory.eos_versions import VersionRule
    from anta._eos.platform import PlatformFamily, PlatformIdentity
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


def assess_platform_scope(
    vulnerability_id: str,
    platform: Fact[PlatformIdentity],
    families: Iterable[PlatformFamily],
    *,
    matched_relation: PlatformRelation = PlatformRelation.AFFECTED,
) -> PlatformAssessment | ErrorResult | NotAffectedResult:
    """Return a platform assessment or a terminal error or not-affected result.

    ``matched_relation`` supports both affected-family allowlists and unaffected-family exclusion lists. An incomplete identity cannot prove
    either relationship and is returned as an input error.
    """
    if isinstance(platform, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(platform,))

    family_match = platform_matches_families(platform.value, families)
    if family_match is None:
        problem = platform.definition.unavailable(FactProblemKind.INVALID, platform.source)
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(problem,))

    unmatched_relation = PlatformRelation.OUTSIDE_SCOPE if matched_relation is PlatformRelation.AFFECTED else PlatformRelation.AFFECTED
    assessment = PlatformAssessment(platform, matched_relation if family_match else unmatched_relation)
    if assessment.relation is PlatformRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(assessment,))
    return assessment
