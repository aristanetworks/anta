# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 217."""

from __future__ import annotations

from datetime import date
from typing import ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.aaa import Dot1xRadiusAccountingFact
from anta._advisory.facts.dot1x import Dot1xAuthenticatorInterfacesFact, Dot1xDhcpProfilingFact, Dot1xSystemAuthControlFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.assessment import assess_eos_scope, assess_platform_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=31, patch_gte=2),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=33, patch_lt=10),
    VersionRule(major=4, minor=34, patch_lt=8),
    VersionRule(major=4, minor=35, patch_lt=6),
    VersionRule(major=4, minor=36, patch_lt=3),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
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
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    }
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0217",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0217",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120977",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=(
                "A crafted DHCP packet may force 802.1X DHCP device profiling to record a spoofed device profile, "
                "potentially granting an authenticated supplicant unauthorized network access."
            ),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25039-security-advisory-0217",
    description=(
        "On affected EOS platforms with 802.1X DHCP device profiling and RADIUS accounting, an adjacent attacker may "
        "spoof the profile recorded for an authenticated supplicant."
    ),
)
VULNERABILITY_ID = "CVE-2026-120977"


def _assess_sa217(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    system_auth_control: Fact[Dot1xSystemAuthControlFact],
    authenticators: Fact[Dot1xAuthenticatorInterfacesFact],
    profiling: Fact[Dot1xDhcpProfilingFact],
    accounting: Fact[Dot1xRadiusAccountingFact],
) -> VulnerabilityResult:
    """Assess affected scope and the four required 802.1X configuration conditions.

    The source requires every condition, and any configured DHCP profiling option satisfies the profiling condition.
    """
    for prerequisite in (system_auth_control, authenticators, profiling, accounting):
        if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state not in {FeatureState.ENABLED, ConfigurationState.CONFIGURED}:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(prerequisite,))

    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    if isinstance(platform_scope, NotAffectedResult):
        return platform_scope
    problems = (
        (eos_scope.problems if isinstance(eos_scope, ErrorResult) else ())
        + (platform_scope.problems if isinstance(platform_scope, ErrorResult) else ())
        + tuple(fact for fact in (system_auth_control, authenticators, profiling, accounting) if isinstance(fact, UnavailableFact))
    )
    if isinstance(eos_scope, ErrorResult) or isinstance(platform_scope, ErrorResult) or problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_scope),
        conditions=(
            cast("AvailableFact[Dot1xSystemAuthControlFact]", system_auth_control),
            cast("AvailableFact[Dot1xAuthenticatorInterfacesFact]", authenticators),
            cast("AvailableFact[Dot1xDhcpProfilingFact]", profiling),
            cast("AvailableFact[Dot1xRadiusAccountingFact]", accounting),
        ),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA217(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0217.

    Expected Results
    ----------------
    * Not Affected: EOS or platform is outside scope, 802.1X system authentication control is disabled or unsupported, no interface
      is configured as an 802.1X authenticator, no DHCP profiling option is configured, or 802.1X accounting does not use RADIUS.
    * Affected: An affected EOS release on an affected platform has 802.1X system authentication control, at least one
      authenticator interface, at least one DHCP profiling option, and 802.1X RADIUS accounting configured.
    * Error: Required EOS, platform, 802.1X, DHCP profiling, or accounting evidence is missing, invalid, unsupported, or cannot be
      collected.

    Notes
    -----
    An interface counts as an authenticator when it is configured with ``dot1x pae authenticator``, whatever its configured
    port-control mode. The advisory sample also configures ``dot1x port-control auto``, but its required conditions only require an
    authenticator interface, so a force-authorized or force-unauthorized authenticator is conservatively treated as exposed.

    Any one of the ``radius av-pair dhcp hostname``, ``parameter-request-list``, or ``vendor-class-id`` statements under ``dot1x``
    satisfies the DHCP profiling condition. The advisory does not require DHCP snooping, so explicit DHCP snooping configuration is
    not assessed and ``no ip dhcp snooping`` does not establish safety.

    The default 802.1X accounting list satisfies the RADIUS accounting condition when it contains the built-in ``radius`` group or a
    named group that the device reports as a RADIUS server group, with either a start-stop or a stop-only action. Accounting that
    only uses logging or a group that is not a configured RADIUS server group does not satisfy it.

    Exposure is assessed from persistent configuration. Configured RADIUS servers, server reachability, link state, current
    supplicants, and authenticated sessions are not required, so an idle or disconnected authenticator does not establish safety.

    One valid authenticator interface, recognized DHCP profiling option, or referenced RADIUS group is sufficient despite unrelated
    incomplete records; otherwise, incomplete evidence produces Error. A command that fails to collect only produces Error when
    its evidence is needed, so a fixed release, an excluded platform, or an absent condition still produces Not Affected.

    The advisory provides no workaround, so established exposure is Affected and remediation is a software upgrade. Platform scope is
    limited to the listed physical families; virtual EOS, CloudEOS, CloudVision eXchange, 7130, 7170, AWE, and ZTX platforms are not
    affected. Unrecognized or incomplete platform identity produces Error. The test assesses configuration exposure, not exploitation
    or the advisory's RADIUS accounting indicators of compromise.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA217:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        system_auth_control: Fact[Dot1xSystemAuthControlFact] = fact_field(Dot1xSystemAuthControlFact)
        authenticators: Fact[Dot1xAuthenticatorInterfacesFact] = fact_field(Dot1xAuthenticatorInterfacesFact)
        profiling: Fact[Dot1xDhcpProfilingFact] = fact_field(Dot1xDhcpProfilingFact)
        accounting: Fact[Dot1xRadiusAccountingFact] = fact_field(Dot1xRadiusAccountingFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0217."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect facts, assess the vulnerability, and project its atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa217(facts.version, facts.platform, facts.system_auth_control, facts.authenticators, facts.profiling, facts.accounting)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
