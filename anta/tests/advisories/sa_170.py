# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 170."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiAuthorizationFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VulnerabilityResult
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
    VersionRule(major=4, minor_gte=24, minor_lte=32),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0170",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0170",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-19640",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Existing gNMI subscriptions may retain authorization granted before an AAA policy change.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24726-security-advisory-0170",
    description="On affected EOS releases, authenticated gNMI users may retain access beyond their current authorization policy.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa170(version: Fact[EOSVersion], authorization: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS scope and enabled gNMI request authorization."""
    if not isinstance(authorization, UnavailableFact) and authorization.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(authorization,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(authorization, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(authorization,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(cast("AvailableFact[FeatureValue]", authorization),),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA170(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0170.

    Expected Results
    ----------------
    * Success: EOS is outside scope or no enabled gNMI transport uses request authorization.
    * Failure: An affected EOS release has an enabled gNMI transport using request authorization.
    * Error: Required EOS or gNMI authorization state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA170:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnmiAuthorizationFact)
    description = "Verify whether the device is impacted by Security Advisory 0170."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa170(self.fact(EosVersionFact), self.fact(GnmiAuthorizationFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
