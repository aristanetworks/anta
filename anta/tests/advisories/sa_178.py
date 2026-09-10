# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 178."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import SnmpV3AuthenticationFact, SnmpV3CredentialSyntaxFact
from anta._advisory.facts.models import (
    CredentialSyntaxState,
    CredentialSyntaxValue,
    Fact,
    FactDefinition,
    FeatureState,
    FeatureValue,
    UnavailableFact,
)
from anta._advisory.findings.assessment import assess_eos_version
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, RemediationPlan, RunCommand, Sequence, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

# pylint: disable=duplicate-code
AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lte=7),
    VersionRule(major=4, minor=33, patch_lte=9),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
# pylint: enable=duplicate-code
CONVERT_CREDENTIALS = RunCommand(("configure convert new-syntax",))

ADVISORY = _AdvisoryMetadata(
    sa_number="0178",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0178",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73440",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="SNMPv3 authentication keys may be exposed as hashed localized values in configuration.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24734-security-advisory-0178",
    description=(
        "On affected Arista EOS releases, local or remote SNMPv3 authentication keys may be exposed as one-way hashed localized values "
        "in running and sanitized configuration."
    ),
)
VULNERABILITY_ID = ADVISORY.vulnerabilities[0].id


def _assess_sa178(  # pylint: disable=too-many-return-statements
    version: Fact[EOSVersion],
    authentication: Fact[FeatureValue],
    credential_syntax: Fact[CredentialSyntaxValue],
) -> VulnerabilityResult:
    """Assess EOS software and the legacy SNMPv3 credential-syntax prerequisite.

    Legacy or mixed credential syntax is required for exposure. Upgrading EOS does not convert existing credentials, so credentials that
    retain legacy syntax on a fixed release still require ``configure convert new-syntax``.
    """
    if not isinstance(authentication, UnavailableFact) and authentication.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(authentication,))
    if not isinstance(credential_syntax, UnavailableFact) and credential_syntax.value.state not in {
        CredentialSyntaxState.LEGACY,
        CredentialSyntaxState.MIXED,
    }:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(credential_syntax,))

    software_context = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    problems = tuple(fact for fact in (software_context, authentication, credential_syntax) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    assert isinstance(software_context, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(authentication, UnavailableFact)  # noqa: S101
    assert not isinstance(credential_syntax, UnavailableFact)  # noqa: S101
    configured_authentication = authentication
    legacy_credential_syntax = credential_syntax
    if software_context.relation is VersionRelation.AFFECTED:
        return AffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            context=(software_context,),
            conditions=(configured_authentication, legacy_credential_syntax),
            remediation=RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=software_context.fact.value), CONVERT_CREDENTIALS))),
        )

    if software_context.relation is VersionRelation.OUTSIDE_SCOPE:
        software_context = EosReleaseAssessment(software_context.fact, VersionRelation.FIXED)

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(software_context,),
        conditions=(configured_authentication, legacy_credential_syntax),
        remediation=RemediationPlan(CONVERT_CREDENTIALS),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA178(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0178.

    Expected Results
    ----------------
    * Success: The test will pass if no SNMPv3 authentication key is configured, or every key uses encrypted syntax.
    * Failure: The test will fail if an SNMPv3 authentication key uses legacy or mixed syntax. Affected software requires an upgrade followed by
      credential conversion; fixed software requires credential conversion because upgrading does not rewrite existing configuration.
    * Error: The test will error if the required EOS version, authentication-key state, or credential syntax cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA178:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (EosVersionFact, SnmpV3AuthenticationFact, SnmpV3CredentialSyntaxFact)
    description = "Verify whether the device is impacted by Security Advisory 0178."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        finding = _assess_sa178(
            self.fact(EosVersionFact),
            self.fact(SnmpV3AuthenticationFact),
            self.fact(SnmpV3CredentialSyntaxFact),
        )
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
