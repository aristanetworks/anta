# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 208."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import cast

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp import BgpInstanceFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactsBase, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_208 import ADVISORY, AFFECTED_VERSION_MATRIX, SA208, _assess_sa208
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.bgp_captures import BGP_INSTANCE, route_summary

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 35, 3, suffix="F")).available(SOURCE)
BGP = BgpInstanceFact(FeatureState.ENABLED).available(SOURCE)
MULTI = MultiAgentRoutingFact(FeatureState.ENABLED).available(SOURCE)
RIBD = MultiAgentRoutingFact(FeatureState.DISABLED).available(SOURCE)
MISSING_VERSION = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
MISSING_BGP = BgpInstanceFact.unavailable(FactProblemKind.MISSING, SOURCE)
MISSING_MODEL = MultiAgentRoutingFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
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
        ("4.24.9M", False),
        ("4.25.0F", False),
        ("4.25.0.1F", False),
        ("4.25.1F", True),
        ("4.25.11M", True),
        ("4.26.0F", True),
        ("4.31.2F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.8M", True),
        ("4.34.8.1M", True),
        ("4.34.9M", False),
        ("4.35.6M", True),
        ("4.35.6.1M", True),
        ("4.35.7M", False),
        ("4.36.2F", True),
        ("4.36.2.1F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_software_boundaries(version: str, affected: bool) -> None:
    """End-of-support trains start at 4.25.1F; named fixes close their own trains."""
    actual = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert actual.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_assessment_and_remediation() -> None:
    """A BGP instance with multi-agent routing on affected software requires the source's software fix."""
    result = _assess_sa208(VERSION, BGP, MULTI)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-121289"
    assert result.conditions == (BGP, MULTI)
    assert result.remediation == remediation(EOSVersion(4, 35, 3, suffix="F"))


def test_decisive_absence_ignores_unrelated_errors() -> None:
    """Absent BGP, ribd in both models, or fixed software each close exposure alone."""
    no_bgp = BgpInstanceFact(FeatureState.DISABLED).available(SOURCE)
    assert _assess_sa208(MISSING_VERSION, no_bgp, MISSING_MODEL) == NotAffectedResult(vulnerability_id="CVE-2026-121289", decisive=(no_bgp,))
    assert _assess_sa208(MISSING_VERSION, MISSING_BGP, RIBD) == NotAffectedResult(vulnerability_id="CVE-2026-121289", decisive=(RIBD,))
    fixed = _assess_sa208(EosVersionFact.from_version(EOSVersion(4, 37, 0, suffix="F")).available(SOURCE), MISSING_BGP, MISSING_MODEL)
    assert isinstance(fixed, NotAffectedResult)


def test_all_required_unavailable_inputs_are_retained() -> None:
    """A missing version does not hide BGP or routing-model failures."""
    result = _assess_sa208(MISSING_VERSION, MISSING_BGP, MISSING_MODEL)
    assert isinstance(result, ErrorResult)
    assert result.problems == (MISSING_VERSION, MISSING_BGP, MISSING_MODEL)
    assert _assess_sa208(VERSION, BGP, MISSING_MODEL) == ErrorResult(vulnerability_id="CVE-2026-121289", problems=(MISSING_MODEL,))


def test_metadata_and_collection() -> None:
    """All EOS is in scope; collection uses the BGP instance inventory and both routing models."""
    assert ADVISORY.sa_number == "0208"
    assert ADVISORY.title == "Security Advisory 0208"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert [(item.id, item.severity) for item in ADVISORY.vulnerabilities] == [("CVE-2026-121289", _AdvisoryVulnerabilitySeverity.CRITICAL)]
    facts = cast("type[FactsBase]", SA208.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "bgp", "multi_agent")
    instance = SA208(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt) for command in instance.instance_commands] == [
        ("show bgp instance vrf all", "text"),
        ("show ip route summary", "json"),
    ]


AFFECTED_MESSAGE = "The device is affected because EOS version '{}' is affected, the BGP feature is enabled, and the routing protocol model multi-agent is enabled."
NO_BGP_MESSAGE = "The device is not affected because the BGP feature is disabled."
expected = partial(build_expected_advisory_result, "CVE-2026-121289")

_DATA: AntaUnitTestData = {
    (SA208, "affected-zero-peer-instance"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [BGP_INSTANCE, route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.36.2F"), remediation(EOSVersion(4, 36, 2, suffix="F"))),
    },
    (SA208, "affected-instance-in-named-vrf-only"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [BGP_INSTANCE.replace("VRF default", "VRF RED"), route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.35.3F"), remediation(EOSVersion(4, 35, 3, suffix="F"))),
    },
    (SA208, "affected-ribd-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [BGP_INSTANCE, route_summary("ribd", "multi-agent")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"))),
    },
    (SA208, "affected-multi-agent-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [BGP_INSTANCE, route_summary("multi-agent", "ribd")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"))),
    },
    (SA208, "not-affected-no-bgp"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": ["", route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NO_BGP_MESSAGE, None),
    },
    (SA208, "not-affected-missing-router-id"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": ["BGP is disabled for VRF default (Missing Router ID)\n", route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NO_BGP_MESSAGE, None),
    },
    (SA208, "not-affected-ribd"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [BGP_INSTANCE, route_summary("ribd", "ribd")],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the routing protocol model multi-agent is disabled.", None),
    },
    (SA208, "not-affected-fixed-release"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [BGP_INSTANCE, route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA208, "error-unknown-routing-model"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": [BGP_INSTANCE, route_summary("ribd", "unknown")],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the multi-agent routing protocol model because the 'show ip route summary' output is invalid.",
            None,
        ),
    },
    (SA208, "error-unrecognized-bgp-inventory"): {
        "version": build_eos_version("4.35.3F"),
        "eos_data": ["BGP is not active", route_summary()],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP instance presence because the 'show bgp instance vrf all' output is invalid.",
            None,
        ),
    },
}
