# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 218."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.http import EapiEnabledFact, HttpDefaultServicesFact
from anta._advisory.facts.models import Fact, FactsBase, FeatureState, UnavailableFact, fact_field, facts_dataclass
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lt=3),
    VersionRule(major=4, minor=36, patch_eq=3, hotfix_lt=2),
    VersionRule(major=4, minor=35, patch_lt=7),
    VersionRule(major=4, minor=35, patch_eq=7, hotfix_lt=2),
    VersionRule(major=4, minor=34, patch_lt=9),
    VersionRule(major=4, minor=34, patch_eq=9, hotfix_lt=2),
    VersionRule(major=4, minor=33, patch_lt=11),
    VersionRule(major=4, minor=33, patch_eq=11, hotfix_lt=2),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, hotfix=2, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0218",
    last_updated=date(2026, 11, 10),
    title="Security Advisory 0218",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-121371",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="An unauthenticated attacker may read arbitrary files through a crafted management HTTP request.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/25040-security-advisory-0218",
    description="Affected EOS releases with eAPI and management HTTP default services enabled may disclose files from the switch filesystem.",
)
VULNERABILITY_ID = "CVE-2026-121371"


def _assess_sa218(
    version: Fact[EosVersionFact],
    eapi: Fact[EapiEnabledFact],
    default_services: Fact[HttpDefaultServicesFact],
) -> VulnerabilityResult:
    """Assess the source-required configured services independently of transport activity."""
    for feature in (eapi, default_services):
        if not isinstance(feature, UnavailableFact) and feature.value.state is not FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(feature,))
    release = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    if isinstance(release, EosReleaseAssessment) and release.relation is VersionRelation.OUTSIDE_SCOPE:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(release,))
    problems = tuple(fact for fact in (release, eapi, default_services) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    assert isinstance(release, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(eapi, UnavailableFact)  # noqa: S101
    assert not isinstance(default_services, UnavailableFact)  # noqa: S101
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(release,),
        conditions=(eapi, default_services),
        remediation=software_version_plan(FIXED_RELEASES, current_version=release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA218(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0218.

    Expected Results
    ----------------
    * Not Affected: EOS is outside the affected releases, eAPI is disabled, or management HTTP default services are disabled.
    * Affected: An affected EOS release has eAPI and management HTTP default services enabled.
    * Error: Required software or service-setting evidence is unavailable, incomplete, malformed, or contradictory.

    Notes
    -----
    The test checks configured eAPI and default-service enablement. It does not use listener type, remote reachability, current requests,
    or transient running state to establish safety. HTTP, HTTPS, local HTTP and Unix-socket choices receive no transport exclusion;
    this conservative assessment does not claim that exploitation has been verified over every transport.

    Disabled eAPI removes an explicit advisory prerequisite even if another management HTTP service remains active. Disabling default
    services also removes a necessary feature and is Not Affected rather than Mitigated. The default-services setting is read from
    full-default configuration across both supported carrier contexts; an omitted directive is not treated as disabled.

    All EOS platforms are in scope. Exact four-component fixes are honored; earlier 4.x trains without a published fix remain in scope.
    The test assesses the EOS device itself, including an EOS switch managed by DMF. It does not inspect a DMF controller's bundled images,
    read files or logs, send exploit requests, or determine whether exploitation occurred. Remediation recommends fixed software.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA218:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """EOS release, configured eAPI enablement and explicit default-service setting."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        eapi: Fact[EapiEnabledFact] = fact_field(EapiEnabledFact)
        default_services: Fact[HttpDefaultServicesFact] = fact_field(HttpDefaultServicesFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0218."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Collect source-required service settings and project the independent finding."""
        facts = self.Facts.collect(self)
        finding = _assess_sa218(facts.version, facts.eapi, facts.default_services)
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
