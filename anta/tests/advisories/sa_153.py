# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 153."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactsBase, fact_field, facts_dataclass
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedEosRelease, AffectedResult, EosReleaseAssessment, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import AllOf, ConditionalAction, FixedRelease, OperationalAction, RemediationPlan, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=4),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
CLEAN_LOGS = ConditionalAction(
    "the affected trace levels were enabled",
    OperationalAction("Clean up current and rotated agent logs as described in the advisory."),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0153",
    last_updated=date(2026, 9, 22),
    title="Security Advisory 0153",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73465",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Private keys may be written in plaintext to ConfigAgent logs when risky tracing is enabled.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73466",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="User passwords may be written in plaintext to Aaa logs when risky tracing is enabled.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73467",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="TACACS+ shared keys may be written in plaintext to Aaa logs when risky tracing is enabled.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24709-security-advisory-0153",
    description=(
        "On affected Arista EOS releases, specialized non-standard agent tracing may write plaintext private keys, user passwords, or "
        "TACACS+ shared keys to agent logs."
    ),
)


def _assess_sa153_issue(vulnerability_id: str, version: Fact[EosVersionFact]) -> VulnerabilityResult:
    """Assess one trace-driven exposure from the EOS release alone."""
    eos_release = assess_eos_scope(vulnerability_id, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        conditions=(AffectedEosRelease(eos_release.fact),),
        remediation=RemediationPlan(AllOf((software_version_action(FIXED_RELEASES, current_version=eos_release.fact.value), CLEAN_LOGS))),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA153(_AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0153.

    Expected Results
    ----------------
    * Not Affected: EOS is outside the affected releases.
    * Affected: EOS is within the affected releases.
    * Error: The EOS version cannot be determined.

    Notes
    -----
    Each issue requires an advisory-identified agent trace level, which this test does not use. An operator can enable
    the trace at any time with `start trace`, which leaves no running-config record and disappears from `show trace`
    once the timer expires, so trace state cannot rule out exposure.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA153:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0153."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive EOS state, assess each vulnerability, and project it."""
        facts = self.Facts.collect(self)
        for vulnerability in ADVISORY.vulnerabilities:
            atomic_result = self.result.add(f"Verify {vulnerability.id}.", vulnerability_ids=(vulnerability.id,))
            project_vulnerability_result(atomic_result, _assess_sa153_issue(vulnerability.id, facts.version))
