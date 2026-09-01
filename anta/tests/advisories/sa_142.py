# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 142."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

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
    PlatformIdentity,
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
    ErrorResult,
    FindingEvidence,
    InconclusiveResult,
    MitigatedExposure,
    MitigatedResult,
    NotAffectedResult,
    PlatformAssessment,
    PlatformRelation,
    SoftwareAssessment,
    SoftwareRelation,
    Unobservable,
    UnobservableKind,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.platforms import PlatformFamily, patterns_for
from anta._advisory.remediation import (
    FixedRelease,
    upgrade_remediation,
)
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta.device import DeviceVersion

MTU_DROP_COMMAND = "ip software forwarding mtu exceed action drop"
MTU_DROP_SHOW_COMMAND = f"show running-config | include ^{MTU_DROP_COMMAND}$"

REDIRECT_VERSION_MATRIX: tuple[VersionRule, ...] = tuple(VersionRule(major=4, minor=minor) for minor in range(32, 37))
SEGMENT_SECURITY_VERSION_MATRIX: tuple[VersionRule, ...] = tuple(VersionRule(major=4, minor=minor) for minor in range(32, 36))

FIXED_RELEASES = (
    FixedRelease("4.36.1F", "4.36"),
    FixedRelease("4.35.4M", "4.35"),
    FixedRelease("4.34.6M", "4.34"),
    FixedRelease("4.33.8M", "4.33"),
    FixedRelease("4.32.11M", "4.32"),
)


@dataclass(frozen=True)
class ExposurePath:
    """Advisory scope for one next-hop redirection feature."""

    name: str
    patterns: tuple[re.Pattern[str], ...]
    conservative_patterns: tuple[re.Pattern[str], ...]
    versions: tuple[VersionRule, ...]


# TODO(sa142): Replace broad chassis matches with generation-aware resolution.  # NOSONAR
# The shared resolver must combine show-version chassis identity with
# structured module inventory. The advisory distinguishes modular generations that the
# chassis model alone does not identify; the accepted interim behavior is to continue as
# "may be affected" for the corresponding modular series.
MODULAR_7300_PATTERN = re.compile(r"^DCS-73(?:04|08|16)(?:-[FR])?$")
MODULAR_7358_7368_PATTERN = re.compile(r"^(?:DCS-)?(?:7358|7368)(?:-[A-Z]+)?$")
MODULAR_7388_PATTERN = re.compile(r"^(?:DCS-)?7388(?:-[A-Z]+)?$")
MODULAR_7500_PATTERN = re.compile(r"^DCS-75(?:04|08|12|16)(?:N|-CH)?(?:-[FR])?$")
MODULAR_7800_PATTERN = re.compile(r"^DCS-78(?:04|08|12|16[BL]?)-CH(?:-[FR])?$")

PBR_PATH = ExposurePath(
    name="Policy-Based Routing",
    patterns=patterns_for(
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
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7368_X4,
    ),
    conservative_patterns=(
        MODULAR_7300_PATTERN,
        MODULAR_7358_7368_PATTERN,
        MODULAR_7388_PATTERN,
        MODULAR_7500_PATTERN,
        MODULAR_7800_PATTERN,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

FLOWSPEC_PATH = ExposurePath(
    name="BGP FlowSpec",
    patterns=patterns_for(
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7280_E,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
    ),
    conservative_patterns=(MODULAR_7500_PATTERN, MODULAR_7800_PATTERN),
    versions=REDIRECT_VERSION_MATRIX,
)

TRAFFIC_POLICY_PATH = ExposurePath(
    name="Traffic Policy",
    patterns=patterns_for(
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
    ),
    conservative_patterns=(
        MODULAR_7300_PATTERN,
        MODULAR_7358_7368_PATTERN,
        MODULAR_7388_PATTERN,
        MODULAR_7500_PATTERN,
        MODULAR_7800_PATTERN,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

DIRECTFLOW_PATH = ExposurePath(
    name="DirectFlow",
    patterns=patterns_for(
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
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7368_X4,
    ),
    conservative_patterns=(
        MODULAR_7300_PATTERN,
        MODULAR_7358_7368_PATTERN,
    ),
    versions=REDIRECT_VERSION_MATRIX,
)

SEGMENT_SECURITY_PATH = ExposurePath(
    name="Segment Security",
    patterns=patterns_for(
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_755_758,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7280_R3,
    ),
    conservative_patterns=(
        MODULAR_7300_PATTERN,
        MODULAR_7500_PATTERN,
        MODULAR_7800_PATTERN,
    ),
    versions=SEGMENT_SECURITY_VERSION_MATRIX,
)

EXPOSURE_PATHS = (
    PBR_PATH,
    FLOWSPEC_PATH,
    TRAFFIC_POLICY_PATH,
    DIRECTFLOW_PATH,
    SEGMENT_SECURITY_PATH,
)
_NON_ALPHA_PATTERN = re.compile(r"[^a-z]")
_REDIRECT_TARGET_KEYS = {"nexthop", "nexthops", "resolvednexthop", "resolvednexthops", "outputnexthop"}

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
    platform: str | None,
) -> tuple[AffectedStatus, bool, str | None]:
    """Evaluate a configured path's documented EOS train and platform scope."""
    version_evaluation = evaluate_version(device_version, path.versions)
    if version_evaluation.affected_status is not AffectedStatus.AFFECTED:
        return version_evaluation.affected_status, False, None

    if platform is None:
        return AffectedStatus.UNKNOWN, False, None
    if any(pattern.fullmatch(platform) for pattern in path.patterns):
        return AffectedStatus.AFFECTED, False, platform
    if any(pattern.fullmatch(platform) for pattern in path.conservative_patterns):
        return AffectedStatus.AFFECTED, True, platform
    return AffectedStatus.NOT_AFFECTED, False, platform


def _resolution_remediation(*, inconclusive: bool = False) -> str:
    """Return the advisory's upgrade plus required post-upgrade action."""
    return upgrade_remediation(
        FIXED_RELEASES,
        inconclusive=inconclusive,
        additional_action=("Apply the required post-upgrade remediation described in the advisory."),
    )


# pylint: disable-next=too-many-branches
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
    confirmed: list[AvailableFact[ConfigurationValue]] = []
    conservative: list[AvailableFact[ConfigurationValue]] = []
    context: list[SoftwareAssessment | PlatformAssessment] = []

    for path, path_fact in zip(EXPOSURE_PATHS, path_facts, strict=True):
        if not isinstance(path_fact, UnavailableFact) and path_fact.value.state is ConfigurationState.NOT_CONFIGURED:
            decisive.append(path_fact)
            continue
        if isinstance(version, UnavailableFact):
            problems.append(version)
            continue
        version_evaluation = evaluate_version(version.value, path.versions)
        if version_evaluation.affected_status is AffectedStatus.UNKNOWN:
            problems.append(EosVersionFact.unavailable(FactProblemKind.INVALID, version.source))
            continue
        software = SoftwareAssessment(
            version,
            SoftwareRelation.AFFECTED if version_evaluation.affected_status is AffectedStatus.AFFECTED else SoftwareRelation.OUTSIDE_SCOPE,
        )
        if software.relation is SoftwareRelation.OUTSIDE_SCOPE:
            if software not in decisive:
                decisive.append(software)
            continue
        if isinstance(platform, UnavailableFact):
            problems.append(platform)
            continue
        exact_match = any(pattern.fullmatch(platform.value.model) for pattern in path.patterns)
        conservative_match = any(pattern.fullmatch(platform.value.model) for pattern in path.conservative_patterns)
        if not exact_match and not conservative_match:
            platform_outside = PlatformAssessment(platform, PlatformRelation.OUTSIDE_SCOPE)
            if platform_outside not in decisive:
                decisive.append(platform_outside)
            continue
        if isinstance(path_fact, UnavailableFact):
            problems.append(path_fact)
            continue
        if conservative_match and not exact_match:
            conservative.append(path_fact)
            continue
        confirmed.append(path_fact)
        software_context = SoftwareAssessment(version, SoftwareRelation.AFFECTED)
        platform_context = PlatformAssessment(platform, PlatformRelation.AFFECTED)
        if software_context not in context:
            context.append(software_context)
        if platform_context not in context:
            context.append(platform_context)

    if confirmed:
        if isinstance(mitigation, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(mitigation,))
        if mitigation.value.state is MitigationState.EFFECTIVE:
            return MitigatedResult(
                vulnerability_id=vulnerability_id,
                context=tuple(context),
                mitigated_exposures=tuple(MitigatedExposure(path, (mitigation,)) for path in confirmed),
                remediation=_resolution_remediation(),
            )
        return AffectedResult(
            vulnerability_id=vulnerability_id,
            context=tuple(context),
            exposure=tuple(confirmed),
            remediation=_resolution_remediation(),
        )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=tuple(dict.fromkeys(problems)))
    if conservative:
        if isinstance(mitigation, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(mitigation,))
        indications: tuple[FindingEvidence, ...] = (*conservative, mitigation)
        return InconclusiveResult(
            vulnerability_id=vulnerability_id,
            indications=indications,
            unresolved=(Unobservable(UnobservableKind.INCOMPLETE_PLATFORM_IDENTITY, "modular switch generation"),),
            remediation=_resolution_remediation(inconclusive=True),
        )
    return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=tuple(decisive))


@preview_test_class
class VerifySA142(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify that Security Advisory 142 next-hop redirects are safely mitigated.

    Notes
    -----
    Modular chassis matches are conservative until generation-aware platform resolution is available.

    Expected Results
    ----------------
    * Success: The test will pass if no affected redirect path is active.
    * Failure: The test will fail if an affected redirect path lacks the required MTU control.
    * Inconclusive: The test is inconclusive for a conservatively matched chassis or verified mitigation.
    * Error: The test will error if a required redirect, platform, software, or mitigation state cannot be determined.

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
