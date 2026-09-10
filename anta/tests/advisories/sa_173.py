# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 173."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, MitigationState, MitigationValue, UnavailableFact
from anta._advisory.facts.routing import LegacyOspfv3ConfiguredFact, Ospfv3ConfiguredFact, Ospfv3IpsecAuthenticationFact
from anta._advisory.facts.software import SA173HotfixFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=0),
    VersionRule(major=4, minor=35, patch_lte=4),
    VersionRule(major=4, minor=34, patch_lte=6),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32, patch_lte=10),
    VersionRule(major=4, minor_lt=32),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
HOTFIX_RELEASES = frozenset({"4.36.0.1F", "4.35.4M", "4.34.6M", "4.33.8M"})

ADVISORY = _AdvisoryMetadata(
    sa_number="0173",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0173",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73455",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted OSPFv3 packet may cause the OSPFv3 process to restart unexpectedly.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24729-security-advisory-0173",
    description=("On affected Arista EOS releases with OSPFv3 configured, a peer can send a crafted packet that causes the OSPFv3 process to restart unexpectedly."),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id
_EXPECTED_OBSERVATION_COUNT = 2


def _assess_sa173(
    version: Fact[EOSVersion],
    current: Fact[FeatureValue],
    legacy: Fact[FeatureValue],
    ipsec_authentication: Fact[MitigationValue],
    hotfix: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess persistent OSPFv3 configuration, complete IPsec coverage, and the persistent SWIX."""
    available = tuple(fact for fact in (current, legacy) if isinstance(fact, AvailableFact))
    if len(available) == _EXPECTED_OBSERVATION_COUNT and all(fact.value.state is not FeatureState.ENABLED for fact in available):
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=available)

    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if not any(fact.value.state is FeatureState.ENABLED for fact in available):
        problems = tuple(fact for fact in (current, legacy) if isinstance(fact, UnavailableFact))
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    software_context = eos_release
    remediation = software_version_plan(FIXED_RELEASES, current_version=software_context.fact.value)
    exposure = next(fact for fact in available if fact.value.state is FeatureState.ENABLED)
    applicable_mitigations = (ipsec_authentication, hotfix) if str(software_context.fact.value) in HOTFIX_RELEASES else (ipsec_authentication,)
    effective_mitigations = tuple(fact for fact in applicable_mitigations if isinstance(fact, AvailableFact) and fact.value.state is MitigationState.EFFECTIVE)
    if effective_mitigations:
        return MitigatedResult(
            vulnerability_id=VULNERABILITY_ID,
            context=(software_context,),
            mitigated_conditions=(MitigatedCondition(condition=exposure, mitigations=effective_mitigations),),
            remediation=remediation,
        )

    problems = tuple(fact for fact in applicable_mitigations if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(software_context,),
        conditions=(exposure,),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA173(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0173.

    Expected Results
    ----------------
    * Success: The test will pass if the EOS version is outside scope or both supported observations prove OSPFv3 is absent.
    * Failure: The test will fail if affected EOS has OSPFv3 configured without complete IPsec coverage or an applicable hotfix.
    * Mitigated: The test is mitigated when IPsec covers every configured OSPFv3 scope or an applicable persistent hotfix is installed.
    * Error: The test will error if required EOS version, OSPFv3 configuration, IPsec coverage, or applicable hotfix state cannot be determined.

    Active-neighbor absence is not accepted as a safe state because adjacency state is transient. IPsec mitigation is evaluated against persistent
    interface, VRF, area, and address-family configuration instead of the neighbors present when the test runs.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA173:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        Ospfv3ConfiguredFact,
        LegacyOspfv3ConfiguredFact,
        Ospfv3IpsecAuthenticationFact,
        SA173HotfixFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0173."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa173(
            self.fact(EosVersionFact),
            self.fact(Ospfv3ConfiguredFact),
            self.fact(LegacyOspfv3ConfiguredFact),
            self.fact(Ospfv3IpsecAuthenticationFact),
            self.fact(SA173HotfixFact),
        )
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
