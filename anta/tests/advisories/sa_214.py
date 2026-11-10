# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 214."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bgp import BgpInstanceFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.vpls import BgpVplsSignalingInstanceFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

# Both vulnerabilities were introduced in EOS 4.33; earlier releases are outside their scope.
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.SERIES_7280_R3, PlatformFamily.SERIES_7500_R3, PlatformFamily.SERIES_7800_R3})

ADVISORY = _AdvisoryMetadata(
    sa_number="0214",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0214",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120980",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A specially crafted BGP packet may unexpectedly restart the BGP agent when VPLS-BGP is configured.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-120981",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A malicious BGP peer may cause churn of VPLS pseudowire route advertisements.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25036-security-advisory-0214",
    description="On affected R3 platforms and EOS releases, configured BGP-signaled VPLS exposes BGP restart and pseudowire route-churn vulnerabilities.",
)


def _assess_vpls_bgp(
    vulnerability_id: str,
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    bgp: Fact[BgpInstanceFact],
    vpls: Fact[BgpVplsSignalingInstanceFact],
) -> VulnerabilityResult:
    """Assess affected software/platform, BGP enablement, and reported VPLS signaling."""
    if not isinstance(bgp, UnavailableFact) and bgp.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(bgp,))
    if not isinstance(vpls, UnavailableFact) and vpls.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(vpls,))
    eos_scope = assess_eos_scope(vulnerability_id, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    platform_scope = assess_platform_scope(vulnerability_id, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    problems = (
        *(eos_scope.problems if isinstance(eos_scope, ErrorResult) else ()),
        *(platform_scope.problems if isinstance(platform_scope, ErrorResult) else ()),
        *((bgp,) if isinstance(bgp, UnavailableFact) else ()),
        *((vpls,) if isinstance(vpls, UnavailableFact) else ()),
    )
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=problems)
    assert not isinstance(eos_scope, ErrorResult)  # noqa: S101
    assert not isinstance(platform_scope, ErrorResult)  # noqa: S101
    assert not isinstance(bgp, UnavailableFact)  # noqa: S101
    assert not isinstance(vpls, UnavailableFact)  # noqa: S101
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(eos_scope, platform_scope),
        conditions=(bgp, vpls),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


def _assess_cve_2026_120980(
    version: Fact[EosVersionFact], platform: Fact[PlatformIdentityFact], bgp: Fact[BgpInstanceFact], vpls: Fact[BgpVplsSignalingInstanceFact]
) -> VulnerabilityResult:
    """Assess BGP restart exposure without requiring a currently established peer."""
    return _assess_vpls_bgp("CVE-2026-120980", version, platform, bgp, vpls)


def _assess_cve_2026_120981(
    version: Fact[EosVersionFact], platform: Fact[PlatformIdentityFact], bgp: Fact[BgpInstanceFact], vpls: Fact[BgpVplsSignalingInstanceFact]
) -> VulnerabilityResult:
    """Assess pseudowire route churn without using current labels or signaling errors as a gate."""
    return _assess_vpls_bgp("CVE-2026-120981", version, platform, bgp, vpls)


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA214(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0214.

    Expected Results
    ----------------
    * Not Affected: BGP is disabled, no VPLS signaling instance is reported, EOS is outside scope, or the platform is outside the R3 scope.
    * Affected: An affected EOS release and R3 platform has BGP enabled and a reported VPLS signaling instance.
    * Error: Required EOS, complete platform identity, BGP state, or VPLS signaling evidence cannot be determined.

    Notes
    -----
    Each CVE is assessed independently. Local signaling instances count even when BGP peers are down or absent.
    This is a point-in-time operational assessment: successful empty signaling output establishes absence for that observation,
    including during convergence. Persistent configuration is not checked. Peer state and negotiated labels are not required.
    Releases before EOS 4.33 are outside both vulnerabilities' scope.
    Modular R3 membership is determined from discovered line cards; incomplete chassis identity cannot prove platform exclusion.
    This test assesses exposure, not exploitation.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA214:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts shared by the two independent vulnerability assessments."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        bgp: Fact[BgpInstanceFact] = fact_field(BgpInstanceFact)
        vpls: Fact[BgpVplsSignalingInstanceFact] = fact_field(BgpVplsSignalingInstanceFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0214."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect facts and project one atomic finding for each vulnerability."""
        facts = self.Facts.collect(self)
        for assess in (_assess_cve_2026_120980, _assess_cve_2026_120981):
            finding = assess(facts.version, facts.platform, facts.bgp, facts.vpls)
            atomic = self.result.add(f"Verify {finding.vulnerability_id}.", vulnerability_ids=(finding.vulnerability_id,))
            project_vulnerability_result(atomic, finding)
