# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 225."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.interfaces import InterfaceSpeedFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    Fact,
    FactProblemKind,
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
    PlatformRelation,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformComponentRole, PlatformFamily
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta._eos.platform import PlatformComponentIdentity

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_gte=2, patch_lte=6),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_eq=0),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M", hotfix=1)),
)
AFFECTED_PLATFORM_FAMILIES = frozenset({PlatformFamily.SERIES_750_X})
AFFECTED_LINECARDS = frozenset({"CCS-750XM-48TX-LC", "CCS-750XPM-48NH-LC", "CCS-750XPM-48TXH-LC"})

ADVISORY = _AdvisoryMetadata(
    sa_number="0225",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0225",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121369",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Default or unbounded automatic interface speed can expose affected 750X linecards to resource exhaustion.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25047-security-advisory-0225",
    description="On affected EOS and 750X linecards, specific link configurations can cause high CPU and memory utilization and a system reboot.",
)
VULNERABILITY_ID = "CVE-2026-121369"


def _assess_sa225(version: Fact[EosVersionFact], platform: Fact[PlatformIdentityFact], speeds: Fact[InterfaceSpeedFact]) -> VulnerabilityResult:
    """Correlate persistent configured speed with the exact affected linecards."""
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    platform_scope = assess_platform_scope(VULNERABILITY_ID, platform, AFFECTED_PLATFORM_FAMILIES)
    for scope in (eos_release, platform_scope):
        if isinstance(scope, NotAffectedResult):
            return scope
    inventory = _assess_linecards(platform) if isinstance(platform_scope, PlatformAssessment) and isinstance(platform, AvailableFact) else _LinecardScope()
    if isinstance(inventory, NotAffectedResult):
        return inventory
    speed_scope = _scope_configured_speeds(inventory.cards, speeds) if inventory.cards and isinstance(speeds, AvailableFact) else speeds
    exposed = bool(inventory.cards) and isinstance(speed_scope, ConfigurationAssessment) and speed_scope.state is ConfigurationState.CONFIGURED
    problems: list[UnavailableFact[object]] = [
        problem for scope in (eos_release, platform_scope, speed_scope) if isinstance(scope, ErrorResult) for problem in scope.problems
    ]
    if not exposed:
        problems.extend(inventory.problems)
    if isinstance(speed_scope, UnavailableFact):
        problems.append(speed_scope)
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=tuple(problems))
    scoped_speeds = cast("ConfigurationAssessment", speed_scope)
    if scoped_speeds.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(scoped_speeds,))
    release = cast("EosReleaseAssessment", eos_release)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release, cast("PlatformAssessment", platform_scope)),
        conditions=(scoped_speeds,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@dataclass(frozen=True, slots=True)
class _LinecardScope:
    """Usable affected-card identities alongside unresolved inventory evidence."""

    cards: tuple[PlatformComponentIdentity, ...] = ()
    problems: tuple[UnavailableFact[PlatformIdentityFact], ...] = ()


def _assess_linecards(platform: AvailableFact[PlatformIdentityFact]) -> _LinecardScope | NotAffectedResult:
    """Retain usable affected cards even when other module identities are incomplete."""
    modules = platform.value.modules
    matched = tuple(module for module in modules if module.role is PlatformComponentRole.LINE_CARD and module.model in AFFECTED_LINECARDS)
    cards = tuple(card for card in matched if card.slot is not None and card.slot.isdecimal())
    problems: list[UnavailableFact[PlatformIdentityFact]] = []
    if not any(module.role is PlatformComponentRole.LINE_CARD for module in modules) or any(
        module.role is PlatformComponentRole.UNKNOWN or module.model is None for module in modules
    ):
        problems.append(PlatformIdentityFact.unavailable(FactProblemKind.MISSING, platform.source))
    if len(cards) != len(matched):
        problems.append(PlatformIdentityFact.unavailable(FactProblemKind.INVALID, platform.source))
    if not cards and not problems:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(PlatformAssessment(platform, PlatformRelation.COMPONENTS_OUTSIDE_SCOPE),))
    return _LinecardScope(cards, tuple(problems))


def _scope_configured_speeds(
    cards: tuple[PlatformComponentIdentity, ...],
    speeds: AvailableFact[InterfaceSpeedFact],
) -> ConfigurationAssessment | ErrorResult:
    """Prefer a validated unbounded witness; otherwise require complete slot evidence."""
    slots = {card.slot for card in cards}
    relevant = tuple(item for item in speeds.value.interfaces if item.slot in slots)
    scoped_speeds = ConfigurationAssessment(
        fact=InterfaceSpeedFact.from_interfaces(relevant).available(speeds.source),
        feature=SubFeature(FeatureName.INTERFACE, "default or unbounded automatic speed"),
        state=ConfigurationState.CONFIGURED if any(item.configuration in {"no speed", "speed auto"} for item in relevant) else ConfigurationState.NOT_CONFIGURED,
    )
    if scoped_speeds.state is ConfigurationState.CONFIGURED:
        return scoped_speeds
    problems = tuple(problem.fact for problem in speeds.value.problems if problem.slot in slots)
    observed_slots = {item.slot for item in relevant} | {problem.slot for problem in speeds.value.problems}
    if not slots.issubset(observed_slots):
        problems += (InterfaceSpeedFact.unavailable(FactProblemKind.MISSING, speeds.source),)
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return scoped_speeds


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA225(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0225.

    Expected Results
    ----------------
    * Not Affected: EOS or platform is excluded, no affected linecard is installed,
      or all affected-card interfaces have explicit speed constraints.
    * Affected: Affected EOS and an affected linecard have at least one interface
      configured with ``no speed`` or unbounded ``speed auto``.
    * Error: Required EOS, linecard identity, slot correlation, or speed configuration
      cannot be determined reliably.

    Notes
    -----
    The affected 750X linecards are CCS-750XM-48TX-LC, CCS-750XPM-48NH-LC,
    and CCS-750XPM-48TXH-LC. Assessment uses persistent speed configuration,
    including defaults. Powered-off cards and down interfaces remain in scope;
    operational bandwidth and link state do not establish safety.

    Explicit speed constraints, such as ``speed auto 1g``, remove the exposure
    prerequisite and produce Not Affected. One validated exposed interface is
    sufficient despite unrelated incomplete observations; otherwise, relevant
    inventory and speed evidence must be complete to establish safety.

    Remediation recommends a fixed software release rather than assuming the
    illustrative 1g workaround is suitable for every port. The test assesses
    exposure, not exploitation or resource-utilization indicators.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA225:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected persistent exposure facts."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        platform: Fact[PlatformIdentityFact] = fact_field(PlatformIdentityFact)
        speeds: Fact[InterfaceSpeedFact] = fact_field(InterfaceSpeedFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0225."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project one atomic result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa225(facts.version, facts.platform, facts.speeds)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
