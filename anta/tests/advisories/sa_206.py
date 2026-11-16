# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 206."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.bfd import BfdAuthenticationUnavailableFact, BfdKeyedAuthenticationFact
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

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor_gte=22, minor_lte=32),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=36, patch_lt=3),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
VULNERABILITY_ID = "CVE-2026-121368"
ADVISORY = _AdvisoryMetadata(
    sa_number="0206",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0206",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id=VULNERABILITY_ID,
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="A crafted BFD packet may reboot a device configured with keyed MD5 or SHA1 authentication.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25028-security-advisory-0206",
    description="Affected EOS releases with keyed BFD authentication may reboot after receiving a crafted BFD packet.",
)


def _assess_sa206(
    version: Fact[EosVersionFact],
    authentication: Fact[BfdKeyedAuthenticationFact],
) -> VulnerabilityResult:
    """Assess affected software and configured keyed authentication while BFD is enabled."""
    if not isinstance(authentication, UnavailableFact) and authentication.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(authentication,))
    release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, NotAffectedResult):
        return release
    authentication_problems = ()
    if isinstance(authentication, BfdAuthenticationUnavailableFact):
        authentication_problems = authentication.problems
    elif isinstance(authentication, UnavailableFact):
        authentication_problems = (authentication,)
    problems = (
        *(release.problems if isinstance(release, ErrorResult) else ()),
        *authentication_problems,
    )
    if isinstance(release, ErrorResult) or isinstance(authentication, UnavailableFact):
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(authentication,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA206(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0206.

    Expected Results
    ----------------
    * Not Affected: EOS is outside scope, BFD is shut down, or no MD5/SHA1 authentication is configured.
    * Affected: Affected EOS has MD5/SHA1 BFD authentication, optionally meticulous.
    * Error: Required software or configuration evidence cannot be interpreted.

    Notes
    -----
    Configured global, peer or interface authentication is assessed without requiring
    live peers or working keys. BFD administrative shutdown excludes exposure. Conservatively,
    interface overrides do not cancel a configured global MD5/SHA1 mode. Simple
    authentication alone is outside scope. All EOS platforms are included.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA206:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Software and persistent authentication configuration."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        authentication: Fact[BfdKeyedAuthenticationFact] = fact_field(BfdKeyedAuthenticationFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0206."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect declared facts and project the vulnerability result."""
        facts = self.Facts.collect(self)
        finding = _assess_sa206(facts.version, facts.authentication)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
