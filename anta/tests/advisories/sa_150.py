# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 150."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import Dot1xControlledAuthenticatorFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    NotAffectedResult,
    PlatformAssessment,
    PlatformRelation,
    Unobservable,
    UnobservableKind,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import AllOf, ConditionalAction, FixedRelease, RemediationPlan, RunCommand, software_version_action
from anta._eos.platform import PlatformFamily, PlatformIdentity
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from collections.abc import Sequence

CVE_77191_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=35, patch_eq=0),
    VersionRule(major=4, minor=34, patch_lte=5),
    VersionRule(major=4, minor=33, patch_lte=7),
    VersionRule(major=4, minor_lt=33),
)
CVE_75943_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
CVE_75944_75945_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (VersionRule(major=4, minor=36, patch_eq=1),)

UNAFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.AWE_5000,
        PlatformFamily.AWE_7200_R,
        PlatformFamily.CLOUDEOS,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CVX,
    }
)

CVE_77191_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 35, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 34, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 8, suffix="M")),
)
CVE_75943_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
CVE_75944_75945_FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)

# TODO(sa150-acl): Replace the external-state conclusion only if device
# evidence can rule out current and future ACL authorization from AAA.
ADVISORY = _AdvisoryMetadata(
    sa_number="0150",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0150",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-77191",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="An authenticated supplicant may briefly send traffic before its assigned ACL is enforced.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-75943",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="A removed or timed-out supplicant may briefly send traffic without ACL enforcement.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-75944",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A stale supplicant ACL may be applied after re-authentication and an AclAgent restart.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-75945",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="A supplicant may remain authorized after all 802.1X hosts are cleared.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24706-security-advisory-0150",
    description=(
        "On affected physical EOS platforms using 802.1X authentication with per-supplicant ACL authorization, transient or stale state may "
        "permit traffic without the intended ACL policy."
    ),
)
CVE_77191_ID, CVE_75943_ID, CVE_75944_ID, CVE_75945_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)

ACL_ASSIGNMENT = Unobservable(UnobservableKind.EXTERNAL_STATE, "whether a static or dynamic ACL is assigned to the supplicant")


def _remediation_plan(vulnerability_id: str, fixed_releases: Sequence[FixedRelease], current_version: EOSVersion) -> RemediationPlan:
    """Return permanent resolution and any source-backed conditional response."""
    version_action = software_version_action(fixed_releases, current_version=current_version)
    if vulnerability_id != CVE_75945_ID:
        return RemediationPlan(version_action)
    return RemediationPlan(
        AllOf(
            (
                version_action,
                ConditionalAction(
                    "a supplicant remains authenticated after all 802.1X hosts are cleared",
                    RunCommand(("clear dot1x host all",)),
                ),
            )
        )
    )


def _assess_sa150_issue(
    *,
    vulnerability_id: str,
    version: Fact[EOSVersion],
    platform: Fact[PlatformIdentity],
    dot1x: Fact[FeatureValue],
    affected_versions: Sequence[VersionRule],
    unresolved: tuple[Unobservable, ...],
    fixed_releases: Sequence[FixedRelease],
) -> VulnerabilityResult:
    """Assess the shared SA150 prerequisites for one vulnerability."""
    if not isinstance(dot1x, UnavailableFact) and dot1x.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(dot1x,))
    eos_release = assess_eos_scope(vulnerability_id, version, affected_versions)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    platform_scope = assess_platform_scope(
        vulnerability_id,
        platform,
        UNAFFECTED_PLATFORM_FAMILIES,
        matched_relation=PlatformRelation.OUTSIDE_SCOPE,
    )
    if not isinstance(platform_scope, PlatformAssessment):
        return platform_scope
    if isinstance(dot1x, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(dot1x,))
    return InconclusiveResult(
        vulnerability_id=vulnerability_id,
        indications=(eos_release, platform_scope, cast("AvailableFact[FeatureValue]", dot1x)),
        unresolved=unresolved,
        remediation=_remediation_plan(vulnerability_id, fixed_releases, eos_release.fact.value),
    )


def _assess_cve_77191(version: Fact[EOSVersion], platform: Fact[PlatformIdentity], dot1x: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess CVE-2026-77191."""
    return _assess_sa150_issue(
        vulnerability_id=CVE_77191_ID,
        version=version,
        platform=platform,
        dot1x=dot1x,
        affected_versions=CVE_77191_AFFECTED_VERSIONS,
        unresolved=(ACL_ASSIGNMENT,),
        fixed_releases=CVE_77191_FIXED_RELEASES,
    )


def _assess_cve_75943(version: Fact[EOSVersion], platform: Fact[PlatformIdentity], dot1x: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess CVE-2026-75943."""
    return _assess_sa150_issue(
        vulnerability_id=CVE_75943_ID,
        version=version,
        platform=platform,
        dot1x=dot1x,
        affected_versions=CVE_75943_AFFECTED_VERSIONS,
        unresolved=(ACL_ASSIGNMENT,),
        fixed_releases=CVE_75943_FIXED_RELEASES,
    )


def _assess_cve_75944(version: Fact[EOSVersion], platform: Fact[PlatformIdentity], dot1x: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess CVE-2026-75944."""
    return _assess_sa150_issue(
        vulnerability_id=CVE_75944_ID,
        version=version,
        platform=platform,
        dot1x=dot1x,
        affected_versions=CVE_75944_75945_AFFECTED_VERSIONS,
        unresolved=(
            ACL_ASSIGNMENT,
            Unobservable(UnobservableKind.DEVICE_STATE_NOT_EXPOSED, "whether a stale ACL entry remains after supplicant re-authentication"),
        ),
        fixed_releases=CVE_75944_75945_FIXED_RELEASES,
    )


def _assess_cve_75945(version: Fact[EOSVersion], platform: Fact[PlatformIdentity], dot1x: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess CVE-2026-75945."""
    return _assess_sa150_issue(
        vulnerability_id=CVE_75945_ID,
        version=version,
        platform=platform,
        dot1x=dot1x,
        affected_versions=CVE_75944_75945_AFFECTED_VERSIONS,
        unresolved=(ACL_ASSIGNMENT,),
        fixed_releases=CVE_75944_75945_FIXED_RELEASES,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA150(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0150.

    Expected Results
    ----------------
    * Success: An issue passes when EOS or platform is outside its scope, or no controlled 802.1X authenticator is active.
    * Inconclusive: An applicable issue is inconclusive because static or dynamic ACL assignment cannot be ruled out from device state.
    * Error: An issue errors when required EOS, platform, or 802.1X state cannot be determined.

    Whether an operator previously ran `clear dot1x host all` does not change exposure assessment. For CVE-2026-75945,
    rerunning that command is presented only as conditional mitigation advice when a supplicant remains authenticated.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA150:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, PlatformIdentityFact, Dot1xControlledAuthenticatorFact)
    description = "Verify whether the device is impacted by Security Advisory 0150."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive shared facts, assess each vulnerability, and project it."""
        version = self.fact(EosVersionFact)
        platform = self.fact(PlatformIdentityFact)
        dot1x = self.fact(Dot1xControlledAuthenticatorFact)
        findings = (
            _assess_cve_77191(version, platform, dot1x),
            _assess_cve_75943(version, platform, dot1x),
            _assess_cve_75944(version, platform, dot1x),
            _assess_cve_75945(version, platform, dot1x),
        )
        for vulnerability, finding in zip(ADVISORY.vulnerabilities, findings, strict=True):
            atomic = self.result.add(f"Verify {vulnerability.id}.", vulnerability_ids=(vulnerability.id,))
            project_vulnerability_result(atomic, finding)
