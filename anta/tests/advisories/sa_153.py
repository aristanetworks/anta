# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 153."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactDefinition, FeatureState, FeatureValue, UnavailableFact
from anta._advisory.facts.tracing import (
    AaaPasswordTraceFact,
    AaaTacacsKeyTraceFact,
    ConfigAgentPrivateKeyTraceFact,
)
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import FixedRelease, OperationalAction, RemediationPlan, Sequence, software_version_action
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=4),
    VersionRule(major=4, minor=34),
    VersionRule(major=4, minor=33),
    VersionRule(major=4, minor=32),
    VersionRule(major=4, minor=31),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
)
CLEAN_LOGS = OperationalAction("Clean current and rotated agent logs if the affected trace levels were enabled.")

ADVISORY = _AdvisoryMetadata(
    sa_number="0153",
    last_updated=date(2026, 9, 9),
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
PRIVATE_KEY_ID, PASSWORD_ID, TACACS_KEY_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _assess_sa153_issue(
    vulnerability_id: str,
    version: Fact[EOSVersion],
    risky_trace: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess one independent trace-driven exposure."""
    if not isinstance(risky_trace, UnavailableFact) and risky_trace.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(risky_trace,))

    eos_release = assess_eos_scope(vulnerability_id, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    if isinstance(risky_trace, UnavailableFact):
        return ErrorResult(vulnerability_id=vulnerability_id, problems=(risky_trace,))

    remediation = RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=eos_release.fact.value), CLEAN_LOGS)))
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        context=(eos_release,),
        conditions=(risky_trace,),
        remediation=remediation,
    )


def _assess_private_key(
    version: Fact[EOSVersion],
    risky_trace: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess private-key exposure in ConfigAgent logs."""
    return _assess_sa153_issue(PRIVATE_KEY_ID, version, risky_trace)


def _assess_password(
    version: Fact[EOSVersion],
    risky_trace: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess user-password exposure in Aaa logs."""
    return _assess_sa153_issue(PASSWORD_ID, version, risky_trace)


def _assess_tacacs_key(
    version: Fact[EOSVersion],
    risky_trace: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess TACACS+ shared-key exposure in Aaa logs."""
    return _assess_sa153_issue(TACACS_KEY_ID, version, risky_trace)


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA153(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0153.

    Expected Results
    ----------------
    * Success: Each issue passes when the EOS version is outside its affected scope or its risky trace level is disabled.
    * Failure: An issue fails when an affected EOS release has its risky trace level enabled.
    * Error: An issue errors when required EOS version or trace state cannot be determined.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA153:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        ConfigAgentPrivateKeyTraceFact,
        AaaPasswordTraceFact,
        AaaTacacsKeyTraceFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0153."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive the declared facts, assess each vulnerability, and project it."""
        version = self.fact(EosVersionFact)
        findings = (
            _assess_private_key(version, self.fact(ConfigAgentPrivateKeyTraceFact)),
            _assess_password(version, self.fact(AaaPasswordTraceFact)),
            _assess_tacacs_key(version, self.fact(AaaTacacsKeyTraceFact)),
        )
        for vulnerability, finding in zip(ADVISORY.vulnerabilities, findings, strict=True):
            atomic_result = self.result.add(f"Verify {vulnerability.id}.", vulnerability_ids=(vulnerability.id,))
            project_vulnerability_result(atomic_result, finding)
