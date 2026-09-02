# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 146."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiMtlsFact, GnmiTransportFact, GribiMtlsFact, GribiTransportFact
from anta._advisory.facts.models import (
    AvailableFact,
    ComponentSoftwareVersion,
    Fact,
    FactDefinition,
    FactProblemKind,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.facts.terminattr import TerminAttrGrpcFact, TerminAttrMtlsFact
from anta._advisory.findings.models import (
    AffectedResult,
    ComponentVersionAssessment,
    EosReleaseAssessment,
    ErrorResult,
    FindingEvidence,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VersionAssessment,
    VersionRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import (
    FixedRelease,
    upgrade_remediation,
)
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta.device import DeviceVersion

EOS_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_lte=1),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lt=33),
)

EOS_FIXED_RELEASES = (
    FixedRelease("4.36.2F", "4.36"),
    FixedRelease("4.35.6M", "4.35"),
    FixedRelease("4.34.8M", "4.34"),
    FixedRelease("4.33.9M", "4.33"),
)

TERMINATTR_FIXED_RELEASES = (
    FixedRelease("v1.46.0", "v1.46", "TerminAttr"),
    FixedRelease("v1.45.1", "v1.45", "TerminAttr"),
    FixedRelease("v1.43.8", "v1.43", "TerminAttr"),
    FixedRelease("v1.40.13", "v1.40", "TerminAttr"),
    FixedRelease("v1.37.13", "v1.37", "TerminAttr"),
    FixedRelease("v1.34.14", "v1.34", "TerminAttr"),
    FixedRelease("v1.31.17", "v1.31", "TerminAttr"),
)

TERMINATTR_VERSION_PATTERN = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
TERMINATTR_LAST_AFFECTED_PATCH = {31: 16, 34: 13, 37: 12, 40: 12, 43: 7, 45: 0}
TERMINATTR_FULLY_AFFECTED_MINOR_RANGES = ((0, 30), (32, 33), (35, 36), (38, 39), (41, 42))
TERMINATTR_EXEC_PREFIX = ("exec", "/usr/bin/TerminAttr")

ADVISORY = _AdvisoryMetadata(
    sa_number="0146",
    title="Security Advisory 0146",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="GHSA-hrxh-6v49-42gf",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=("HTTP/2 Rapid Reset denial-of-service rate-limit bypass in affected gRPC servers."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24500-security-advisory-0146"),
    description=(
        "Arista Networks is providing this security update in response to the gRPC-Go security "
        "vulnerabilities published as GHSA-hrxh-6v49-42gf. Arista products are affected solely "
        "by the HTTP/2 Rapid Reset denial-of-service bypass, in which an unauthenticated remote "
        "attacker can exploit unthrottled HTTP/2 stream resets to bypass rate-limiting controls, "
        "consume excessive CPU resources, and cause a denial of service."
    ),
)


def _is_affected_terminattr_version(version_string: str) -> bool | None:
    """Return whether a TerminAttr version is in one documented affected range."""
    match = TERMINATTR_VERSION_PATTERN.fullmatch(version_string.strip())
    if match is None:
        return None

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    if major != 1:
        return major < 1

    if (last_affected_patch := TERMINATTR_LAST_AFFECTED_PATCH.get(minor)) is not None:
        return patch <= last_affected_patch
    return any(first_minor <= minor <= last_minor for first_minor, last_minor in TERMINATTR_FULLY_AFFECTED_MINOR_RANGES)


def _eos_release_assessment(fact: Fact[DeviceVersion]) -> EosReleaseAssessment | UnavailableFact[DeviceVersion]:
    """Interpret the EOS version for SA146."""
    if isinstance(fact, UnavailableFact):
        return fact
    evaluation = evaluate_version(fact.value, EOS_AFFECTED_VERSION_MATRIX)
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        return EosVersionFact.unavailable(FactProblemKind.INVALID, fact.source)
    relation = VersionRelation.AFFECTED if evaluation.affected_status is AffectedStatus.AFFECTED else VersionRelation.OUTSIDE_SCOPE
    return EosReleaseAssessment(fact, relation)


def _terminattr_version_assessment(fact: Fact[ComponentSoftwareVersion]) -> ComponentVersionAssessment | UnavailableFact[ComponentSoftwareVersion]:
    """Interpret the TerminAttr package version for SA146."""
    if isinstance(fact, UnavailableFact):
        return fact
    affected = _is_affected_terminattr_version(fact.value.version)
    if affected is None:
        return TerminAttrVersionFact.unavailable(FactProblemKind.INVALID, fact.source)
    return ComponentVersionAssessment(fact, VersionRelation.AFFECTED if affected else VersionRelation.FIXED)


@dataclass(frozen=True, slots=True)
class _GrpcPath:
    """Facts and remediation scope for one independent gRPC server path."""

    version: VersionAssessment | UnavailableFact[Any]
    service: Fact[FeatureValue]
    mitigation: Fact[MitigationValue]
    fixed_releases: tuple[FixedRelease, ...]


def _append_unique(items: list[VersionAssessment], item: VersionAssessment) -> None:
    """Append one version assessment while preserving first-seen order."""
    if item not in items:
        items.append(item)


def _assess_sa146(paths: tuple[_GrpcPath, ...]) -> VulnerabilityResult:  # noqa: C901
    """Assess GHSA-hrxh-6v49-42gf from normalized path facts."""
    vulnerability_id = ADVISORY.vulnerabilities[0].id
    decisive: list[FindingEvidence] = []
    problems: list[UnavailableFact[Any]] = []
    affected_services: list[AvailableFact[FeatureValue]] = []
    affected_versions: list[VersionAssessment] = []
    affected_releases: list[FixedRelease] = []
    mitigated_conditions: list[MitigatedCondition] = []
    mitigated_versions: list[VersionAssessment] = []
    mitigated_releases: list[FixedRelease] = []

    for path in paths:
        if not isinstance(path.service, UnavailableFact) and path.service.value.state is not FeatureState.ENABLED:
            if path.service not in decisive:
                decisive.append(path.service)
            continue
        if not isinstance(path.version, UnavailableFact) and path.version.relation is not VersionRelation.AFFECTED:
            if path.version not in decisive:
                decisive.append(path.version)
            continue
        if isinstance(path.service, UnavailableFact):
            problems.append(path.service)
            continue
        if isinstance(path.version, UnavailableFact):
            problems.append(path.version)
            continue
        if isinstance(path.mitigation, UnavailableFact):
            problems.append(path.mitigation)
            continue
        if path.mitigation.value.state is MitigationState.EFFECTIVE:
            mitigated_conditions.append(MitigatedCondition(path.service, (path.mitigation,)))
            _append_unique(mitigated_versions, path.version)
            mitigated_releases.extend(release for release in path.fixed_releases if release not in mitigated_releases)
            continue
        affected_services.append(path.service)
        _append_unique(affected_versions, path.version)
        affected_releases.extend(release for release in path.fixed_releases if release not in affected_releases)

    if affected_services:
        return AffectedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(affected_versions),
            conditions=tuple(affected_services),
            remediation=upgrade_remediation(tuple(affected_releases)),
        )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=tuple(problems))
    if mitigated_conditions:
        return MitigatedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(mitigated_versions),
            mitigated_conditions=tuple(mitigated_conditions),
            remediation=upgrade_remediation(tuple(mitigated_releases)),
        )
    return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=tuple(decisive))


@preview_test_class
class VerifySA146(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess the SA146 HTTP/2 Rapid Reset exposure and documented mTLS control.

    Expected Results
    ----------------
    * Success: The test will pass if no affected gRPC service is enabled.
    * Failure: The test will fail if an affected gRPC service is enabled without mTLS.
    * Inconclusive: The test is inconclusive if all affected services are mitigated with mTLS.
    * Error: The test will error if a required service, EOS release, component version, or mTLS state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_146:
      - VerifySA146:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        TerminAttrVersionFact,
        GnmiTransportFact,
        GribiTransportFact,
        TerminAttrGrpcFact,
        GnmiMtlsFact,
        GribiMtlsFact,
        TerminAttrMtlsFact,
    )
    description = "Verify whether the device is impacted by SA 0146."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project GHSA-hrxh-6v49-42gf."""
        eos_release = _eos_release_assessment(self.fact(EosVersionFact))
        terminattr_version = _terminattr_version_assessment(self.fact(TerminAttrVersionFact))
        finding = _assess_sa146(
            (
                _GrpcPath(eos_release, self.fact(GnmiTransportFact), self.fact(GnmiMtlsFact), EOS_FIXED_RELEASES),
                _GrpcPath(eos_release, self.fact(GribiTransportFact), self.fact(GribiMtlsFact), EOS_FIXED_RELEASES),
                _GrpcPath(
                    terminattr_version,
                    self.fact(TerminAttrGrpcFact),
                    self.fact(TerminAttrMtlsFact),
                    TERMINATTR_FIXED_RELEASES,
                ),
            )
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_vulnerability_result(atomic_result, finding)
