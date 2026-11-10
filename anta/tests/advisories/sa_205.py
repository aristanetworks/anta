# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 205."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.certificates import EstCaCertificateAutoUpdateFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (VersionRule(major=4, minor=36, patch_eq=1),)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0205",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0205",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-120975",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="A malicious packet may terminate AutoCertMgmt and prevent automatic renewal of managed X.509 certificates.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25027-security-advisory-0205",
    description="Affected EOS releases with automatic CA certificate retrieval enabled may stop renewing managed certificates.",
)
VULNERABILITY_ID = "CVE-2026-120975"


def _assess_sa205(version: Fact[EosVersionFact], auto_update: Fact[EstCaCertificateAutoUpdateFact]) -> VulnerabilityResult:
    """Assess the affected release and configured automatic CA retrieval."""
    if not isinstance(auto_update, UnavailableFact) and auto_update.value.state is FeatureState.DISABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(auto_update,))
    eos_scope = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(eos_scope, NotAffectedResult):
        return eos_scope
    problems = (eos_scope.problems if isinstance(eos_scope, ErrorResult) else ()) + ((auto_update,) if isinstance(auto_update, UnavailableFact) else ())
    if isinstance(eos_scope, ErrorResult) or isinstance(auto_update, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(eos_scope,),
        conditions=(auto_update,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_scope.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA205(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0205.

    Expected Results
    ----------------
    * Not Affected: EOS is outside the affected releases, no EST protocol is configured, or CA auto-update is disabled on every EST protocol.
    * Affected: An affected EOS release has CA auto-update enabled on at least one EST protocol.
    * Error: Required EOS version or CA auto-update evidence is unavailable, incomplete, malformed, or invalid.

    Notes
    -----
    The EST detail command reports configured CA auto-update. The test does not require a referencing certificate profile, enrollment,
    successful retrieval, or a currently valid protocol configuration; those operational states do not establish safety.

    One enabled protocol establishes exposure even if another protocol's setting is incomplete or malformed. Without an enabled protocol,
    unresolved settings prevent a Not Affected conclusion. Empty inventory or explicitly disabled retrieval removes the necessary feature
    and is Not Affected rather than Mitigated.

    The advisory applies across EOS platforms; no hardware-family gate is used. Software scope is the 4.36.1 release, including its hotfixes,
    up to the fixed 4.36.2F release. Exploitation and AutoCertMgmt crash indicators are not assessed.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA205:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        auto_update: Fact[EstCaCertificateAutoUpdateFact] = fact_field(EstCaCertificateAutoUpdateFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0205."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect configured CA retrieval, assess the issue, and project its result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa205(facts.version, facts.auto_update)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
