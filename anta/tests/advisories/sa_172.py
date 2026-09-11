# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""ANTA test for Arista Security Advisory 172."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, MitigationState, MitigationValue, UnavailableFact
from anta._advisory.facts.routing import LegacyOspfv3ConfiguredFact, Ospfv3ConfiguredFact, Ospfv3IpsecAuthenticationFact
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
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0172",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0172",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73438",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Crafted packets may restart OSPFv3 and disrupt routing adjacencies.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24728-security-advisory-0172",
    description="On affected EOS releases with OSPFv3 configured, crafted packets may restart the OSPFv3 agent and disrupt routing.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id
_EXPECTED_OBSERVATION_COUNT = 2


def _assess_sa172(
    version: Fact[EOSVersion],
    current: Fact[FeatureValue],
    legacy: Fact[FeatureValue],
    ipsec_authentication: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess EOS scope, persistent OSPFv3 configuration, and complete IPsec coverage."""
    available = tuple(fact for fact in (current, legacy) if isinstance(fact, AvailableFact))
    if len(available) == _EXPECTED_OBSERVATION_COUNT and all(fact.value.state is not FeatureState.ENABLED for fact in available):
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=available)
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if not any(fact.value.state is FeatureState.ENABLED for fact in available):
        problems = tuple(fact for fact in (current, legacy) if isinstance(fact, UnavailableFact))
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    exposure = next(fact for fact in available if fact.value.state is FeatureState.ENABLED)
    remediation = software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value)
    if isinstance(ipsec_authentication, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(ipsec_authentication,))
    if ipsec_authentication.value.state is MitigationState.EFFECTIVE:
        return MitigatedResult(
            vulnerability_id=VULNERABILITY_ID,
            mitigated_conditions=(MitigatedCondition(condition=exposure, mitigations=(ipsec_authentication,)),),
            context=(eos_release,),
            remediation=remediation,
        )
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(exposure,),
        context=(eos_release,),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA172(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0172.

    Expected Results
    ----------------
    * Success: EOS is outside scope or both supported observations prove OSPFv3 is absent.
    * Failure: An affected EOS release has OSPFv3 configured without complete IPsec authentication coverage.
    * Mitigated: IPsec authentication covers every configured OSPFv3 interface scope on an affected release.
    * Error: Required EOS, OSPFv3 configuration, or IPsec authentication state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA172:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        Ospfv3ConfiguredFact,
        LegacyOspfv3ConfiguredFact,
        Ospfv3IpsecAuthenticationFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0172."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa172(
            self.fact(EosVersionFact),
            self.fact(Ospfv3ConfiguredFact),
            self.fact(LegacyOspfv3ConfiguredFact),
            self.fact(Ospfv3IpsecAuthenticationFact),
        )
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
