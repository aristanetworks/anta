# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 176."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    Fact,
    FactDefinition,
    FactProblemKind,
    FeatureState,
    FeatureValue,
    UnavailableFact,
)
from anta._advisory.facts.platform import PlatformIdentityFact, SwitchCardIdentityFact
from anta._advisory.facts.routing import LooseUrpfFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    PlatformAssessment,
    PlatformRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformComponentIdentity, PlatformFamily, PlatformIdentity, PlatformType
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (VersionRule(major=4, minor=35, patch_lte=4),)
FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 0, suffix="F")), FixedRelease(EOSVersion(4, 35, 5, suffix="M")))
AFFECTED_FIXED_FAMILIES = frozenset({PlatformFamily.SERIES_7050_X4})
AFFECTED_SWITCH_CARD_FAMILIES = frozenset({PlatformFamily.SERIES_7358_X4})

# TODO(sa176-platform): Replace the advisory-local chassis and switch-card
# combination with framework-provided resolved modular platform identity.
ADVISORY = _AdvisoryMetadata(
    sa_number="0176",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0176",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73469",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Loose uRPF may fail to drop traffic that should not pass source verification.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24732-security-advisory-0176",
    description=(
        "On affected 7050X4 and 7358X4 platforms running affected EOS releases, traffic received on an interface configured with loose "
        "Unicast Reverse Path Forwarding may bypass the intended verification drop."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


# pylint: disable-next=too-many-return-statements
def _assess_platform(  # noqa: PLR0911
    platform: Fact[PlatformIdentity],
    switch_card: Fact[PlatformComponentIdentity],
) -> tuple[VulnerabilityResult | None, PlatformAssessment | None]:
    """Return a terminal platform result or the affected platform context."""
    if not isinstance(switch_card, UnavailableFact):
        if switch_card.value.platform_families & AFFECTED_SWITCH_CARD_FAMILIES:
            return None, PlatformAssessment(switch_card, PlatformRelation.AFFECTED)
        if not switch_card.value.platform_families:
            problem = switch_card.definition.unavailable(FactProblemKind.INVALID, switch_card.source)
            return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(problem,)), None
    if isinstance(platform, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(platform,)), None

    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_FIXED_FAMILIES)
    if isinstance(platform_scope, PlatformAssessment):
        return None, platform_scope
    if platform.value.type is PlatformType.CHASSIS:
        if isinstance(switch_card, UnavailableFact):
            return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(switch_card,)), None
        outside = PlatformAssessment(switch_card, PlatformRelation.OUTSIDE_SCOPE)
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(outside,)), None
    if isinstance(platform_scope, ErrorResult):
        return platform_scope, None

    return platform_scope, None


def _assess_sa176(
    version: Fact[EOSVersion],
    platform: Fact[PlatformIdentity],
    switch_card: Fact[PlatformComponentIdentity],
    loose_urpf: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess EOS, platform, and loose-uRPF exposure."""
    if not isinstance(loose_urpf, UnavailableFact) and loose_urpf.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(loose_urpf,))

    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    platform_result, platform_context = _assess_platform(platform, switch_card)
    if platform_result is not None:
        return platform_result
    if isinstance(loose_urpf, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(loose_urpf,))

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release, cast("PlatformAssessment", platform_context)),
        conditions=(cast("AvailableFact[FeatureValue]", loose_urpf),),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA176(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0176.

    Expected Results
    ----------------
    * Success: The test passes when EOS or the platform is outside scope, or loose uRPF is not configured.
    * Failure: The test fails when an affected EOS release and platform have loose IPv4 or IPv6 uRPF configured.
    * Error: The test errors when required EOS, platform, loose-uRPF, or any needed switch-card state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA176:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        PlatformIdentityFact,
        SwitchCardIdentityFact,
        LooseUrpfFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0176."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa176(
            self.fact(EosVersionFact),
            self.fact(PlatformIdentityFact),
            self.fact(SwitchCardIdentityFact),
            self.fact(LooseUrpfFact),
        )
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
