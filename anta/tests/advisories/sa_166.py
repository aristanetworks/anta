# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 166."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact
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
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_eq=0),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
    VersionRule(major=4, minor=30),
    VersionRule(major=4, minor=29),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, hotfix=1, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0166",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0166",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73464",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted authenticated gNMI request may execute arbitrary code with root privileges.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24722-security-advisory-0166",
    description="On affected EOS releases with gNMI enabled, a malicious authenticated client may execute arbitrary code with root privileges.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa166(version: Fact[EOSVersion], gnmi: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS scope and enabled gNMI transport exposure."""
    if not isinstance(gnmi, UnavailableFact) and gnmi.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(gnmi,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(gnmi, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(gnmi,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(cast("AvailableFact[FeatureValue]", gnmi),),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA166(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0166.

    Expected Results
    ----------------
    * Success: EOS is outside scope or no gNMI transport is enabled.
    * Failure: An affected EOS release has an enabled gNMI transport.
    * Error: Required EOS or gNMI state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA166:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, GnmiTransportFact)
    description = "Verify whether the device is impacted by Security Advisory 0166."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa166(self.fact(EosVersionFact), self.fact(GnmiTransportFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
