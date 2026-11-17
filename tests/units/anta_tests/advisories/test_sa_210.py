# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 210."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import cast

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp import BgpPathSelectionActivationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, FactProblemKind, FactsBase, FactSource, FactSourceKind
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_210 import ADVISORY, AFFECTED_VERSION_MATRIX, SA210, _assess_sa210
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.bgp_captures import BGP_CONFIG

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 35, 0, suffix="F")).available(SOURCE)
ACTIVATED = BgpPathSelectionActivationFact(ConfigurationState.CONFIGURED, ("path-selection",)).available(SOURCE)
NOT_ACTIVATED = BgpPathSelectionActivationFact(ConfigurationState.NOT_CONFIGURED).available(SOURCE)
MISSING_VERSION = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
MISSING_ACTIVATION = BgpPathSelectionActivationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
FIXED = KnownFixedReleases(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    )
)


def remediation(version: EOSVersion) -> RemediationPlan:
    """Return the source's fixed-software resolution for one current release."""
    return RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, version, FIXED))


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("3.9.1", False),
        ("4.0.1F", True),
        ("4.21.0F", True),
        ("4.31.2F", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.8M", True),
        ("4.34.9M", False),
        ("4.35.0F", True),
        ("4.35.6M", True),
        ("4.35.7M", False),
        ("4.36.0.1F", True),
        ("4.36.2F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_software_boundaries(version: str, affected: bool) -> None:
    """4.32 and all older 4.x trains have no floor; named fixes close their own trains."""
    actual = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert actual.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_assessment_and_remediation() -> None:
    """Configured activation on affected software requires the source's software fix."""
    result = _assess_sa210(VERSION, ACTIVATED)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-121293"
    assert result.conditions == (ACTIVATED,)
    assert result.remediation == remediation(EOSVersion(4, 35, 0, suffix="F"))


def test_decisive_absence_ignores_unrelated_errors() -> None:
    """Absent activation or fixed software closes exposure alone."""
    assert _assess_sa210(MISSING_VERSION, NOT_ACTIVATED) == NotAffectedResult(vulnerability_id="CVE-2026-121293", decisive=(NOT_ACTIVATED,))
    fixed = _assess_sa210(EosVersionFact.from_version(EOSVersion(4, 37, 0, suffix="F")).available(SOURCE), MISSING_ACTIVATION)
    assert isinstance(fixed, NotAffectedResult)


def test_all_required_unavailable_inputs_are_retained() -> None:
    """A missing version does not hide unavailable configuration."""
    result = _assess_sa210(MISSING_VERSION, MISSING_ACTIVATION)
    assert isinstance(result, ErrorResult)
    assert result.problems == (MISSING_VERSION, MISSING_ACTIVATION)


def test_metadata_and_collection() -> None:
    """No routing model or operational summary is collected."""
    assert ADVISORY.sa_number == "0210"
    assert ADVISORY.title == "Security Advisory 0210"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert [(item.id, item.severity) for item in ADVISORY.vulnerabilities] == [("CVE-2026-121293", _AdvisoryVulnerabilitySeverity.MEDIUM)]
    facts = cast("type[FactsBase]", SA210.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "path_selection")
    instance = SA210(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt) for command in instance.instance_commands] == [("show running-config | section router bgp", "text")]


AFFECTED_MESSAGE = "The device is affected because EOS version '{}' is affected and the BGP path-selection address family configuration is configured."
NOT_CONFIGURED_MESSAGE = "The device is not affected because the BGP path-selection address family configuration is not configured."
NO_PATH_SELECTION = BGP_CONFIG.replace(
    "   address-family path-selection\n      neighbor PS activate\n      neighbor 192.0.2.1 activate\n      no neighbor 192.0.2.4 activate\n", ""
)
expected = partial(build_expected_advisory_result, "CVE-2026-121293")

_DATA: AntaUnitTestData = {
    (SA210, "affected-captured-configuration"): {
        "version": build_eos_version("4.35.0F"),
        "eos_data": [BGP_CONFIG],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.0F"), remediation(EOSVersion(4, 35, 0, suffix="F"))),
    },
    (SA210, "not-affected-sr-te-only"): {
        "version": build_eos_version("4.35.0F"),
        "eos_data": [NO_PATH_SELECTION],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA210, "not-affected-address-family-without-activation"): {
        "version": build_eos_version("4.35.0F"),
        "eos_data": [NO_PATH_SELECTION.replace("   vrf PROBE\n", "   address-family path-selection\n      no neighbor 192.0.2.4 activate\n   vrf PROBE\n")],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA210, "not-affected-no-bgp"): {
        "version": None,
        "eos_data": [""],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA210, "not-affected-fixed-release"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [BGP_CONFIG],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA210, "error-invalid-configuration-output"): {
        "version": build_eos_version("4.35.0F"),
        "eos_data": [{}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP path-selection address-family activation because "
            "the 'show running-config | section router bgp' output is invalid.",
            None,
        ),
    },
}
