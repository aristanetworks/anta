# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 178."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import SnmpV3AuthenticationFact, SnmpV3CredentialSyntaxFact
from anta._advisory.facts.models import (
    AvailableFact,
    CredentialSyntaxState,
    Fact,
    FactsBase,
    FeatureState,
    MitigationState,
    UnavailableFact,
    fact_field,
    facts_dataclass,
)
from anta._advisory.facts.software import SA178HotfixFact
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
    VersionRule(major=4, minor=36, patch_lte=2),
    VersionRule(major=4, minor=35, patch_lte=6),
    VersionRule(major=4, minor=34, patch_lte=8),
    VersionRule(major=4, minor=33, patch_lte=10),
    VersionRule(major=4, minor_lt=33),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
# pylint: enable=duplicate-code
HOTFIX_RELEASES = frozenset({"4.36.2F", "4.35.6M", "4.34.8M", "4.33.10M"})
CONVERT_CREDENTIALS = RunCommand(("configure convert new-syntax",))

ADVISORY = _AdvisoryMetadata(
    sa_number="0178",
    last_updated=date(2026, 10, 28),
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


def _assess_sa178(
    version: Fact[EosVersionFact],
    authentication: Fact[SnmpV3AuthenticationFact],
    credential_syntax: Fact[SnmpV3CredentialSyntaxFact],
    hotfix: Fact[SA178HotfixFact],
) -> VulnerabilityResult:
    """Assess EOS software, the release-specific hotfix, and the legacy SNMPv3 credential-syntax prerequisite.

    Legacy or mixed credential syntax is required for exposure. Upgrading EOS or installing the hotfix does not convert existing credentials, so
    credentials that retain legacy syntax on fixed or hotfixed software still require ``configure convert new-syntax``.
    """
    if not isinstance(authentication, UnavailableFact) and authentication.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(authentication,))
    if not isinstance(credential_syntax, UnavailableFact) and credential_syntax.value.state not in {
        CredentialSyntaxState.LEGACY,
        CredentialSyntaxState.MIXED,
    }:
        return NotAffectedResult(vulnerability_id=VULNERABILITY_ID, decisive=(credential_syntax,))

    software_context = assess_eos_version(version, AFFECTED_VERSION_MATRIX)
    hotfix_applies = (
        isinstance(software_context, EosReleaseAssessment)
        and software_context.relation is VersionRelation.AFFECTED
        and str(software_context.fact.value) in HOTFIX_RELEASES
    )
    required = (software_context, authentication, credential_syntax, hotfix) if hotfix_applies else (software_context, authentication, credential_syntax)
    problems = tuple(fact for fact in required if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=VULNERABILITY_ID, problems=problems)

    assert isinstance(software_context, EosReleaseAssessment)  # noqa: S101
    assert not isinstance(authentication, UnavailableFact)  # noqa: S101
    assert not isinstance(credential_syntax, UnavailableFact)  # noqa: S101
    configured_authentication = authentication
    legacy_credential_syntax = credential_syntax
    applicable_hotfix = hotfix if hotfix_applies and isinstance(hotfix, AvailableFact) else None
    if software_context.relation is VersionRelation.AFFECTED and (applicable_hotfix is None or applicable_hotfix.value.state is not MitigationState.EFFECTIVE):
        hotfix_conditions = () if applicable_hotfix is None else (applicable_hotfix,)
        return AffectedResult(
            vulnerability_id=VULNERABILITY_ID,
            context=(software_context,),
            conditions=(configured_authentication, legacy_credential_syntax, *hotfix_conditions),
            remediation=RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=software_context.fact.value), CONVERT_CREDENTIALS))),
        )

    return AffectedResult(
        vulnerability_id=VULNERABILITY_ID,
        context=(EosReleaseAssessment(software_context.fact, VersionRelation.FIXED),),
        conditions=(configured_authentication, legacy_credential_syntax),
        remediation=RemediationPlan(CONVERT_CREDENTIALS),
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA178(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0178.

    Expected Results
    ----------------
    * Not Affected: No SNMPv3 authentication key is configured, or every key uses encrypted syntax.
    * Affected: An SNMPv3 authentication key uses legacy or mixed syntax.
    * Error: The required EOS version, authentication-key state, or credential syntax cannot be determined.

    Notes
    -----
    Legacy or mixed credential syntax is reported as affected on both affected and fixed software, because upgrading EOS does not rewrite existing
    configuration. Affected software requires an upgrade followed by credential conversion; fixed software requires credential conversion only.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA178:
    ```
    """

    @facts_dataclass
    class Facts(FactsBase):
        """Collected facts required to assess the advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)
        authentication: Fact[SnmpV3AuthenticationFact] = fact_field(SnmpV3AuthenticationFact)
        credential_syntax: Fact[SnmpV3CredentialSyntaxFact] = fact_field(SnmpV3CredentialSyntaxFact)
        hotfix: Fact[SA178HotfixFact] = fact_field(SA178HotfixFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    description = "Verify whether the device is impacted by Security Advisory 0178."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess the vulnerability, and project it."""
        facts = self.Facts.collect(self)
        finding = _assess_sa178(facts.version, facts.authentication, facts.credential_syntax, facts.hotfix)
        atomic_result = self.result.add(f"Verify {VULNERABILITY_ID}.", vulnerability_ids=(VULNERABILITY_ID,))
        project_vulnerability_result(atomic_result, finding)
