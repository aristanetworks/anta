# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 152."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.aaa import LoginAuthenticationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management_access import PasswordManagementServiceFact
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
    VersionRule(major=4, minor=36, patch_lte=0),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)

ADVISORY = _AdvisoryMetadata(
    sa_number="0152",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0152",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-19641",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="A crafted password may exhaust pending authentication sessions and prevent legitimate logins.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24708-security-advisory-0152",
    description=(
        "On affected EOS releases with login authentication and a password-capable SSH or Telnet service enabled, crafted passwords may "
        "create orphan sessions and exhaust authentication resources."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa152(version: Fact[EOSVersion], login_authentication: Fact[FeatureValue], password_service: Fact[FeatureValue]) -> VulnerabilityResult:
    """Assess EOS scope and both required password-authentication conditions."""
    for fact in (login_authentication, password_service):
        if not isinstance(fact, UnavailableFact) and fact.value.state is not FeatureState.ENABLED:
            return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(fact,))
    eos_release = assess_eos_scope(VULNERABILITY_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    problems = tuple(fact for fact in (login_authentication, password_service) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)
    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        conditions=(
            cast("AvailableFact[FeatureValue]", login_authentication),
            cast("AvailableFact[FeatureValue]", password_service),
        ),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA152(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0152.

    Expected Results
    ----------------
    * Success: EOS is outside scope, login authentication is disabled, or no password-capable management service is enabled.
    * Failure: Affected EOS has login authentication and password-capable SSH or Telnet enabled.
    * Error: Required EOS, AAA, or management-service configuration cannot be determined.

    SSH and Telnet exposure is determined from configuration, including configured VRF scope. Current VRF operational state is transient and
    does not prove safety because a down VRF can return without any management-service configuration change.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA152:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, LoginAuthenticationFact, PasswordManagementServiceFact)
    description = "Verify whether the device is impacted by Security Advisory 0152."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess the vulnerability, and project it."""
        finding = _assess_sa152(self.fact(EosVersionFact), self.fact(LoginAuthenticationFact), self.fact(PasswordManagementServiceFact))
        atomic = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic, finding)
