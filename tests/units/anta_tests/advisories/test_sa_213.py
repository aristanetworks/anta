# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 213."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import cast

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp import BgpSrTeActivationFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import ConfigurationState, FactProblemKind, FactsBase, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_213 import ADVISORY, AFFECTED_VERSION_MATRIX, SA213, _assess_sa213
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.bgp_captures import BGP_CONFIG, route_summary

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 34, 1, suffix="F")).available(SOURCE)
SR_TE = BgpSrTeActivationFact(ConfigurationState.CONFIGURED, ("ipv4 sr-te",)).available(SOURCE)
NO_SR_TE_FACT = BgpSrTeActivationFact(ConfigurationState.NOT_CONFIGURED).available(SOURCE)
MULTI = MultiAgentRoutingFact(FeatureState.ENABLED).available(SOURCE)
RIBD = MultiAgentRoutingFact(FeatureState.DISABLED).available(SOURCE)
MISSING_VERSION = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
MISSING_SR_TE = BgpSrTeActivationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
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
        ("4.21.9M", False),
        ("4.22.0F", False),
        ("4.22.0.1F", False),
        ("4.22.1F", True),
        ("4.22.12M", True),
        ("4.23.0F", True),
        ("4.31.2F", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.1F", True),
        ("4.34.8M", True),
        ("4.34.9M", False),
        ("4.35.6M", True),
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
    """End-of-support trains start at 4.22.1F; 4.32 is fully affected; named fixes close their own trains."""
    actual = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert actual.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_assessment_and_remediation() -> None:
    """SR-TE activation with multi-agent routing on affected software requires the source's software fix."""
    result = _assess_sa213(VERSION, SR_TE, MULTI)
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == "CVE-2026-121286"
    assert result.conditions == (SR_TE, MULTI)
    assert result.remediation == remediation(EOSVersion(4, 34, 1, suffix="F"))


def test_decisive_absence_ignores_unrelated_errors() -> None:
    """No SR-TE activation, ribd in both models, or fixed software each close exposure alone."""
    assert _assess_sa213(MISSING_VERSION, NO_SR_TE_FACT, MISSING_MODEL) == NotAffectedResult(vulnerability_id="CVE-2026-121286", decisive=(NO_SR_TE_FACT,))
    assert _assess_sa213(MISSING_VERSION, MISSING_SR_TE, RIBD) == NotAffectedResult(vulnerability_id="CVE-2026-121286", decisive=(RIBD,))
    fixed = _assess_sa213(EosVersionFact.from_version(EOSVersion(4, 33, 11, suffix="M")).available(SOURCE), MISSING_SR_TE, MISSING_MODEL)
    assert isinstance(fixed, NotAffectedResult)


def test_all_required_unavailable_inputs_are_retained() -> None:
    """A missing version does not hide configuration or model failures."""
    result = _assess_sa213(MISSING_VERSION, MISSING_SR_TE, MISSING_MODEL)
    assert isinstance(result, ErrorResult)
    assert result.problems == (MISSING_VERSION, MISSING_SR_TE, MISSING_MODEL)
    assert _assess_sa213(VERSION, SR_TE, MISSING_MODEL) == ErrorResult(vulnerability_id="CVE-2026-121286", problems=(MISSING_MODEL,))


def test_metadata_and_collection() -> None:
    """Collection uses the BGP running configuration and both routing models, not session summaries."""
    assert ADVISORY.sa_number == "0213"
    assert ADVISORY.title == "Security Advisory 0213"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert [(item.id, item.severity) for item in ADVISORY.vulnerabilities] == [("CVE-2026-121286", _AdvisoryVulnerabilitySeverity.MEDIUM)]
    facts = cast("type[FactsBase]", SA213.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "sr_te", "multi_agent")
    instance = SA213(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt, command.revision) for command in instance.instance_commands] == [
        ("show running-config | section router bgp", "text", 1),
        ("show ip route summary", "json", 3),
    ]


IPV4_ONLY = BGP_CONFIG.replace("   address-family ipv6 sr-te\n      neighbor 2001:db8::1 activate\n", "")
IPV6_ONLY = BGP_CONFIG.replace("   address-family ipv4 sr-te\n      neighbor 192.0.2.3 activate\n", "")
NO_SR_TE = IPV4_ONLY.replace("   address-family ipv4 sr-te\n      neighbor 192.0.2.3 activate\n", "")
AFFECTED_MESSAGE = (
    "The device is affected because EOS version '{}' is affected, the BGP SR-TE address family configuration is configured, "
    "and the routing protocol model multi-agent is enabled."
)
NOT_CONFIGURED_MESSAGE = "The device is not affected because the BGP SR-TE address family configuration is not configured."
expected = partial(build_expected_advisory_result, "CVE-2026-121286")

_DATA: AntaUnitTestData = {
    (SA213, "affected-captured-ipv4-and-ipv6-sr-te"): {
        "version": build_eos_version("4.34.1F"),
        "eos_data": [BGP_CONFIG, route_summary()],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.34.1F"), remediation(EOSVersion(4, 34, 1, suffix="F"))),
    },
    (SA213, "affected-ipv4-sr-te-only-ribd-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [IPV4_ONLY, route_summary("ribd", "multi-agent")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"))),
    },
    (SA213, "affected-ipv6-sr-te-only-multi-agent-configured-pending-reload"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [IPV6_ONLY, route_summary("multi-agent", "ribd")],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format("4.31.2F"), remediation(EOSVersion(4, 31, 2, suffix="F"))),
    },
    (SA213, "not-affected-path-selection-only"): {
        "version": build_eos_version("4.34.1F"),
        "eos_data": [NO_SR_TE, route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA213, "not-affected-no-bgp"): {
        "version": build_eos_version("4.34.1F"),
        "eos_data": ["", route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, NOT_CONFIGURED_MESSAGE, None),
    },
    (SA213, "not-affected-ribd"): {
        "version": build_eos_version("4.31.2F"),
        "eos_data": [BGP_CONFIG, route_summary("ribd", "ribd")],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the routing protocol model multi-agent is disabled.", None),
    },
    (SA213, "not-affected-fixed-release"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [BGP_CONFIG, route_summary()],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA213, "error-invalid-routing-model-with-activated-sr-te"): {
        "version": build_eos_version("4.34.1F"),
        "eos_data": [BGP_CONFIG, "unexpected"],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the multi-agent routing protocol model because the 'show ip route summary' output is invalid.",
            None,
        ),
    },
}
