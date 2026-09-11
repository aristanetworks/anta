# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 149."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import Dot1xDynamicAuthorizationFact, RadiusProxyDynamicAuthorizationFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily, PlatformIdentity
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_X,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7130,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.SERIES_7700_R4,
    }
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0149",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0149",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73449",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="RADIUS proxy processing may prevent dynamic authorization from reaching local 802.1X sessions.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24705-security-advisory-0149",
    description="On affected physical EOS platforms, combined 802.1X and RADIUS proxy dynamic authorization may prevent local sessions from being disconnected.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa149(
    version: Fact[EOSVersion],
    platform: Fact[PlatformIdentity],
    dot1x: Fact[FeatureValue],
    radius_proxy: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess the physical-platform, EOS, 802.1X, and RADIUS proxy conjunction."""
    for prerequisite in (dot1x, radius_proxy):
        if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is not FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(prerequisite,))
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(platform_scope, ErrorResult):
        return platform_scope
    problems = tuple(fact for fact in (dot1x, radius_proxy) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(cast("AvailableFact[FeatureValue]", dot1x), cast("AvailableFact[FeatureValue]", radius_proxy)),
        context=(eos_release, platform_scope),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA149(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0149.

    Expected Results
    ----------------
    * Success: EOS or platform is outside scope, or either required dynamic-authorization feature is absent.
    * Failure: An affected physical platform and EOS release has both required features configured.
    * Error: Required EOS, platform, 802.1X, or RADIUS proxy state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA149:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        PlatformIdentityFact,
        Dot1xDynamicAuthorizationFact,
        RadiusProxyDynamicAuthorizationFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0149."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa149(
            self.fact(EosVersionFact),
            self.fact(PlatformIdentityFact),
            self.fact(Dot1xDynamicAuthorizationFact),
            self.fact(RadiusProxyDynamicAuthorizationFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
