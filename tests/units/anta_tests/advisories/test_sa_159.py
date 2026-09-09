# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 159."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_159 import ADVISORY, AFFECTED_VERSION_MATRIX, SA159, _assess_sa159
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def test_sa159_assessment_contract() -> None:
    """Treat default IGMP snooping exposure as a version-only assessment."""
    assert isinstance(_assess_sa159(eos_version_fact("4.36.1F")), AffectedResult)
    assert isinstance(_assess_sa159(eos_version_fact("4.36.2F")), NotAffectedResult)
    assert isinstance(_assess_sa159(unavailable_fact(EosVersionFact)), ErrorResult)


def test_sa159_version_boundaries() -> None:
    """Cover every source-defined affected and first-fixed EOS boundary."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
        ),
    )


DATA: AntaUnitTestData = {
    (SA159, "failure-affected-version"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [],
        "expected": expected_result(AntaTestStatus.FAILURE, "EOS version '4.36.1F' is affected", REMEDIATION),
    },
    (SA159, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA159, "error-missing-version"): {
        "version": None,
        "eos_data": [],
        "expected": expected_result(AntaTestStatus.ERROR, "EOS version", None),
    },
}
