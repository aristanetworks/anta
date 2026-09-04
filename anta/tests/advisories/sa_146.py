# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 146."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar

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
    ChangeSoftwareVersion,
    FixedRelease,
    SoftwareTarget,
    remediation_plan,
    software_version_action,
)
from anta._advisory.version import SemanticVersion
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

EOS_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_lte=1),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lt=33),
)

EOS_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

TERMINATTR_FIXED_RELEASES = (
    FixedRelease(SemanticVersion(1, 46, 0, prefix="v")),
    FixedRelease(SemanticVersion(1, 45, 1, prefix="v")),
    FixedRelease(SemanticVersion(1, 43, 8, prefix="v")),
    FixedRelease(SemanticVersion(1, 40, 13, prefix="v")),
    FixedRelease(SemanticVersion(1, 37, 13, prefix="v")),
    FixedRelease(SemanticVersion(1, 34, 14, prefix="v")),
    FixedRelease(SemanticVersion(1, 31, 17, prefix="v")),
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


def _parse_terminattr_version(version_string: str) -> SemanticVersion | None:
    """Parse one normalized TerminAttr version."""
    match = TERMINATTR_VERSION_PATTERN.fullmatch(version_string.strip())
    if match is None:
        return None
    return SemanticVersion(int(match.group("major")), int(match.group("minor")), int(match.group("patch")), prefix="v")


def _is_affected_terminattr_version(version_string: str) -> bool | None:
    """Return whether a TerminAttr version is in one documented affected range."""
    version = _parse_terminattr_version(version_string)
    if version is None:
        return None

    if version.major != 1:
        return version.major < 1

    if (last_affected_patch := TERMINATTR_LAST_AFFECTED_PATCH.get(version.minor)) is not None:
        return version.patch <= last_affected_patch
    return any(first_minor <= version.minor <= last_minor for first_minor, last_minor in TERMINATTR_FULLY_AFFECTED_MINOR_RANGES)


def _eos_release_assessment(fact: Fact[EOSVersion]) -> EosReleaseAssessment | UnavailableFact[EOSVersion]:
    """Interpret the EOS version for SA146."""
    if isinstance(fact, UnavailableFact):
        return fact
    evaluation = evaluate_version(fact.value, EOS_AFFECTED_VERSION_MATRIX)
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
    software: SoftwareTarget
    fixed_releases: tuple[FixedRelease, ...]


def _software_version_action_for_path(path: _GrpcPath) -> ChangeSoftwareVersion:
    """Build a path version change from its observed affected software version."""
    if isinstance(path.version, EosReleaseAssessment):
        current_version = path.version.fact.value
    elif isinstance(path.version, ComponentVersionAssessment):
        current_version = _parse_terminattr_version(path.version.fact.value.version)
        if current_version is None:
            msg = "Cannot build a software-version change for an invalid component version"
            raise ValueError(msg)
    else:
        msg = "Cannot build a software-version change for an unavailable path version"
        raise TypeError(msg)
    return software_version_action(path.fixed_releases, current_version=current_version, software=path.software)


def _append_unique(items: list[VersionAssessment], item: VersionAssessment) -> None:
    """Append one version assessment while preserving first-seen order."""
    if item not in items:
        items.append(item)


# pylint: disable-next=too-many-branches
def _assess_sa146(paths: tuple[_GrpcPath, ...]) -> VulnerabilityResult:  # noqa: C901, PLR0912
    """Assess GHSA-hrxh-6v49-42gf from normalized path facts."""
    vulnerability_id = ADVISORY.vulnerabilities[0].id
    decisive: list[FindingEvidence] = []
    problems: list[UnavailableFact[Any]] = []
    affected_services: list[AvailableFact[FeatureValue]] = []
    affected_versions: list[VersionAssessment] = []
    unmitigated_version_changes: list[ChangeSoftwareVersion] = []
    mitigated_conditions: list[MitigatedCondition] = []
    affected_versions_for_mitigated_paths: list[VersionAssessment] = []
    mitigated_path_version_changes: list[ChangeSoftwareVersion] = []

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
        version_change = _software_version_action_for_path(path)
        if path.mitigation.value.state is MitigationState.EFFECTIVE:
            mitigated_conditions.append(MitigatedCondition(path.service, (path.mitigation,)))
            _append_unique(affected_versions_for_mitigated_paths, path.version)
            if version_change not in mitigated_path_version_changes:
                mitigated_path_version_changes.append(version_change)
            continue
        affected_services.append(path.service)
        _append_unique(affected_versions, path.version)
        if version_change not in unmitigated_version_changes:
            unmitigated_version_changes.append(version_change)

    if affected_services:
        required_version_changes = [
            *unmitigated_version_changes,
            *(version_change for version_change in mitigated_path_version_changes if version_change not in unmitigated_version_changes),
        ]
        return AffectedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(affected_versions),
            conditions=tuple(affected_services),
            remediation=remediation_plan(required_version_changes),
        )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=tuple(problems))
    if mitigated_conditions:
        return MitigatedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(affected_versions_for_mitigated_paths),
            mitigated_conditions=tuple(mitigated_conditions),
            remediation=remediation_plan(mitigated_path_version_changes),
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
                _GrpcPath(eos_release, self.fact(GnmiTransportFact), self.fact(GnmiMtlsFact), SoftwareTarget.EOS, EOS_FIXED_RELEASES),
                _GrpcPath(eos_release, self.fact(GribiTransportFact), self.fact(GribiMtlsFact), SoftwareTarget.EOS, EOS_FIXED_RELEASES),
                _GrpcPath(
                    terminattr_version,
                    self.fact(TerminAttrGrpcFact),
                    self.fact(TerminAttrMtlsFact),
                    SoftwareTarget.TERMINATTR,
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
