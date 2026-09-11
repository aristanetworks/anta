# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 163."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.aaa import LevelZeroCommandAuthorizationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiMtlsAuthorizationFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, MitigationState, MitigationValue, UnavailableFact
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
    VersionRule(major=4, minor=36, patch_eq=0),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32, patch_lte=11),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30),
    VersionRule(major=4, minor=29),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

# The source comment questioning CVX does not narrow this test: the advisory otherwise describes
# the complete EOS platform scope and the advisory owner explicitly rejected a CVX exclusion.
ADVISORY = _AdvisoryMetadata(
    sa_number="0163",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0163",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73461",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="OpenConfig gRPC requests may be authorized using the wrong AAA privilege level.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24719-security-advisory-0163",
    description=(
        "On affected EOS releases, an authenticated OpenConfig gRPC request using mutual TLS and request authorization may use privilege "
        "level zero and the wrong AAA command-authorization method list."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa163(version: Fact[EOSVersion], exposure: Fact[FeatureValue], mitigation: Fact[MitigationValue]) -> VulnerabilityResult:
    """Assess EOS scope, exposed OpenConfig transport state, and the documented AAA mitigation."""
    if not isinstance(exposure, UnavailableFact) and exposure.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(exposure,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(exposure, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(exposure,))
    if isinstance(mitigation, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(mitigation,))
    remediation = software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value)
    if mitigation.value.state is MitigationState.EFFECTIVE:
        return MitigatedResult(
            vulnerability_id=VULNERABILITY_ID,
            mitigated_conditions=(MitigatedCondition(condition=cast("AvailableFact[FeatureValue]", exposure), mitigations=(mitigation,)),),
            context=(eos_release,),
            remediation=remediation,
        )
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(cast("AvailableFact[FeatureValue]", exposure),),
        context=(eos_release,),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA163(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0163.

    Expected Results
    ----------------
    * Success: EOS is outside scope or no enabled gNMI transport combines mutual TLS with request authorization.
    * Failure: An affected release has an exposed transport without the documented AAA mitigation.
    * Mitigated: The exposed transport is covered by explicit privilege-level-zero AAA authorization.
    * Error: Required EOS, transport, SSL-profile, or AAA state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA163:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnmiMtlsAuthorizationFact, LevelZeroCommandAuthorizationFact)
    description = "Verify whether the device is impacted by Security Advisory 0163."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa163(self.fact(EosVersionFact), self.fact(GnmiMtlsAuthorizationFact), self.fact(LevelZeroCommandAuthorizationFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
