# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 158."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnpsiAuthenticationExposureFact, GnpsiEosRpcAuthTraceFact, GnpsiMutualTlsSpiffeMitigationFact, GnpsiTransportFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, MitigationState, MitigationValue, SubFeature
from anta._advisory.findings.models import AffectedResult, ErrorResult, MitigatedResult, NotAffectedResult
from anta._advisory.remediation import (
    AllOf,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    OperationalAction,
    RemediationPlan,
    SoftwareTarget,
)
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_158 import ADVISORY, AFFECTED_VERSION_MATRIX, SA158, _assess_gnpsi_issue, _assess_logging_issue
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
Issue: TypeAlias = tuple[Status, str, RemediationPlan | None]
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
SOFTWARE_REMEDIATION = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), KnownFixedReleases(FIXED_RELEASES)))
LOGGING_REMEDIATION = RemediationPlan(
    AllOf(
        (
            ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), KnownFixedReleases(FIXED_RELEASES)),
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


def gnpsi_fact(
    definition: type[GnpsiTransportFact | GnpsiAuthenticationExposureFact | GnpsiEosRpcAuthTraceFact], name: str, state: FeatureState
) -> AvailableFact[FeatureValue]:
    """Build one normalized gNPSI fact for direct assessment tests."""
    return available_fact(definition, FeatureValue(SubFeature(FeatureName.GNPSI, name), state))


def authentication_mitigation(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build the exact gNPSI authentication mitigation for direct assessment tests."""
    return available_fact(GnpsiMutualTlsSpiffeMitigationFact, MitigationValue(state))


def test_sa158_assessment_contract() -> None:
    """Evaluate transport and issue-specific gNPSI prerequisites independently."""
    transport_enabled = gnpsi_fact(GnpsiTransportFact, "transport", FeatureState.ENABLED)
    transport_disabled = gnpsi_fact(GnpsiTransportFact, "transport", FeatureState.DISABLED)
    authentication_enabled = gnpsi_fact(GnpsiAuthenticationExposureFact, "exposed authentication mode", FeatureState.ENABLED)
    authentication_disabled = gnpsi_fact(GnpsiAuthenticationExposureFact, "exposed authentication mode", FeatureState.DISABLED)
    vulnerability_id = "CVE-2026-73456"
    assert isinstance(_assess_gnpsi_issue(vulnerability_id, unavailable_fact(EosVersionFact), transport_enabled, authentication_disabled), NotAffectedResult)
    assert isinstance(_assess_gnpsi_issue(vulnerability_id, unavailable_fact(EosVersionFact), transport_disabled, authentication_enabled), NotAffectedResult)
    assert isinstance(_assess_gnpsi_issue(vulnerability_id, eos_version_fact("4.36.1F"), transport_enabled, authentication_enabled), AffectedResult)
    assert isinstance(_assess_gnpsi_issue(vulnerability_id, eos_version_fact("4.36.2F"), transport_enabled, authentication_enabled), NotAffectedResult)
    assert isinstance(
        _assess_gnpsi_issue(vulnerability_id, eos_version_fact("4.36.1F"), transport_enabled, unavailable_fact(GnpsiAuthenticationExposureFact)),
        ErrorResult,
    )

    trace_enabled = gnpsi_fact(GnpsiEosRpcAuthTraceFact, "EosRpcAuth trace", FeatureState.ENABLED)
    mitigated = _assess_logging_issue(
        eos_version_fact("4.36.1F"),
        transport_enabled,
        trace_enabled,
        authentication_mitigation(MitigationState.EFFECTIVE),
    )
    assert isinstance(mitigated, MitigatedResult)
    assert mitigated.remediation == LOGGING_REMEDIATION
    affected = _assess_logging_issue(
        eos_version_fact("4.36.1F"),
        transport_enabled,
        trace_enabled,
        authentication_mitigation(MitigationState.INEFFECTIVE),
    )
    assert isinstance(affected, AffectedResult)
    assert affected.remediation == LOGGING_REMEDIATION
    assert isinstance(
        _assess_logging_issue(
            unavailable_fact(EosVersionFact),
            transport_disabled,
            unavailable_fact(GnpsiEosRpcAuthTraceFact),
            unavailable_fact(GnpsiMutualTlsSpiffeMitigationFact),
        ),
        NotAffectedResult,
    )


def test_sa158_version_boundaries() -> None:
    """Cover the source-defined bounded 4.34 range and newer trains."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.1F", AffectedStatus.NOT_AFFECTED),
            ("4.34.2F", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )


GNPSI_VULNERABLE: dict[str, object] = {
    "enabled": True,
    "transports": {"t2": {"enabled": True, "securityType": "tls", "authnUsernamePriority": ["x509-spiffe", "metadata", "x509-common-name"]}},
}
GNPSI_SAFE: dict[str, object] = {
    "enabled": True,
    "transports": {"t2": {"enabled": True, "securityType": "mtls", "authnUsernamePriority": ["x509-spiffe"]}},
}
GNPSI_DISABLED: dict[str, object] = {
    "enabled": False,
    "transports": {"t2": {"enabled": False, "securityType": "unknown", "authnUsernamePriority": []}},
}
TRACE_ENABLED = "EosRpcAuth           enabled  0123456789"


def expected_result(status: Status, issues: tuple[Issue, ...]) -> UnitTestResult:
    """Build parent and per-vulnerability expectations."""
    atomic_results: list[AtomicResult] = []
    for vulnerability, (issue_status, message, remediation) in zip(ADVISORY.vulnerabilities, issues, strict=True):
        atomic: AtomicResult = {"description": f"Verify {vulnerability.id}.", "result": issue_status, "messages": [message]}
        if remediation is not None:
            atomic["remediation"] = remediation
        atomic_results.append(atomic)
    return {
        "result": status,
        "messages": [message for _, message, _ in issues],
        "remediations": list(dict.fromkeys(remediation for _, _, remediation in issues if remediation is not None)),
        "atomic_results": atomic_results,
    }


_DATA: AntaUnitTestData = {
    (SA158, "failure-both-issues"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [GNPSI_VULNERABLE, GNPSI_VULNERABLE, TRACE_ENABLED, GNPSI_VULNERABLE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "gNPSI exposed authentication mode is enabled", SOFTWARE_REMEDIATION),
                (AntaTestStatus.FAILURE, "gNPSI EosRpcAuth trace is enabled", LOGGING_REMEDIATION),
            ),
        ),
    },
    (SA158, "success-safe-authentication-and-tracing"): {
        "version": None,
        "eos_data": [GNPSI_SAFE, GNPSI_SAFE, "", GNPSI_SAFE],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, "gNPSI exposed authentication mode is disabled", None),
                (AntaTestStatus.SUCCESS, "gNPSI EosRpcAuth trace is disabled", None),
            ),
        ),
    },
    (SA158, "mitigated-safe-authentication-with-tracing"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [GNPSI_SAFE, GNPSI_SAFE, TRACE_ENABLED, GNPSI_SAFE],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, "gNPSI exposed authentication mode is disabled", None),
                (AntaTestStatus.SUCCESS, "gNPSI mutual TLS with only x509-spiffe authentication is effective", LOGGING_REMEDIATION),
            ),
        ),
    },
    (SA158, "success-gnpsi-disabled"): {
        "version": None,
        "eos_data": [GNPSI_DISABLED, GNPSI_DISABLED, TRACE_ENABLED, GNPSI_DISABLED],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "is disabled", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
    (SA158, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [GNPSI_VULNERABLE, GNPSI_VULNERABLE, TRACE_ENABLED, GNPSI_VULNERABLE],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "outside the affected releases", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
    (SA158, "error-malformed-gnpsi-output"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{}, {}, "unexpected", {}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (AntaTestStatus.ERROR, "gNPSI transport state", None),
                (AntaTestStatus.ERROR, "gNPSI transport state", None),
            ),
        ),
    },
}
