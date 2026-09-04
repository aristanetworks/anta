# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 142."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, cast

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import (
    AffectedStatus,
    VersionRule,
    evaluate_version,
)
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactDefinition,
    FactProblemKind,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.redirection import (
    DirectFlowRedirectFact,
    FlowSpecRedirectFact,
    MtuDropMitigationFact,
    PbrRedirectFact,
    SegmentSecurityRedirectFact,
    TrafficPolicyRedirectFact,
)
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    FindingEvidence,
    InconclusiveResult,
    NotAffectedResult,
    PlatformAssessment,
    PlatformRelation,
    Unobservable,
    UnobservableKind,
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
    ApplyConfiguration,
    FixedRelease,
    RemediationPlan,
    Sequence,
    software_version_action,
)
from anta._eos.platform import PlatformFamily, PlatformIdentity, platform_matches_families
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta.device import DeviceVersion

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"
MTU_DROP_SHOW_COMMAND = f"show running-config | include ^{MTU_DROP_COMMAND}$"

REDIRECT_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_eq=0, hotfix_lte=1),
    VersionRule(major=4, minor=35, patch_lte=3),
    VersionRule(major=4, minor=34, patch_lte=5),
    VersionRule(major=4, minor=33, patch_lte=7),
    VersionRule(major=4, minor=32, patch_lte=10),
)
SEGMENT_SECURITY_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = REDIRECT_AFFECTED_VERSION_MATRIX[1:]
CONDITIONAL_FIXED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_gte=1),
    VersionRule(major=4, minor=35, patch_gte=4),
    VersionRule(major=4, minor=34, patch_gte=6),
    VersionRule(major=4, minor=33, patch_gte=8),
    VersionRule(major=4, minor=32, patch_gte=11),
)

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 4, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 32, 11, suffix="M")),
)


@dataclass(frozen=True)
class ExposurePath:
    """Advisory scope for one next-hop redirection feature."""

    name: str
    platform_families: tuple[PlatformFamily, ...]
    affected_versions: tuple[VersionRule, ...]


PBR_PATH = ExposurePath(
    name="Policy-Based Routing",
    platform_families=(
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_7010,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7160,
        PlatformFamily.SERIES_7050_X,
        PlatformFamily.SERIES_7050_X2,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7250_X,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    affected_versions=REDIRECT_AFFECTED_VERSION_MATRIX,
)

FLOWSPEC_PATH = ExposurePath(
    name="BGP FlowSpec",
    platform_families=(
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    affected_versions=REDIRECT_AFFECTED_VERSION_MATRIX,
)

TRAFFIC_POLICY_PATH = ExposurePath(
    name="Traffic Policy",
    platform_families=(
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_E,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ),
    affected_versions=REDIRECT_AFFECTED_VERSION_MATRIX,
)

DIRECTFLOW_PATH = ExposurePath(
    name="DirectFlow",
    platform_families=(
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7250_X,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7368_X4,
    ),
    affected_versions=REDIRECT_AFFECTED_VERSION_MATRIX,
)

SEGMENT_SECURITY_PATH = ExposurePath(
    name="Segment Security",
    platform_families=(
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
    ),
    affected_versions=SEGMENT_SECURITY_AFFECTED_VERSION_MATRIX,
)

EXPOSURE_PATHS = (
    PBR_PATH,
    FLOWSPEC_PATH,
    TRAFFIC_POLICY_PATH,
    DIRECTFLOW_PATH,
    SEGMENT_SECURITY_PATH,
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0142",
    title="Security Advisory 0142",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-12546",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description=("Next-hop redirection bypass for packets requiring exception handling."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24111-security-advisory-0142"),
    description=(
        "On affected platforms running Arista EOS (Extensible Operating System) configured "
        "with next-hop redirection features—such as Policy-Based Routing (PBR), Border Gateway "
        "Protocol (BGP) Flowspec, Traffic Policy, DirectFlow, or Segment Security—certain "
        "specific classes of IP packets requiring exception handling may bypass the configured "
        "redirection action. Instead of being redirected to the designated next hop, these "
        "packets may be handled via fallback software forwarding paths, which can result in the "
        "packets being routed according to the system's standard forwarding information."
    ),
)


def _path_applies(
    path: ExposurePath,
    device_version: DeviceVersion | None,
    platform: PlatformIdentity | None,
) -> tuple[AffectedStatus, bool, str | None]:
    """Evaluate whether a configured path requires vulnerability assessment."""
    relation = _version_relation(path, device_version)
    if relation is None:
        return AffectedStatus.UNKNOWN, False, None
    if relation is VersionRelation.OUTSIDE_SCOPE:
        return AffectedStatus.NOT_AFFECTED, False, None

    if platform is None:
        return AffectedStatus.UNKNOWN, False, None
    family_match = platform_matches_families(platform, path.platform_families)
    if family_match is True:
        return AffectedStatus.AFFECTED, False, str(platform)
    if family_match is None:
        return AffectedStatus.UNKNOWN, True, str(platform)
    return AffectedStatus.NOT_AFFECTED, False, str(platform)


def _version_relation(path: ExposurePath, device_version: DeviceVersion | None) -> VersionRelation | None:
    """Classify an EOS release using the advisory's vulnerable and conditional-fix boundaries."""
    affected = evaluate_version(device_version, path.affected_versions)
    if affected.affected_status is AffectedStatus.UNKNOWN:
        return None
    if affected.affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.AFFECTED
    conditional_fixed = evaluate_version(device_version, CONDITIONAL_FIXED_VERSION_MATRIX)
    if conditional_fixed.affected_status is AffectedStatus.AFFECTED:
        return VersionRelation.CONDITIONAL_FIXED
    return VersionRelation.OUTSIDE_SCOPE


def _full_remediation_plan(version: Fact[DeviceVersion]) -> RemediationPlan:
    """Return the required software-version change followed by the configuration."""
    current_version = cast("EOSVersion", cast("AvailableFact[DeviceVersion]", version).value)
    return RemediationPlan(
        Sequence(
            (
                software_version_action(FIXED_RELEASES, current_version=current_version),
                ApplyConfiguration((MTU_DROP_COMMAND,)),
            )
        )
    )


def _configuration_remediation_plan() -> RemediationPlan:
    """Return the remaining configuration action for a conditional-fixed release."""
    return RemediationPlan(ApplyConfiguration((MTU_DROP_COMMAND,)))


# pylint: disable-next=too-many-branches,too-many-locals,too-many-return-statements,too-many-statements
def _assess_sa142(  # noqa: C901, PLR0911, PLR0912, PLR0915
    path_facts: tuple[Fact[ConfigurationValue], ...],
    version: Fact[DeviceVersion],
    platform: Fact[PlatformIdentity],
    mitigation: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess CVE-2026-12546 from normalized redirect-path facts."""
    vulnerability_id = ADVISORY.vulnerabilities[0].id
    decisive: list[FindingEvidence] = []
    problems: list[UnavailableFact[Any]] = []
    affected: list[AvailableFact[ConfigurationValue]] = []
    conditional_fixed: list[AvailableFact[ConfigurationValue]] = []
    conservative_affected: list[FindingEvidence] = []
    conservative_conditional_fixed: list[FindingEvidence] = []
    affected_context: list[EosReleaseAssessment | PlatformAssessment] = []
    conditional_fixed_context: list[EosReleaseAssessment | PlatformAssessment] = []

    if not isinstance(version, UnavailableFact) and not isinstance(mitigation, UnavailableFact):
        conditional_fixed_evaluation = evaluate_version(version.value, CONDITIONAL_FIXED_VERSION_MATRIX)
        if conditional_fixed_evaluation.affected_status is AffectedStatus.AFFECTED and mitigation.value.state is MitigationState.EFFECTIVE:
            return NotAffectedResult(
                vulnerability_id=vulnerability_id,
                decisive=(EosReleaseAssessment(version, VersionRelation.CONDITIONAL_FIXED), mitigation),
            )

    for path, path_fact in zip(EXPOSURE_PATHS, path_facts, strict=True):
        if not isinstance(path_fact, UnavailableFact) and path_fact.value.state is ConfigurationState.NOT_CONFIGURED:
            decisive.append(path_fact)
            continue
        if isinstance(version, UnavailableFact):
            problems.append(version)
            continue
        relation = _version_relation(path, version.value)
        if relation is None:
            problems.append(EosVersionFact.unavailable(FactProblemKind.INVALID, version.source))
            continue
        release = EosReleaseAssessment(version, relation)
        if release.relation is VersionRelation.OUTSIDE_SCOPE:
            if release not in decisive:
                decisive.append(release)
            continue
        if isinstance(platform, UnavailableFact):
            problems.append(platform)
            continue
        family_match = platform_matches_families(platform.value, path.platform_families)
        if family_match is False:
            platform_outside = PlatformAssessment(platform, PlatformRelation.OUTSIDE_SCOPE)
            if platform_outside not in decisive:
                decisive.append(platform_outside)
            continue
        if isinstance(path_fact, UnavailableFact):
            problems.append(path_fact)
            continue
        if family_match is None:
            conservative = conservative_affected if relation is VersionRelation.AFFECTED else conservative_conditional_fixed
            if release not in conservative:
                conservative.append(release)
            conservative.append(path_fact)
            continue
        confirmed = affected if relation is VersionRelation.AFFECTED else conditional_fixed
        context = affected_context if relation is VersionRelation.AFFECTED else conditional_fixed_context
        confirmed.append(path_fact)
        release_context = EosReleaseAssessment(version, relation)
        platform_context = PlatformAssessment(platform, PlatformRelation.AFFECTED)
        if release_context not in context:
            context.append(release_context)
        if platform_context not in context:
            context.append(platform_context)

    if affected:
        return AffectedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(affected_context),
            conditions=tuple(affected),
            remediation=_full_remediation_plan(version),
        )
    if conditional_fixed:
        if isinstance(mitigation, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(mitigation,))
        return AffectedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(conditional_fixed_context),
            conditions=(*conditional_fixed, mitigation),
            remediation=_configuration_remediation_plan(),
        )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=tuple(dict.fromkeys(problems)))
    if conservative_affected:
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=tuple(conservative_affected),
            unresolved=(Unobservable(UnobservableKind.INCOMPLETE_PLATFORM_IDENTITY, "modular switch generation"),),
            remediation=_full_remediation_plan(version),
        )
    if conservative_conditional_fixed:
        if isinstance(mitigation, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(mitigation,))
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=(*conservative_conditional_fixed, mitigation),
            unresolved=(Unobservable(UnobservableKind.INCOMPLETE_PLATFORM_IDENTITY, "modular switch generation"),),
            remediation=_configuration_remediation_plan(),
        )
    return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=tuple(decisive))


@preview_test_class
class VerifySA142(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify that Security Advisory 142 next-hop redirects are fully remediated.

    Notes
    -----
    This test currently requires the structured EOS platform identity supplied by `AsyncEOSDevice`.
    Incomplete modular identities remain inconclusive when the installed modules cannot establish the affected family.

    Expected Results
    ----------------
    * Success: The test will pass if no affected redirect path is active or a conditional fix is complete.
    * Failure: The test will fail if a vulnerable redirect path is active or a conditional fix is incomplete.
    * Inconclusive: The test is inconclusive for a conservatively matched chassis.
    * Error: The test will error if a required redirect, platform, EOS release, or MTU control state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_142:
      - VerifySA142:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        PlatformIdentityFact,
        PbrRedirectFact,
        FlowSpecRedirectFact,
        TrafficPolicyRedirectFact,
        DirectFlowRedirectFact,
        SegmentSecurityRedirectFact,
        MtuDropMitigationFact,
    )
    description = "Verify whether the device is impacted by SA 0142."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Assess and project the advisory vulnerability."""
        finding = _assess_sa142(
            (
                self.fact(PbrRedirectFact),
                self.fact(FlowSpecRedirectFact),
                self.fact(TrafficPolicyRedirectFact),
                self.fact(DirectFlowRedirectFact),
                self.fact(SegmentSecurityRedirectFact),
            ),
            self.fact(EosVersionFact),
            self.fact(PlatformIdentityFact),
            self.fact(MtuDropMitigationFact),
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_vulnerability_result(atomic_result, finding)
