# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 207."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bgp import BgpInstanceFact, MultiAgentRoutingFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactsBase, FactSource, FactSourceKind, FeatureState
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_207 import ADVISORY, AFFECTED_VERSION_MATRIX, SA207, _assess_sa207
from tests.units.anta_tests import (
    AntaUnitTestData,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from typing import Any

SOURCE = FactSource("unit-test", FactSourceKind.DEVICE_METADATA)
VERSION = EosVersionFact.from_version(EOSVersion(4, 35, 6, suffix="M")).available(SOURCE)
BGP = BgpInstanceFact(FeatureState.ENABLED).available(SOURCE)
MULTI = MultiAgentRoutingFact(FeatureState.ENABLED).available(SOURCE)
EXPECTED_FIXED_RELEASES = KnownFixedReleases(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    )
)
REMEDIATION = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 35, 6, suffix="M"), EXPECTED_FIXED_RELEASES))


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("3.9.1", False),
        ("4.0.1F", True),
        ("4.24.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.10M", True),
        ("4.33.10.1M", True),
        ("4.33.11M", False),
        ("4.34.0F", True),
        ("4.34.8M", True),
        ("4.34.8.1M", True),
        ("4.34.9M", False),
        ("4.35.0F", True),
        ("4.35.6M", True),
        ("4.35.6.1M", True),
        ("4.35.7M", False),
        ("4.36.0F", True),
        ("4.36.2F", True),
        ("4.36.2.1F", True),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_source_software_boundaries(version: str, affected: bool) -> None:
    """First fixed releases close their own train, including fixed-only 4.37."""
    actual = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert actual.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_affected_assessment_and_complete_remediation() -> None:
    """Established software and feature exposure requires the source's software fix."""
    affected = _assess_sa207(VERSION, BGP, MULTI)
    assert isinstance(affected, AffectedResult)
    assert affected.vulnerability_id == "CVE-2026-120982"
    assert affected.remediation == REMEDIATION


@pytest.mark.parametrize("decisive", ["version", "bgp", "multi_agent"])
def test_decisive_absence_ignores_unrelated_errors(decisive: str) -> None:
    """Each independent exclusion retains its evidence despite unrelated failures."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    bgp = BgpInstanceFact.unavailable(FactProblemKind.MISSING, SOURCE)
    model = MultiAgentRoutingFact.unavailable(FactProblemKind.MISSING, SOURCE)
    if decisive == "version":
        version = EosVersionFact.from_version(EOSVersion(4, 37, 0, suffix="F")).available(SOURCE)
    elif decisive == "bgp":
        bgp = BgpInstanceFact(FeatureState.DISABLED).available(SOURCE)
    else:
        model = MultiAgentRoutingFact(FeatureState.DISABLED).available(SOURCE)
    result = _assess_sa207(version, bgp, model)
    assert isinstance(result, NotAffectedResult)
    if decisive == "version":
        assert isinstance(result.decisive[0], EosReleaseAssessment)
        assert result.decisive[0].fact is version
    else:
        assert result.decisive == (bgp if decisive == "bgp" else model,)


def test_all_required_unavailable_inputs_are_retained() -> None:
    """Missing version does not hide required instance/model failures."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    missing_bgp = BgpInstanceFact.unavailable(FactProblemKind.MISSING, SOURCE)
    missing_model = MultiAgentRoutingFact.unavailable(FactProblemKind.MISSING, SOURCE)
    result = _assess_sa207(missing_version, missing_bgp, missing_model)
    assert isinstance(result, ErrorResult)
    assert result.problems == (missing_version, missing_bgp, missing_model)


def test_all_eos_scope_and_metadata() -> None:
    """All EOS includes virtual/new families without collecting platform identity."""
    assert ADVISORY.sa_number == "0207"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.vulnerabilities[0].id == "CVE-2026-120982"
    facts = cast("type[FactsBase]", SA207.__dict__["Facts"])
    assert "platform" not in facts.definitions()
    assert tuple(facts.definitions()) == ("version", "bgp", "multi_agent")


INSTANCE = "BGP instance information for VRF default\nBGP Local AS:   123, Router ID: 1.1.1.1\nTotal peers:              0\n"
MODEL = {"protoModelStatus": {"configuredProtoModel": "multi-agent", "operatingProtoModel": "multi-agent"}, "vrfs": {"default": {"connected": 1}}}
expected = partial(build_expected_advisory_result, "CVE-2026-120982")

_DATA: AntaUnitTestData = {
    (SA207, "not-affected-no-router-id-or-shutdown"): {
        "version": None,
        "eos_data": ["", {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP feature is disabled.", None),
    },
    (SA207, "not-affected-ribd"): {
        "version": None,
        "eos_data": [INSTANCE, {"protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": "ribd"}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the routing protocol model multi-agent is disabled.", None),
    },
    (SA207, "not-affected-fixed-missing-inputs"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [{}, {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA207, "error-missing-routing-model"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [INSTANCE, {}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the multi-agent routing protocol model because the 'show ip route summary' output is incomplete.",
            None,
        ),
    },
    (SA207, "error-malformed-bgp-inventory"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [{}, MODEL],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP instance presence because the 'show bgp instance vrf all' output is invalid.",
            None,
        ),
    },
}


_DATA[(SA207, "not-affected-missing-router-id-newer-eos")] = {
    "version": None,
    "eos_data": ["BGP is disabled for VRF default (Missing Router ID)\n", {}],
    "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP feature is disabled.", None),
}
_DATA[(SA207, "affected-zero-peer-eos-4-31-0F")] = {
    "version": build_eos_version("4.31.0F"),
    "eos_data": [INSTANCE, MODEL],
    "expected": expected(
        AntaTestStatus.FAILURE,
        "The device is affected because EOS version '4.31.0F' is affected, the BGP feature is enabled, and the routing protocol model multi-agent is enabled.",
        RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 31, 0, suffix="F"), EXPECTED_FIXED_RELEASES)),
    ),
}


for _vrf in ("default", "RED"):
    _DATA[(SA207, f"affected-zero-peer-instance-{_vrf}")] = {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [INSTANCE.replace("VRF default", f"VRF {_vrf}"), MODEL],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected, the BGP feature is enabled, and the routing protocol model multi-agent is enabled.",
            REMEDIATION,
        ),
    }


for _configured, _operating in (("ribd", "multi-agent"), ("multi-agent", "ribd")):
    _DATA[(SA207, f"affected-pending-model-change-{_configured}-to-{_operating}")] = {
        "version": build_eos_version("4.31.10M"),
        "eos_data": [
            INSTANCE,
            {"protoModelStatus": {"configuredProtoModel": _configured, "operatingProtoModel": _operating}},
        ],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.31.10M' is affected, the BGP feature is enabled, and the routing protocol model multi-agent is enabled.",
            RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 31, 10, suffix="M"), EXPECTED_FIXED_RELEASES)),
        ),
    }


def test_collection_uses_bgp_instances_and_routing_model() -> None:
    """Collect instance inventory and routing model without neighbors or discard configuration."""
    instance = SA207(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt) for command in instance.instance_commands] == [
        ("show bgp instance vrf all", "text"),
        ("show ip route summary", "json"),
    ]


@pytest.mark.parametrize(
    ("errors", "status"),
    [
        (["BGP inactive"], AntaTestStatus.SUCCESS),
        (["% BGP inactive"], AntaTestStatus.SUCCESS),
        (["BGP inactive", "permission denied"], AntaTestStatus.ERROR),
    ],
)
async def test_inactive_bgp_command_result(errors: list[str], status: AntaTestStatus) -> None:
    """Handle inactive EOS responses through the real test wrapper on an affected release."""
    device = OfflineAntaDevice("unit-test")
    device.version = EOSVersion(4, 35, 6, suffix="M")
    await device.refresh()
    instance = cast("Any", SA207)(device, eos_data=["", MODEL])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()

    await instance.test()

    assert instance.result.result is status
    assert len(instance.result.atomic_results) == 1
    assert instance.result.atomic_results[0].result is status
    if status is AntaTestStatus.SUCCESS:
        assert "The device is not affected because the BGP feature is disabled." in instance.result.messages[0]
    else:
        assert "show bgp instance vrf all" in instance.result.messages[0]
