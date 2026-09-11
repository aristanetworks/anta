# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 159."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedEosRelease, AffectedResult, EosReleaseAssessment, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact, FactDefinition

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
    sa_number="0159",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0159",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73462",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Malformed network packets can cause the IGMP snooping agent to terminate unexpectedly.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24715-security-advisory-0159",
    description="Malformed network packets can cause the IGMP snooping agent to terminate unexpectedly and temporarily disrupt multicast traffic management.",
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa159(version: Fact[EOSVersion]) -> VulnerabilityResult:
    """Assess the version-only exposure because IGMP snooping requires no configuration."""
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(AffectedEosRelease(eos_release.fact),),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA159(_AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0159.

    Expected Results
    ----------------
    * Success: EOS is outside the affected releases.
    * Failure: EOS is within the affected releases; IGMP snooping is instantiated by default.
    * Error: The EOS version cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA159:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact,)
    description = "Verify whether the device is impacted by Security Advisory 0159."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive EOS state, assess the vulnerability, and project it."""
        finding = _assess_sa159(self.fact(EosVersionFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
