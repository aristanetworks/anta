# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 175."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.routing import PimSparseModeFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VulnerabilityResult
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
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lte=32),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0175",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0175",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73468",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A crafted packet may prematurely expire multicast forwarding state on PIM sparse-mode interfaces.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24731-security-advisory-0175",
    description=(
        "On affected Arista EOS releases with PIM sparse mode configured, a crafted packet can prematurely expire multicast forwarding state "
        "and temporarily disrupt multicast traffic."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa175(version: Fact[EOSVersion], sparse_mode: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS applicability and PIM sparse-mode exposure."""
    if not isinstance(sparse_mode, UnavailableFact) and sparse_mode.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(sparse_mode,))

    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(sparse_mode, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=(sparse_mode,))
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_release,),
        conditions=(cast("AvailableFact[FeatureValue]", sparse_mode),),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA175(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0175.

    Expected Results
    ----------------
    * Success: The test passes when the EOS version is outside scope or no PIM sparse-mode interface is configured.
    * Failure: The test fails when an affected EOS version has an IPv4 or IPv6 PIM sparse-mode interface.
    * Error: The test errors when required EOS version or PIM sparse-mode state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA175:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, PimSparseModeFact)
    description = "Verify whether the device is impacted by Security Advisory 0175."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa175(self.fact(EosVersionFact), self.fact(PimSparseModeFact))
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
