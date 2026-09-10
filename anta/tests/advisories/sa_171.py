# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 171."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactDefinition,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)
from anta._advisory.facts.routing import Ospfv2BroadcastAuthenticationFact, Ospfv2ProcessConfiguredFact, Ospfv2SegmentRoutingFact
from anta._advisory.facts.software import SA171HotfixFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    Unobservable,
    UnobservableKind,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

BROADCAST_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_eq=0),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
SEGMENT_ROUTING_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
BROADCAST_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, hotfix=1, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
SEGMENT_ROUTING_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
BROADCAST_HOTFIX_RELEASES = frozenset({"4.36.1F", "4.35.5M", "4.34.7M", "4.33.9M"})
ADVISORY = _AdvisoryMetadata(
    sa_number="0171",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0171",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73435",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Crafted authenticated OSPFv2 packets may disrupt adjacencies and cause packet loss.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73436",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Crafted OSPFv2 packets may restart the OSPF process when segment routing is enabled.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24727-security-advisory-0171",
    description="On affected EOS releases, crafted OSPFv2 packets may disrupt authenticated broadcast adjacencies or restart OSPF segment routing.",
)
BROADCAST_ID, SEGMENT_ROUTING_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _assess_ospfv2_issue(
    vulnerability_id: str,
    version: Fact[EOSVersion],
    prerequisite: Fact[FeatureValue],
    affected_versions: tuple[VersionRule, ...],
    fixed_releases: tuple[FixedRelease, ...],
    hotfix: Fact[MitigationValue] | None,
    hotfix_releases: frozenset[str],
) -> VulnerabilityResult:
    """Assess one OSPFv2 issue using its independent version and feature prerequisite."""
    # pylint: disable=duplicate-code
    if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(prerequisite,))
    eos_release = assess_eos_scope(vulnerability_id, version, affected_versions)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(prerequisite, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(prerequisite,))
    remediation = software_version_plan(fixed_releases, current_version=eos_release.fact.value)
    if hotfix is not None and str(eos_release.fact.value) in hotfix_releases:
        if isinstance(hotfix, UnavailableFact):
            return ErrorResult(vulnerability_id=vulnerability_id, problems=(hotfix,))
        if hotfix.value.state is MitigationState.EFFECTIVE:
            return MitigatedResult(
                vulnerability_id=vulnerability_id,
                mitigated_conditions=(MitigatedCondition(cast("AvailableFact[FeatureValue]", prerequisite), (hotfix,)),),
                context=(eos_release,),
                remediation=remediation,
            )
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        conditions=(cast("AvailableFact[FeatureValue]", prerequisite),),
        context=(eos_release,),
        remediation=remediation,
    )
    # pylint: enable=duplicate-code


def _assess_broadcast_issue(
    version: Fact[EOSVersion],
    prerequisite: Fact[FeatureValue],
    configuration: Fact[ConfigurationValue],
    hotfix: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess reported active broadcast authentication, falling back to configured-process state when inactive."""
    if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is FeatureState.ENABLED:
        return _assess_ospfv2_issue(
            BROADCAST_ID,
            version,
            prerequisite,
            BROADCAST_AFFECTED_VERSIONS,
            BROADCAST_FIXED_RELEASES,
            hotfix,
            BROADCAST_HOTFIX_RELEASES,
        )
    if not isinstance(configuration, UnavailableFact) and configuration.value.state is ConfigurationState.NOT_CONFIGURED:
        return NotAffectedResult(vulnerability_id=BROADCAST_ID, decisive=(configuration,))
    if isinstance(prerequisite, UnavailableFact):
        return _assess_ospfv2_issue(
            BROADCAST_ID,
            version,
            prerequisite,
            BROADCAST_AFFECTED_VERSIONS,
            BROADCAST_FIXED_RELEASES,
            hotfix,
            BROADCAST_HOTFIX_RELEASES,
        )
    return _assess_inactive_broadcast_issue(version, configuration, hotfix)


def _assess_inactive_broadcast_issue(
    version: Fact[EOSVersion],
    configuration: Fact[ConfigurationValue],
    hotfix: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess configured OSPFv2 when no qualifying broadcast interface is currently active."""
    eos_release = assess_eos_scope(BROADCAST_ID, version, BROADCAST_AFFECTED_VERSIONS)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(configuration, UnavailableFact):
        return ErrorResult(vulnerability_id=BROADCAST_ID, problems=(configuration,))
    remediation = software_version_plan(BROADCAST_FIXED_RELEASES, current_version=eos_release.fact.value)
    if str(eos_release.fact.value) in BROADCAST_HOTFIX_RELEASES:
        if isinstance(hotfix, UnavailableFact):
            return ErrorResult(vulnerability_id=BROADCAST_ID, problems=(hotfix,))
        if hotfix.value.state is MitigationState.EFFECTIVE:
            return MitigatedResult(
                vulnerability_id=BROADCAST_ID,
                mitigated_conditions=(MitigatedCondition(configuration, (hotfix,)),),
                context=(eos_release,),
                remediation=remediation,
            )
    return InconclusiveResult(
        vulnerability_id=BROADCAST_ID,
        indications=(eos_release, configuration),
        unresolved=(
            Unobservable(
                UnobservableKind.EXTERNAL_STATE,
                "whether an OSPFv2 broadcast interface using cryptographic authentication becomes active",
            ),
        ),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA171(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0171.

    Expected Results
    ----------------
    * Success: An issue's EOS version is outside scope; or, for CVE-2026-73435, no OSPFv2 process is configured; or, for
      CVE-2026-73436, OSPF segment routing is not enabled.
    * Failure: On an affected EOS release, an active OSPFv2 broadcast interface reports cryptographic authentication
      for CVE-2026-73435, or OSPF segment routing is enabled for CVE-2026-73436.
    * Mitigated: For CVE-2026-73435, the SWIX is installed and boot-persistent on an explicitly supported release. This
      is decisive even when no qualifying broadcast interface is currently active.
    * Inconclusive: For CVE-2026-73435, an affected EOS release has an OSPFv2 process configured, but no active
      broadcast interface reporting cryptographic authentication is currently observable.
    * Error: Required EOS, OSPFv2, or applicable SWIX state cannot be determined.

    The two vulnerabilities have independent version boundaries and prerequisites. In particular, 4.34.7.1M fixes
    CVE-2026-73435 but remains affected by CVE-2026-73436.

    CVE-2026-73435 follows this decision pattern:

    * An active OSPFv2 broadcast interface reporting cryptographic authentication confirms an affected condition,
      regardless of its current neighbor count.
    * No configured OSPFv2 process closes the exposure path and produces a not-affected result.
    * A configured OSPFv2 process without a currently observable qualifying active interface is inconclusive. Interface
      state can change without an OSPF configuration change, and authentication may be inherited from area, process, or
      interface configuration.
    * An applicable effective SWIX resolves that uncertainty and produces a mitigated result.

    The test deliberately does not reconstruct effective OSPF behavior from static network, passive-interface, or
    authentication configuration. Process configuration is used only to distinguish an absent exposure path from an
    unresolved inactive one.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA171:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        Ospfv2BroadcastAuthenticationFact,
        Ospfv2ProcessConfiguredFact,
        Ospfv2SegmentRoutingFact,
        SA171HotfixFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0171."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess both vulnerabilities, and project them."""
        version = self.fact(EosVersionFact)
        hotfix = self.fact(SA171HotfixFact)
        ospfv2_configuration = self.fact(Ospfv2ProcessConfiguredFact)
        findings = (
            _assess_broadcast_issue(version, self.fact(Ospfv2BroadcastAuthenticationFact), ospfv2_configuration, hotfix),
            _assess_ospfv2_issue(
                SEGMENT_ROUTING_ID,
                version,
                self.fact(Ospfv2SegmentRoutingFact),
                SEGMENT_ROUTING_AFFECTED_VERSIONS,
                SEGMENT_ROUTING_FIXED_RELEASES,
                None,
                frozenset(),
            ),
        )
        for finding in findings:
            atomic = self.result.add(f"Verify {finding.vulnerability_id}.", vulnerability_ids=(finding.vulnerability_id,))
            project_vulnerability_result(atomic, finding)
