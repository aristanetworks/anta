# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 160."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.routing import IsisConfiguredFact, IsisGracefulRestartFact, IsisNonPassiveBroadcastInterfaceFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    InconclusiveResult,
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
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
)
LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS: tuple[VersionRule, ...] = (VersionRule(major=4, minor=36, patch_lte=1),)
BROADCAST_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)
ADVISORY = _AdvisoryMetadata(
    sa_number="0160",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0160",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73446",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted IS-IS hello may tear down an adjacency on a broadcast interface.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73459",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted IS-IS LSP may purge a legitimate LSP from the link-state database.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73460",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A malformed IS-IS LSP may terminate graceful restart prematurely.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24716-security-advisory-0160",
    description="On affected EOS releases, crafted IS-IS packets may disrupt adjacencies, link-state data, or graceful restart.",
)
BROADCAST_ID, LSP_ID, GRACEFUL_RESTART_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _assess_isis_issue(
    vulnerability_id: str,
    version: Fact[EOSVersion],
    prerequisite: Fact[FeatureValue],
    affected_versions: tuple[VersionRule, ...],
    fixed_releases: tuple[FixedRelease, ...],
) -> VulnerabilityResult:
    """Assess one IS-IS issue using its independent version and feature prerequisite."""
    if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(prerequisite,))
    eos_release = assess_eos_scope(vulnerability_id, version, affected_versions)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(prerequisite, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(prerequisite,))
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        conditions=(cast("AvailableFact[FeatureValue]", prerequisite),),
        context=(eos_release,),
        remediation=software_version_plan(fixed_releases, current_version=eos_release.fact.value),
    )


def _assess_broadcast_issue(
    version: Fact[EOSVersion],
    interface: Fact[FeatureValue],
    isis: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess modeled broadcast-interface state, retaining unresolved inactive configurations."""
    if not isinstance(interface, UnavailableFact) and interface.value.state is FeatureState.ENABLED:
        return _assess_isis_issue(BROADCAST_ID, version, interface, BROADCAST_AFFECTED_VERSIONS, BROADCAST_FIXED_RELEASES)
    if not isinstance(isis, UnavailableFact) and isis.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=BROADCAST_ID, decisive=(isis,))
    if isinstance(interface, UnavailableFact):
        return _assess_isis_issue(BROADCAST_ID, version, interface, BROADCAST_AFFECTED_VERSIONS, BROADCAST_FIXED_RELEASES)
    eos_release = assess_eos_scope(BROADCAST_ID, version, BROADCAST_AFFECTED_VERSIONS)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(isis, UnavailableFact):
        return ErrorResult(vulnerability_id=BROADCAST_ID, problems=(isis,))
    return InconclusiveResult(
        vulnerability_id=BROADCAST_ID,
        indications=(eos_release, isis),
        unresolved=(
            Unobservable(
                UnobservableKind.EXTERNAL_STATE,
                "whether an IS-IS non-passive broadcast interface becomes active",
            ),
        ),
        remediation=software_version_plan(BROADCAST_FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA160(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0160.

    Expected Results
    ----------------
    * Success: An issue's EOS version is outside scope; no IS-IS instance is enabled; or the issue-specific prerequisite is absent.
    * Failure: An affected EOS release reports the issue-specific IS-IS prerequisite.
    * Inconclusive: For CVE-2026-73446, an affected EOS release has IS-IS enabled, but no qualifying active interface is currently observable.
    * Error: Required EOS or IS-IS state cannot be determined.

    Each vulnerability has an independent version matrix and prerequisite: a reported non-passive broadcast interface, any enabled IS-IS instance,
    or graceful restart.

    A reported non-passive broadcast interface confirms CVE-2026-73446 exposure regardless of its current adjacency count. When IS-IS is enabled but no
    qualifying interface is reported, the result is inconclusive because a configured interface may be temporarily down and omitted from operational
    output. The test deliberately does not reconstruct effective interface type, passive state, or shutdown behavior from static EOS configuration.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA160:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        IsisNonPassiveBroadcastInterfaceFact,
        IsisConfiguredFact,
        IsisGracefulRestartFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0160."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess all three vulnerabilities, and project them."""
        version = self.fact(EosVersionFact)
        isis_configured = self.fact(IsisConfiguredFact)
        findings = (
            _assess_broadcast_issue(version, self.fact(IsisNonPassiveBroadcastInterfaceFact), isis_configured),
            _assess_isis_issue(
                LSP_ID,
                version,
                isis_configured,
                LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
                LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
            ),
            _assess_isis_issue(
                GRACEFUL_RESTART_ID,
                version,
                self.fact(IsisGracefulRestartFact),
                LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
                LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
            ),
        )
        for finding in findings:
            atomic = self.result.add(f"Verify {finding.vulnerability_id}.", vulnerability_ids=(finding.vulnerability_id,))
            project_vulnerability_result(atomic, finding)
