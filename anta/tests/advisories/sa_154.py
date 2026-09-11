# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 154."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.routing import BfdAuthenticationFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

# pylint: disable=duplicate-code  # Advisory version metadata stays local even when identical.
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
# pylint: enable=duplicate-code

ADVISORY = _AdvisoryMetadata(
    sa_number="0154",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0154",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73458",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted packet may bring down operational authenticated BFD sessions.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24710-security-advisory-0154",
    description=(
        "On affected EOS releases with authenticated BFD sessions configured, a crafted packet can cause BFD sessions to go down and may "
        "trigger undesirable routing changes."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa154(version: Fact[EOSVersion], bfd: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS applicability and configured BFD authentication exposure."""
    if not isinstance(bfd, UnavailableFact) and bfd.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(bfd,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(bfd, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(bfd,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release,),
        conditions=(cast("AvailableFact[FeatureValue]", bfd),),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA154(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0154.

    BFD is exposed when it is enabled and authentication is configured. Active peers are not
    required because peer state is transient and a configured interface or peer may establish
    a session after the test runs.

    Expected Results
    ----------------
    * Success: EOS is outside scope, BFD is shut down, or BFD authentication is not configured.
    * Failure: An affected EOS release has BFD enabled with authentication configured.
    * Error: Required EOS or BFD state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA154:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, BfdAuthenticationFact)
    description = "Verify whether the device is impacted by Security Advisory 0154."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa154(self.fact(EosVersionFact), self.fact(BfdAuthenticationFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
