# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 219."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.ip_security import IpsecKeyControllerFact, IpsecSaAntiReplayFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, PlatformAssessment, PlatformRelation, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=27),
    VersionRule(major=4, minor=28, patch_lte=13),
    VersionRule(major=4, minor_gte=29, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=36, patch_lte=1),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 28, 14, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.AWE_5000, PlatformFamily.AWE_7200_R, PlatformFamily.CLOUDEOS})
ADVISORY = _AdvisoryMetadata(
    sa_number="0219",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0219",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120974",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Configured IPsec anti-replay protection may be silently inactive for AutoVPN dynamic paths, permitting traffic replay.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25041-security-advisory-0219",
    description="On affected EOS platforms using IPsec AutoVPN, the configured replay window may not be applied to dynamic paths.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa219(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    controller: Fact[IpsecKeyControllerFact],
    anti_replay: Fact[IpsecSaAntiReplayFact],
) -> VulnerabilityResult:
    """Assess configured controller and anti-replay prerequisites within source scope."""
    for prerequisite in (controller, anti_replay):
        if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is FeatureState.DISABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(prerequisite,))
    release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, NotAffectedResult):
        return release
    if not isinstance(platform, UnavailableFact) and platform.value.model.strip().casefold() == "veos":
        platform_scope = PlatformAssessment(platform, PlatformRelation.AFFECTED)
    else:
        platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    problems = (
        *(release.problems if isinstance(release, ErrorResult) else ()),
        *(platform_scope.problems if isinstance(platform_scope, ErrorResult) else ()),
        *(fact for fact in (controller, anti_replay) if isinstance(fact, UnavailableFact)),
    )
    if (
        isinstance(release, ErrorResult)
        or isinstance(platform_scope, ErrorResult)
        or isinstance(controller, UnavailableFact)
        or isinstance(anti_replay, UnavailableFact)
    ):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release, platform_scope),
        conditions=(controller, anti_replay),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA219(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0219.

    Expected Results
    ----------------
    * Not Affected: EOS or platform is excluded, no local key controller is configured, or no SA policy enables anti-replay detection.
    * Affected: An affected EOS release and platform have a configured key controller and any SA policy enabling anti-replay detection.
    * Error: Required EOS, platform, controller, or SA policy evidence cannot be determined.

    Notes
    -----
    This test deliberately approximates AutoVPN exposure using a configured key controller and any SA policy with a positive replay window.
    It favors false positives: an enabled anti-replay policy can trigger an affected result even when it is unused by the controller. No profile
    binding, dynamic path group, live tunnel, generated keys, or known crypto suite is required. An empty controller JSON root means unconfigured;
    unknown controller algorithms do not establish absence. Anti-replay configuration is a prerequisite for this issue, not a verified mitigation.
    A zero replay window excludes that policy without asserting general replay safety; every policy must be disabled to establish absence.

    A narrower check would follow the key controller's configured profile to `show ip security profile`'s `securityAssociation`, then inspect that
    named SA policy's `replayWindowSize`. The controller JSON omits its selected profile, so that link would require scoped running configuration.
    The approximation intentionally avoids collecting running configuration and does not claim to prove that the enabled SA policy is selected.

    Bare `vEOS` model identity is conservatively included because CloudEOS and CVX can share that model string. Explicit `vEOS-lab` and
    `cEOS-lab` identities remain excluded. No live-session state is used to establish that a configured device is not affected.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA219:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected software, platform, and IPsec configuration facts."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        controller: Fact[IpsecKeyControllerFact] = fact_field(IpsecKeyControllerFact)
        anti_replay: Fact[IpsecSaAntiReplayFact] = fact_field(IpsecSaAntiReplayFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0219."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect configured state, assess the vulnerability, and project the result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa219(facts.version, facts.platform, facts.controller, facts.anti_replay)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
