# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 153."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind
from anta._advisory.findings.models import AffectedEosRelease, AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import AllOf, ConditionalAction, FixedRelease, OperationalAction, RemediationPlan, software_version_action
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_153 import ADVISORY, AFFECTED_VERSION_MATRIX, SA153, _assess_sa153_issue
from tests.units.anta_tests import (
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
ProductionStatus: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
EXPECTED_CLEAN_LOGS = ConditionalAction(
    "the affected trace levels were enabled",
    OperationalAction("Clean up current and rotated agent logs as described in the advisory."),
)
EXPECTED_REMEDIATION = RemediationPlan(
    AllOf((software_version_action(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F")), EXPECTED_CLEAN_LOGS))
)


def expected_result(status: ProductionStatus, message: str, remediation: RemediationPlan | None) -> UnitTestResult:
    """Build parent and per-vulnerability expectations when every issue shares one outcome."""
    atomic_results: list[AtomicResult] = []
    for vulnerability in ADVISORY.vulnerabilities:
        atomic_result: AtomicResult = {
            "description": f"Verify {vulnerability.id}.",
            "result": status,
            "messages": [message],
        }
        if remediation is not None:
            atomic_result["remediation"] = remediation
        atomic_results.append(atomic_result)
    return {
        "result": status,
        "messages": [message] * len(ADVISORY.vulnerabilities),
        "remediations": [remediation] if remediation is not None else [],
        "atomic_results": atomic_results,
    }


_DATA: AntaUnitTestData = {
    (SA153, "failure-affected-version"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA153, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.36.2F' is outside the affected releases",
            None,
        ),
    },
    (SA153, "error-missing-version"): {
        "version": None,
        "eos_data": [],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
}


def version_fact(version: str | None) -> Fact[EosVersionFact]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.from_version(parsed).available(SOURCE)


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
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA153Assessment(unittest.TestCase):
    """Validate shared semantics for every vulnerability."""

    def test_affected_release_is_affected(self) -> None:
        for vulnerability in ADVISORY.vulnerabilities:
            with self.subTest(vulnerability_id=vulnerability.id):
                finding = _assess_sa153_issue(vulnerability.id, version_fact("4.36.1F"))
                assert isinstance(finding, AffectedResult)
                assert finding.vulnerability_id == vulnerability.id
                assert isinstance(finding.conditions[0], AffectedEosRelease)
                assert finding.remediation == EXPECTED_REMEDIATION

    def test_fixed_release_is_not_affected(self) -> None:
        finding = _assess_sa153_issue(ADVISORY.vulnerabilities[0].id, version_fact("4.36.2F"))

        assert isinstance(finding, NotAffectedResult)

    def test_missing_version_is_error(self) -> None:
        finding = _assess_sa153_issue(ADVISORY.vulnerabilities[0].id, version_fact(None))

        assert isinstance(finding, ErrorResult)
        assert finding.problems[0].definition is EosVersionFact
