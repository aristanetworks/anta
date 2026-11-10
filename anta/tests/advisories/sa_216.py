# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 216."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.dot1x import Dot1xControlledAuthenticatorInterfacesFact, Dot1xSupplicantInterfacesFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.macsec import MacsecProfilesFact
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
    VersionRule(major=4, minor_gte=22, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lt=10),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=36, patch_lt=3),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
AFFECTED_PLATFORM_FAMILIES = frozenset(
    {
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7289_R3A,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R4,
    }
)
VULNERABILITY_ID = "CVE-2026-120976"
ADVISORY = _AdvisoryMetadata(
    sa_number="0216",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0216",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id=VULNERABILITY_ID,
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="802.1X-derived MACsec authentication information can enter diagnostic data during a Smart Switch Upgrade.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25038-security-advisory-0216",
    description="On affected EOS and hardware, configured 802.1X-derived MACsec keys can expose sensitive authentication information in SSU diagnostic data.",
)
_AUTHENTICATOR = SubFeature(FeatureName.DOT1X, "controlled authenticator interface")
_SUPPLICANT = SubFeature(FeatureName.DOT1X, "supplicant interface")
_KEYED_MACSEC = SubFeature(FeatureName.DOT1X, "MACsec profile attachment using dot1x keys")
_CORRELATED = SubFeature(FeatureName.DOT1X, "interface with an attached dot1x-keyed MACsec profile")


@dataclass(frozen=True, slots=True)
class _ScopedProblem:
    """Unavailable evidence whose potentially relevant interface scope is retained."""

    interfaces: frozenset[str] | None
    fact: UnavailableFact[object]


@dataclass(frozen=True, slots=True)
class _InterfaceScope:
    """Established interfaces alongside incomplete, potentially relevant scopes."""

    interfaces: frozenset[str]
    problems: tuple[_ScopedProblem, ...]


def _dot1x_scope(dot1x: Fact[Dot1xControlledAuthenticatorInterfacesFact] | Fact[Dot1xSupplicantInterfacesFact]) -> _InterfaceScope:
    """Select identities from one configured role without an operational gate."""
    if isinstance(dot1x, UnavailableFact):
        return _InterfaceScope(frozenset(), (_ScopedProblem(None, dot1x),))
    return _InterfaceScope(
        frozenset(interface.name for interface in dot1x.value.interfaces),
        tuple(_ScopedProblem(frozenset({problem.interface}) if problem.interface is not None else None, problem.fact) for problem in dot1x.value.problems),
    )


def _macsec_scope(macsec: Fact[MacsecProfilesFact]) -> _InterfaceScope:
    """Select reported interface attachments with a configured dot1x key source."""
    if isinstance(macsec, UnavailableFact):
        return _InterfaceScope(frozenset(), (_ScopedProblem(None, macsec),))
    interfaces: set[str] = set()
    # Even hypothetical duplicate profile bindings must not veto a dot1x match;
    # EOS replaces the interface's previous profile assignment.
    for profile in macsec.value.profiles:
        if profile.key_source == "dot1x":
            interfaces.update(profile.interfaces)
    problems = [
        _ScopedProblem(frozenset(problem.interfaces) if problem.interfaces is not None else None, problem.fact)
        for problem in macsec.value.problems
        if (not problem.key_source_known or problem.key_source == "dot1x") and problem.interfaces != ()
    ]
    return _InterfaceScope(frozenset(interfaces), tuple(problems))


def _overlaps(left: frozenset[str] | None, right: frozenset[str] | None) -> bool:
    """Treat unknown scope as potentially intersecting any nonempty scope."""
    if left == frozenset() or right == frozenset():
        return False
    return left is None or right is None or bool(left & right)


def _assess_configuration(
    dot1x: Fact[Dot1xControlledAuthenticatorInterfacesFact], macsec: Fact[MacsecProfilesFact], supplicant: Fact[Dot1xSupplicantInterfacesFact]
) -> tuple[ConfigurationAssessment, ConfigurationAssessment] | NotAffectedResult | ErrorResult:
    """Correlate complete witnesses and retain only potentially relevant problems."""
    roles = ((dot1x, _dot1x_scope(dot1x), _AUTHENTICATOR), (supplicant, _dot1x_scope(supplicant), _SUPPLICANT))
    keys = _macsec_scope(macsec)
    for role_fact, role, feature in roles:
        complete = role.interfaces & keys.interfaces
        for problem in (*role.problems, *keys.problems):
            # Unknown sibling scope is uncertainty, not an observed contradiction.
            if problem.interfaces is not None:
                complete -= problem.interfaces
        if complete and isinstance(role_fact, AvailableFact) and isinstance(macsec, AvailableFact):
            scoped_dot1x = replace(
                role_fact.value,
                interfaces=tuple(item for item in role_fact.value.interfaces if item.name in complete),
            ).available(role_fact.source)
            scoped_macsec = MacsecProfilesFact(
                tuple(
                    replace(item, interfaces=tuple(name for name in item.interfaces if name in complete))
                    for item in macsec.value.profiles
                    if item.key_source == "dot1x" and complete.intersection(item.interfaces)
                )
            ).available(macsec.source)
            return (
                ConfigurationAssessment(scoped_dot1x, feature, ConfigurationState.CONFIGURED),
                ConfigurationAssessment(scoped_macsec, _CORRELATED, ConfigurationState.CONFIGURED),
            )
    auth = _InterfaceScope(frozenset().union(*(role.interfaces for _, role, _ in roles)), tuple(problem for _, role, _ in roles for problem in role.problems))
    problems = tuple(
        problem.fact
        for scope, other in ((auth, keys), (keys, auth))
        for problem in scope.problems
        if _overlaps(problem.interfaces, other.interfaces) or any(_overlaps(problem.interfaces, unknown.interfaces) for unknown in other.problems)
    )
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=tuple(dict.fromkeys(problems)))
    if not auth.interfaces and not auth.problems and isinstance(dot1x, AvailableFact) and isinstance(supplicant, AvailableFact):
        return NotAffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            decisive=(
                ConfigurationAssessment(dot1x, _AUTHENTICATOR, ConfigurationState.NOT_CONFIGURED),
                ConfigurationAssessment(supplicant, _SUPPLICANT, ConfigurationState.NOT_CONFIGURED),
            ),
        )
    if isinstance(macsec, AvailableFact):
        absence = ConfigurationAssessment(macsec, _KEYED_MACSEC if not keys.interfaces and not keys.problems else _CORRELATED, ConfigurationState.NOT_CONFIGURED)
    else:
        msg = "Configuration uncertainty must retain a required problem"
        raise AssertionError(msg)  # noqa: TRY004 - This is an unreachable assessment invariant, not a bad input type.
    return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(absence,))


def _assess_sa216(
    version: Fact[EosVersionFact],
    platform: Fact[PlatformIdentityFact],
    dot1x: Fact[Dot1xControlledAuthenticatorInterfacesFact],
    macsec: Fact[MacsecProfilesFact],
    supplicant: Fact[Dot1xSupplicantInterfacesFact],
) -> VulnerabilityResult:
    """Assess software, hardware, and same-interface persistent configuration."""
    configuration = _assess_configuration(dot1x, macsec, supplicant)
    if isinstance(configuration, NotAffectedResult):
        return configuration
    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    for scope in (eos_scope, platform_scope):
        if isinstance(scope, NotAffectedResult):
            return scope
    problems = tuple(problem for scope in (eos_scope, platform_scope, configuration) if isinstance(scope, ErrorResult) for problem in scope.problems)
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    eos_scope = cast("EosReleaseAssessment", eos_scope)
    platform_scope = cast("PlatformAssessment", platform_scope)
    configuration = cast("tuple[ConfigurationAssessment, ConfigurationAssessment]", configuration)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope, platform_scope),
        conditions=configuration,
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA216(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0216.

    Expected Results
    ----------------
    * Not Affected: EOS or hardware is excluded, or no interface has both
      configured 802.1X (authenticator or supplicant) and an attached MACsec profile
      using dot1x keys.
    * Affected: Affected EOS and hardware have both configurations on at least
      one same interface.
    * Error: Required software, hardware, or relevant configuration evidence is
      unavailable, malformed, or contradictory.

    Notes
    -----
    Assessment uses persistent configuration rather than a currently authenticated
    session, link state, SSU history, or proof of leaked diagnostic data. Configured
    authenticators and supplicants are both included. Authenticators require global
    system authentication control and port-control auto. Supplicants are assessed
    independently of those authenticator controls and do not require an active
    session or SSL profile. The test assesses configured exposure rather than
    exploitation or whether an SSU has occurred.

    Profile key sources and interface attachments come from ``show mac security
    profile`` revision 1; authenticators come from ``show dot1x all`` revision 1
    and supplicants from ``show dot1x supplicant`` revision 1. Both role inventories
    must establish absence before the test concludes that no 802.1X role is configured.
    An omitted key-source field is the observed unconfigured default, whereas an
    explicit null or malformed value is an error when relevant. Profiles without
    interface attachments and configurations on different interfaces do not combine
    to establish exposure. Cryptographic keys and hashes are not retained as facts.

    A complete same-interface match survives unrelated parsing errors; without
    a match, incomplete relevant evidence prevents a safe result.

    The 7388 entry is assessed through the 7388X5 family, and the 7289R3 entry through
    the 7289R3A family. Existing platform identity groups 720XPM/722XPM separately
    from excluded 720XP and includes R3A linecards in the 7800R3 family. Virtual EOS
    platforms remain excluded. Unfixed 4.22 through 4.32 trains are kept open-ended;
    the named fixed release bounds each later affected train. There is no verified
    mitigation branch; remediation recommends a fixed software release.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA216:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Required software, platform, and scoped configured-state observations."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        dot1x: Fact[Dot1xControlledAuthenticatorInterfacesFact] = fact_field(Dot1xControlledAuthenticatorInterfacesFact)
        macsec: Fact[MacsecProfilesFact] = fact_field(MacsecProfilesFact)
        supplicant: Fact[Dot1xSupplicantInterfacesFact] = fact_field(Dot1xSupplicantInterfacesFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0216."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect observations, correlate the configuration, and project one result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa216(facts.version, facts.platform, facts.dot1x, facts.macsec, facts.supplicant)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
