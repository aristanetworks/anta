# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 158."""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar, cast

from anta._advisory.base import _PREVIEW_WARNING, _AntaAdvisoryTest
from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import (
    GnpsiAuthenticationExposureFact,
    GnpsiEosRpcAuthTraceFact,
    GnpsiMutualTlsSpiffeMitigationFact,
    GnpsiTransportFact,
)
from anta._advisory.facts.models import AvailableFact, Fact, FactDefinition, FeatureState, FeatureValue, MitigationState, MitigationValue, UnavailableFact
from anta._advisory.findings.assessment import assess_eos_scope
from anta._advisory.findings.models import (
    AffectedResult,
    EosReleaseAssessment,
    ErrorResult,
    MitigatedCondition,
    MitigatedResult,
    NotAffectedResult,
    VulnerabilityResult,
)
from anta._advisory.findings.projection import project_vulnerability_result
from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.optional_commands import OptionalCommandsMixin
from anta._advisory.remediation import AllOf, ConditionalAction, FixedRelease, OperationalAction, RemediationPlan, software_version_action, software_version_plan
from anta._eos.version import EOSVersion
from anta.decorators import preview_test_class

AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_gte=2, patch_lte=7),
)
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
ADVISORY = _AdvisoryMetadata(
    sa_number="0158",
    last_updated=date(2026, 9, 9),
    title="Security Advisory 0158",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-73456",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="An unauthenticated gNPSI client may execute arbitrary code and gain administrative control.",
        ),
        _AdvisoryVulnerability(
            id="CVE-2026-73457",
            severity=_AdvisoryVulnerabilitySeverity.MEDIUM,
            description="Explicit gNPSI authentication tracing may log client credentials in clear text.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/24714-security-advisory-0158",
    description="On affected EOS releases, configured gNPSI authentication or tracing may permit code execution or credential disclosure.",
)
CODE_EXECUTION_ID, LOGGING_ID = (vulnerability.id for vulnerability in ADVISORY.vulnerabilities)


def _logging_remediation_plan(current_version: EOSVersion) -> RemediationPlan:
    """Return the software and conditional response actions for possible credential logging."""
    return RemediationPlan(
        AllOf(
            (
                software_version_action(FIXED_RELEASES, current_version=current_version),
                ConditionalAction(
                    "gNPSI credentials were logged",
                    OperationalAction("Clean up affected gNPSI log files, including rotated logs, as described in the advisory."),
                ),
                ConditionalAction(
                    "logged information contained secrets",
                    OperationalAction("Rotate exposed or compromised gNPSI client credentials as described in the advisory."),
                ),
            )
        )
    )


def _assess_gnpsi_issue(
    vulnerability_id: str,
    version: Fact[EOSVersion],
    transport: Fact[FeatureValue],
    prerequisite: Fact[FeatureValue],
) -> VulnerabilityResult:
    """Assess one gNPSI issue after its independent prerequisite is normalized."""
    if not isinstance(prerequisite, UnavailableFact) and prerequisite.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(prerequisite,))
    if not isinstance(transport, UnavailableFact) and transport.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=vulnerability_id, decisive=(transport,))
    eos_release = assess_eos_scope(vulnerability_id, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    problems = tuple(fact for fact in (transport, prerequisite) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=vulnerability_id, problems=problems)
    return AffectedResult(
        vulnerability_id=vulnerability_id,
        conditions=(cast("AvailableFact[FeatureValue]", transport), cast("AvailableFact[FeatureValue]", prerequisite)),
        context=(eos_release,),
        remediation=software_version_plan(FIXED_RELEASES, current_version=eos_release.fact.value),
    )


def _assess_logging_issue(
    version: Fact[EOSVersion],
    transport: Fact[FeatureValue],
    trace: Fact[FeatureValue],
    authentication_mitigation: Fact[MitigationValue],
) -> VulnerabilityResult:
    """Assess credential logging and the exact source-defined authentication mitigation."""
    if not isinstance(trace, UnavailableFact) and trace.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=LOGGING_ID, decisive=(trace,))
    if not isinstance(transport, UnavailableFact) and transport.value.state is not FeatureState.ENABLED:
        return NotAffectedResult(vulnerability_id=LOGGING_ID, decisive=(transport,))
    eos_release = assess_eos_scope(LOGGING_ID, version, AFFECTED_VERSION_MATRIX)
    if not isinstance(eos_release, EosReleaseAssessment):
        return eos_release
    problems = tuple(fact for fact in (transport, trace, authentication_mitigation) if isinstance(fact, UnavailableFact))
    if problems:
        return ErrorResult(vulnerability_id=LOGGING_ID, problems=problems)
    remediation = _logging_remediation_plan(eos_release.fact.value)
    available_trace = cast("AvailableFact[FeatureValue]", trace)
    available_mitigation = cast("AvailableFact[MitigationValue]", authentication_mitigation)
    if available_mitigation.value.state is MitigationState.EFFECTIVE:
        return MitigatedResult(
            vulnerability_id=LOGGING_ID,
            mitigated_conditions=(MitigatedCondition(condition=available_trace, mitigations=(available_mitigation,)),),
            context=(eos_release,),
            remediation=remediation,
        )
    return AffectedResult(
        vulnerability_id=LOGGING_ID,
        conditions=(cast("AvailableFact[FeatureValue]", transport), available_trace),
        context=(eos_release,),
        remediation=remediation,
    )


@preview_test_class(warning_message=_PREVIEW_WARNING)
class SA158(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Verify whether the device is impacted by Security Advisory 0158.

    Expected Results
    ----------------
    * Success: EOS is outside scope, gNPSI is disabled, or the issue-specific authentication or trace prerequisite is absent.
    * Failure: An affected EOS release has an enabled gNPSI transport and the issue-specific prerequisite.
    * Mitigated: Credential tracing is enabled, but every enabled transport uses mutual TLS with only x509-spiffe authentication.
    * Error: Required EOS, gNPSI transport, authentication, or trace state cannot be determined.

    CVE-2026-73456 evaluates TLS or mTLS authentication combinations. CVE-2026-73457 evaluates explicit EosRpcAuth tracing and the
    source-defined mutual-TLS/x509-spiffe mitigation across every enabled transport.

    Examples
    --------
    ```yaml
    anta.tests.advisories:
      - SA158:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (
        EosVersionFact,
        GnpsiTransportFact,
        GnpsiAuthenticationExposureFact,
        GnpsiEosRpcAuthTraceFact,
        GnpsiMutualTlsSpiffeMitigationFact,
    )
    description = "Verify whether the device is impacted by Security Advisory 0158."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Derive facts, assess both vulnerabilities, and project them."""
        version = self.fact(EosVersionFact)
        transport = self.fact(GnpsiTransportFact)
        findings = (
            (CODE_EXECUTION_ID, _assess_gnpsi_issue(CODE_EXECUTION_ID, version, transport, self.fact(GnpsiAuthenticationExposureFact))),
            (
                LOGGING_ID,
                _assess_logging_issue(
                    version,
                    transport,
                    self.fact(GnpsiEosRpcAuthTraceFact),
                    self.fact(GnpsiMutualTlsSpiffeMitigationFact),
                ),
            ),
        )
        for vulnerability_id, finding in findings:
            atomic = self.result.add(f"Verify {vulnerability_id}.", vulnerability_ids=(vulnerability_id,))
            project_vulnerability_result(atomic, finding)
