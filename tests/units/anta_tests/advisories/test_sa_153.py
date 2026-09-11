# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 153."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    CollectedFact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
)
from anta._advisory.facts.tracing import (
    AaaPasswordTraceFact,
    AaaTacacsKeyTraceFact,
    ConfigAgentPrivateKeyTraceFact,
)
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, OperationalAction, RemediationPlan, Sequence, software_version_action
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_153 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    PASSWORD_ID,
    PRIVATE_KEY_ID,
    SA153,
    TACACS_KEY_ID,
    _assess_password,
    _assess_private_key,
    _assess_tacacs_key,
)
from tests.units.anta_tests import build_eos_version, test

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta._advisory.facts.models import CommandsFactDefinition
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
ProductionStatus: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
IssueExpectation: TypeAlias = tuple[ProductionStatus, str, RemediationPlan | None]
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
)
EXPECTED_CLEAN_LOGS = OperationalAction("Clean current and rotated agent logs if the affected trace levels were enabled.")
EXPECTED_REMEDIATION = RemediationPlan(
    Sequence((software_version_action(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F")), EXPECTED_CLEAN_LOGS))
)


def expected_result(status: ProductionStatus, issues: tuple[IssueExpectation, ...]) -> UnitTestResult:
    """Build parent and per-vulnerability expectations for one production case."""
    remediations: list[RemediationPlan] = []
    for _, _, remediation in issues:
        if remediation is not None and remediation not in remediations:
            remediations.append(remediation)
    atomic_results: list[AtomicResult] = []
    for vulnerability, (issue_status, message, remediation) in zip(ADVISORY.vulnerabilities, issues, strict=True):
        atomic_result: AtomicResult = {
            "description": f"Verify {vulnerability.id}.",
            "result": issue_status,
            "messages": [message],
        }
        if remediation is not None:
            atomic_result["remediation"] = remediation
        atomic_results.append(atomic_result)
    return {
        "result": status,
        "messages": [message for _, message, _ in issues],
        "remediations": remediations,
        "atomic_results": atomic_results,
    }


EOS_NOT_AFFECTED = "The device is not affected because EOS version '4.36.2F' is outside the affected releases"
EOS_VERSION_ERROR = "The test could not determine the EOS version because it is missing from device metadata"
PRIVATE_TRACE_AFFECTED = "The device is affected because EOS version '4.36.1F' is affected and the agent tracing risk for ConfigAgent private keys is enabled"
PASSWORD_TRACE_AFFECTED = "The device is affected because EOS version '4.36.1F' is affected and the agent tracing risk for Aaa user passwords is enabled"
TACACS_TRACE_AFFECTED = "The device is affected because EOS version '4.36.1F' is affected and the agent tracing risk for Aaa TACACS+ shared keys is enabled"
PRIVATE_TRACE_NOT_AFFECTED = "The device is not affected because the agent tracing risk for ConfigAgent private keys is disabled"
PASSWORD_TRACE_NOT_AFFECTED = "The device is not affected because the agent tracing risk for Aaa user passwords is disabled"
TACACS_TRACE_NOT_AFFECTED = "The device is not affected because the agent tracing risk for Aaa TACACS+ shared keys is disabled"


def eos_data(trace: str) -> list[dict[str, Any] | str]:
    """Supply shared trace output to each fact-owned command wrapper."""
    return [trace, trace, trace]


_DATA: AntaUnitTestData = {
    (SA153, "failure-all-risky-traces-enabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data("trace ConfigAgent setting MgmtSecuritySslCertKey/034\ntrace Aaa setting */0-7"),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, PRIVATE_TRACE_AFFECTED, EXPECTED_REMEDIATION),
                (AntaTestStatus.FAILURE, PASSWORD_TRACE_AFFECTED, EXPECTED_REMEDIATION),
                (AntaTestStatus.FAILURE, TACACS_TRACE_AFFECTED, EXPECTED_REMEDIATION),
            ),
        ),
    },
    (SA153, "success-all-risky-traces-disabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, PRIVATE_TRACE_NOT_AFFECTED, None),
                (AntaTestStatus.SUCCESS, PASSWORD_TRACE_NOT_AFFECTED, None),
                (AntaTestStatus.SUCCESS, TACACS_TRACE_NOT_AFFECTED, None),
            ),
        ),
    },
    (SA153, "failure-one-risky-trace-enabled"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data("trace Aaa setting Py*/0-5"),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, PRIVATE_TRACE_NOT_AFFECTED, None),
                (AntaTestStatus.FAILURE, PASSWORD_TRACE_AFFECTED, EXPECTED_REMEDIATION),
                (AntaTestStatus.SUCCESS, TACACS_TRACE_NOT_AFFECTED, None),
            ),
        ),
    },
    (SA153, "success-fixed-version-short-circuits-evidence"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data("trace ConfigAgent setting MgmtSecuritySslCertKey/034\ntrace Aaa setting */0-7"),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, EOS_NOT_AFFECTED, None),
                (AntaTestStatus.SUCCESS, EOS_NOT_AFFECTED, None),
                (AntaTestStatus.SUCCESS, EOS_NOT_AFFECTED, None),
            ),
        ),
    },
    (SA153, "error-missing-version"): {
        "version": None,
        "eos_data": eos_data("trace ConfigAgent setting MgmtSecuritySslCertKey/034\ntrace Aaa setting */0-7"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (AntaTestStatus.ERROR, EOS_VERSION_ERROR, None),
                (AntaTestStatus.ERROR, EOS_VERSION_ERROR, None),
                (AntaTestStatus.ERROR, EOS_VERSION_ERROR, None),
            ),
        ),
    },
    (SA153, "error-malformed-trace-state"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data("trace ConfigAgent enable MgmtSecuritySslCertKey levels 4\ntrace Aaa enable PyServer levels 4"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (
                    AntaTestStatus.ERROR,
                    "The test could not determine the ConfigAgent private-key trace state because the 'show running-config section trace' output is invalid",
                    None,
                ),
                (
                    AntaTestStatus.ERROR,
                    "The test could not determine the Aaa user-password trace state because the 'show running-config section trace' output is invalid",
                    None,
                ),
                (
                    AntaTestStatus.ERROR,
                    "The test could not determine the Aaa TACACS+ shared-key trace state because the 'show running-config section trace' output is invalid",
                    None,
                ),
            ),
        ),
    },
}


def version_fact(version: str | None) -> CollectedFact[EOSVersion]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def trace_fact(definition: type[CommandsFactDefinition[FeatureValue]], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build one agent-trace fact."""
    return definition.available(FeatureValue(SubFeature(FeatureName.AGENT_TRACING, "test trace"), state), SOURCE)


class TestSA153VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.1.99F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.4M", AffectedStatus.AFFECTED),
            ("4.35.5M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.99M", AffectedStatus.AFFECTED),
            ("4.33.99M", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA153Assessment(unittest.TestCase):
    """Validate shared semantics through every vulnerability wrapper."""

    ASSESSMENTS: tuple[
        tuple[
            Callable[[CollectedFact[EOSVersion], CollectedFact[FeatureValue]], object],
            str,
            type[CommandsFactDefinition[FeatureValue]],
        ],
        ...,
    ] = (
        (_assess_private_key, PRIVATE_KEY_ID, ConfigAgentPrivateKeyTraceFact),
        (_assess_password, PASSWORD_ID, AaaPasswordTraceFact),
        (_assess_tacacs_key, TACACS_KEY_ID, AaaTacacsKeyTraceFact),
    )

    def test_risky_trace_is_affected(self) -> None:
        for assess, vulnerability_id, trace_definition in self.ASSESSMENTS:
            with self.subTest(vulnerability_id=vulnerability_id):
                finding = assess(
                    version_fact("4.36.1F"),
                    trace_fact(trace_definition, FeatureState.ENABLED),
                )
                assert isinstance(finding, AffectedResult)
                assert finding.vulnerability_id == vulnerability_id
                assert finding.context[0].relation is VersionRelation.AFFECTED

    def test_disabled_trace_is_not_affected(self) -> None:
        for assess, vulnerability_id, trace_definition in self.ASSESSMENTS:
            with self.subTest(vulnerability_id=vulnerability_id):
                finding = assess(version_fact(None), trace_fact(trace_definition, FeatureState.DISABLED))
                assert isinstance(finding, NotAffectedResult)
                assert finding.vulnerability_id == vulnerability_id

    def test_fixed_version_short_circuits_evidence(self) -> None:
        finding = _assess_password(
            version_fact("4.36.2F"),
            AaaPasswordTraceFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)

    def test_unavailable_required_trace_state_is_error(self) -> None:
        finding = _assess_password(
            version_fact("4.36.1F"),
            AaaPasswordTraceFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, ErrorResult)
        assert finding.problems[0].definition is AaaPasswordTraceFact
