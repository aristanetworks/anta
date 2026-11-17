# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 215."""

from __future__ import annotations

from datetime import date
from typing import ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.dot1x import Dot1xControlledAuthenticatorInterfacesFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    Fact,
    FactsBase,
    FeatureName,
    SubFeature,
    UnavailableFact,
    fact_field,
    facts_dataclass,
)
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import (
    AffectedResult,
    ConfigurationAssessment,
    EosReleaseAssessment,
    ErrorResult,
    NotAffectedResult,
    PlatformAssessment,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7250_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
    }
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0215",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0215",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120983",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=("Traffic from unauthenticated hosts may bypass 802.1X enforcement, and their control packets may be copied to the CPU."),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25037-security-advisory-0215",
    description=(
        "On affected EOS releases and platforms, unauthenticated traffic may bypass 802.1X enforcement to be forwarded by PBR. "
        "Additionally control packets may be copied to the CPU."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


_AUTHENTICATOR = SubFeature(FeatureName.DOT1X, "controlled authenticator")


def _assess_sa215(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    authenticators: Fact[Dot1xControlledAuthenticatorInterfacesFact],
) -> VulnerabilityResult:
    """Screen globally enabled auto authenticators, preserving decisive evidence."""
    witnesses: tuple[ConfigurationAssessment, ...] = ()
    configuration_problems: tuple[UnavailableFact[object], ...] = ()
    if isinstance(authenticators, AvailableFact):
        if authenticators.value.interfaces:
            witnesses = (ConfigurationAssessment(authenticators, _AUTHENTICATOR, ConfigurationState.CONFIGURED),)
        elif authenticators.value.problems:
            configuration_problems = tuple(problem.fact for problem in authenticators.value.problems)
        else:
            return NotAffectedResult(
                vulnerability_id=VULNERABILITY_ID,
                decisive=(ConfigurationAssessment(authenticators, _AUTHENTICATOR, ConfigurationState.NOT_CONFIGURED),),
            )
    else:
        configuration_problems = (authenticators,)
    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    for scope in (eos_scope, platform_scope):
        if isinstance(scope, NotAffectedResult):
            return scope
    problems = tuple(problem for scope in (eos_scope, platform_scope) if isinstance(scope, ErrorResult) for problem in scope.problems) + configuration_problems
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=tuple(dict.fromkeys(problems)))
    # The terminal scope results and required configuration problems have been handled.
    eos_scope = cast("EosReleaseAssessment", eos_scope)
    platform_scope = cast("PlatformAssessment", platform_scope)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_scope),
        conditions=witnesses,
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA215(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0215.

    Expected Results
    ----------------
    * Not Affected: EOS or hardware is outside scope, global system authentication control is disabled, or no auto authenticator is configured.
    * Affected: Affected EOS and hardware have global system authentication control enabled and at least one authenticator in auto mode.
    * Error: Required software, hardware, or controlled-authenticator evidence cannot be determined.

    Notes
    -----
    Requires global ``system-auth-control`` and an authenticator port in ``auto`` mode. Host mode, VLAN assignment, PBR,
    and active authentication sessions are not required. Supplicant-only ports do not qualify.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA215:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Software, hardware, and the existing controlled authenticator inventory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        authenticators: Fact[Dot1xControlledAuthenticatorInterfacesFact] = fact_field(Dot1xControlledAuthenticatorInterfacesFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0215."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect the existing controlled inventory, assess exposure, and project one result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa215(facts.version, facts.platform, facts.authenticators)
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
