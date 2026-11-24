# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 214."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import TYPE_CHECKING, Literal
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.bgp import BgpInstanceFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.vpls import BgpVplsSignalingInstanceFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _AdvisoryAtomicTestResult, _get_atomic_vulnerability_ids
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_214 import (
    ADVISORY,
    AFFECTED_PLATFORM_FAMILIES,
    AFFECTED_VERSION_MATRIX,
    SA214,
    _assess_cve_2026_120980,
    _assess_cve_2026_120981,
)
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Generic ANTA test collector.
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact
    from anta._advisory.remediation import RemediationPlan
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

ASSESSMENTS = (_assess_cve_2026_120980, _assess_cve_2026_120981)
IDS = ("CVE-2026-120980", "CVE-2026-120981")
SIGNALING_PRESENT = BgpVplsSignalingInstanceFact(FeatureState.ENABLED).available(SOURCE)
SIGNALING_ABSENT = BgpVplsSignalingInstanceFact(FeatureState.DISABLED).available(SOURCE)
BGP_ENABLED = BgpInstanceFact(FeatureState.ENABLED).available(SOURCE)
BGP_DISABLED = BgpInstanceFact(FeatureState.DISABLED).available(SOURCE)
BGP_OUTPUT = "BGP instance information for VRF default\nBGP Local AS: 65214, Router ID: 192.0.2.214\nTotal peers: 0\n  Established peers: 0"
LOCAL_ONLY = {
    "instances": {
        "CUSTOMER": {
            "groups": {"MESH": {"rd": "192.0.2.35:3942", "importRts": [844270311313254], "exportRts": [844270311313254], "vplsVeIdLocal": 35, "vplsVeIdsRemote": {}}}
        }
    }
}
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 6, suffix="M"),
)
AFFECTED_MESSAGE = (
    "The device is affected because EOS version '4.35.6M' is affected, platform 'DCS-7280CR3-32P4' is within the affected platform scope, "
    "the BGP feature is enabled, and the BGP VPLS signaling is enabled."
)


def platform_fact(model: str, modules: dict | None = None) -> Fact[PlatformIdentityFact]:
    """Build normalized identity including modular component evidence."""
    platform = build_eos_platform(model, modules)
    assert platform is not None
    return PlatformIdentityFact.from_identity(platform).available(SOURCE)


def test_advisory_metadata() -> None:
    """Use the allocated advisory identity/date and preserve both source CVEs."""
    assert ADVISORY.sa_number == "0214"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.title == "Security Advisory 0214"
    assert tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities) == IDS


def test_source_version_boundaries() -> None:
    """Encode introduction, each last affected patch, and every first fixed release independently."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.32.99M", AffectedStatus.NOT_AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.AFFECTED),
            ("4.33.10.1M", AffectedStatus.AFFECTED),
            ("4.33.11M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.AFFECTED),
            ("4.34.9M", AffectedStatus.NOT_AFFECTED),
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("3.35.1F", AffectedStatus.NOT_AFFECTED),
        ),
    )


def test_source_platform_families() -> None:
    """The source restricts both vulnerabilities to exactly the three R3 families."""
    assert {PlatformFamily.SERIES_7280_R3, PlatformFamily.SERIES_7500_R3, PlatformFamily.SERIES_7800_R3} == AFFECTED_PLATFORM_FAMILIES


@pytest.mark.parametrize("assess", ASSESSMENTS)
@pytest.mark.parametrize(
    ("model", "modules", "affected"),
    [
        ("DCS-7280CR3-32P4", None, True),
        ("DCS-7508", {"modules": {"3": {"modelName": "DCS-7500R3-36CQ-LC"}}}, True),
        ("DCS-7808-CH", {"modules": {"3": {"modelName": "7800R3A-36D-LC"}}}, True),
        ("DCS-7508", {"modules": {"3": {"modelName": "DCS-7500R2-36CQ-LC"}}}, False),
        ("DCS-7808-CH", {"modules": {"3": {"modelName": "7800R4-36D-LC"}}}, False),
        ("DCS-7280CR2-60", None, False),
        ("cEOSLab", None, False),
        ("vEOS-lab", None, False),
        ("CloudEOS", None, False),
        ("DCS-7050CX3-32S", None, False),
    ],
)
def test_platform_paths(assess, model: str, modules: dict | None, affected: bool) -> None:  # noqa: ANN001
    """R3 line cards establish modular scope, while explicitly unaffected families remain excluded."""
    finding = assess(eos_version_fact("4.35.6M"), platform_fact(model, modules), BGP_ENABLED, SIGNALING_PRESENT)
    assert isinstance(finding, AffectedResult if affected else NotAffectedResult)


@pytest.mark.parametrize("assess", ASSESSMENTS)
@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7010_TX,
        PlatformFamily.SERIES_7020_R,
        PlatformFamily.SERIES_7020_R4,
        PlatformFamily.SERIES_7130,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7800_R4,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.AWE_5000,
        PlatformFamily.AWE_7200_R,
        PlatformFamily.ZTX_7200,
        PlatformFamily.CLOUDEOS,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CVX,
    ],
)
def test_explicit_source_platform_exclusions(assess, family: PlatformFamily) -> None:  # noqa: ANN001
    """Independently enumerate every source-excluded family supported by the identity model."""
    identity = PlatformIdentityFact(model=family.value, type=PlatformType.FIXED, modules=(), platform_families=frozenset({family})).available(SOURCE)
    assert isinstance(assess(eos_version_fact("4.35.6M"), identity, BGP_ENABLED, SIGNALING_PRESENT), NotAffectedResult)


@pytest.mark.parametrize("assess", ASSESSMENTS)
def test_pure_assessment_results(assess) -> None:  # noqa: ANN001
    """Exercise affected, decisive absence, and aggregation of every required unavailable input."""
    missing_version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    missing_platform = PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    missing_bgp = BgpInstanceFact.unavailable(FactProblemKind.MISSING, SOURCE)
    missing_vpls = BgpVplsSignalingInstanceFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
    affected = assess(eos_version_fact("4.35.6M"), platform_fact("DCS-7280CR3-32P4"), BGP_ENABLED, SIGNALING_PRESENT)
    assert isinstance(affected, AffectedResult)
    assert affected.remediation == EXPECTED_REMEDIATION
    assert isinstance(assess(missing_version, missing_platform, missing_bgp, SIGNALING_ABSENT), NotAffectedResult)
    assert isinstance(assess(missing_version, missing_platform, BGP_DISABLED, missing_vpls), NotAffectedResult)
    assert isinstance(assess(eos_version_fact("4.35.7M"), missing_platform, missing_bgp, missing_vpls), NotAffectedResult)
    assert isinstance(assess(missing_version, platform_fact("cEOSLab"), missing_bgp, missing_vpls), NotAffectedResult)
    finding = assess(missing_version, missing_platform, missing_bgp, missing_vpls)
    assert isinstance(finding, ErrorResult)
    assert tuple(problem.definition for problem in finding.problems) == (EosVersionFact, PlatformIdentityFact, BgpInstanceFact, BgpVplsSignalingInstanceFact)
    assert isinstance(assess(eos_version_fact("4.35.6M"), platform_fact("DCS-7508"), BGP_ENABLED, SIGNALING_PRESENT), ErrorResult)
    assert isinstance(assess(eos_version_fact("4.35.6M"), platform_fact("DCS-UNRECOGNIZED"), BGP_ENABLED, SIGNALING_PRESENT), ErrorResult)
    assert isinstance(assess(eos_version_fact("4.35.6M"), platform_fact("DCS-7280CR3-32P4"), missing_bgp, SIGNALING_PRESENT), ErrorResult)


def expected(
    status: Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED],
    message: str,
    remediation: RemediationPlan | None = None,
) -> UnitTestResult:
    """Build independent atomic expectations for both source CVEs."""
    atomic_results: list[AtomicResult] = []
    for vulnerability_id in IDS:
        atomic_result: AtomicResult = {
            "description": f"Verify {vulnerability_id}.",
            "result": status,
            "messages": [message],
        }
        if remediation:
            atomic_result["remediation"] = remediation
        atomic_results.append(atomic_result)
    return {
        "result": status,
        "messages": [f"Verify {vulnerability_id}. - {message}" for vulnerability_id in IDS],
        "remediations": [remediation] if remediation else [],
        "atomic_results": atomic_results,
    }


_DATA: AntaUnitTestData = {
    (SA214, "affected-local-groups-without-peers"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": [BGP_OUTPUT, LOCAL_ONLY],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    },
    (SA214, "affected-any-local-instance"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": [BGP_OUTPUT, {"instances": {"CUSTOMER": {}}}],
        "expected": expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE, EXPECTED_REMEDIATION),
    },
    (SA214, "empty-signaling-snapshot-excludes-exposure"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": [BGP_OUTPUT, {"instances": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP VPLS signaling is disabled."),
    },
    (SA214, "empty-signaling-ignores-unavailable-identity-and-bgp"): {
        "version": None,
        "platform": None,
        "eos_data": ["unrecognized BGP output", {"instances": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP VPLS signaling is disabled."),
    },
    (SA214, "shutdown-bgp-excludes-populated-signaling"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": ["BGP is disabled for VRF default", LOCAL_ONLY],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP feature is disabled."),
    },
    (SA214, "absent-bgp-ignores-missing-identity-and-signaling"): {
        "version": None,
        "platform": None,
        "eos_data": ["", {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BGP feature is disabled."),
    },
    (SA214, "fixed-release-ignores-malformed-vpls"): {
        "version": build_eos_version("4.35.7M"),
        "platform": None,
        "eos_data": ["unrecognized BGP output", {}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.7M' is outside the affected releases."),
    },
    (SA214, "error-missing-local-container"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": [BGP_OUTPUT, {}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP VPLS signaling instance presence because the 'show bgp vpls signaling' output is incomplete.",
        ),
    },
    (SA214, "error-malformed-instance-container"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280CR3-32P4"),
        "eos_data": [BGP_OUTPUT, {"instances": []}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BGP VPLS signaling instance presence because the 'show bgp vpls signaling' output is invalid.",
        ),
    },
}


@pytest.mark.parametrize("case", _DATA.values())
def test_exact_class_output_and_vulnerability_attribution(case: dict) -> None:
    """Verify exact rendered findings, source errors, remediation, and CVE associations using the real class."""
    device = OfflineAntaDevice("sa214")
    device.version = case["version"]
    device.platform = case["platform"]
    instance = SA214(device, eos_data=case["eos_data"])
    asyncio.run(instance.test())
    assert instance.result.result is case["expected"]["result"]
    assert instance.result.messages == case["expected"]["messages"]
    assert tuple(_get_atomic_vulnerability_ids(result) for result in instance.result.atomic_results) == (
        ("CVE-2026-120980",),
        ("CVE-2026-120981",),
    )
    assert len(instance.result.atomic_results) == 2
    for result, expected_atomic in zip(instance.result.atomic_results, case["expected"]["atomic_results"], strict=True):
        assert isinstance(result, _AdvisoryAtomicTestResult)
        assert result.messages == expected_atomic["messages"]
        assert result.remediation == expected_atomic.get("remediation")


@pytest.mark.parametrize("failed_command", [0, 1])
async def test_fixed_software_excludes_failed_collection(failed_command: int) -> None:
    """A failed optional command cannot hide an independently fixed release."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.7M")
    await device.refresh()
    instance = SA214(device=device, eos_data=[BGP_OUTPUT, LOCAL_ONLY])
    instance.instance_commands[failed_command].output = None
    instance.instance_commands[failed_command].errors = ["permission denied"]
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.SUCCESS
    assert len(instance.result.atomic_results) == 2
    for result in instance.result.atomic_results:
        assert result.messages == ["The device is not affected because EOS version '4.35.7M' is outside the affected releases."]


@pytest.mark.parametrize("failed_command", [0, 1])
async def test_required_collection_failure_is_atomic_error(failed_command: int) -> None:
    """Required collection failures keep their command source and CVE association."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280CR3-32P4")
    await device.refresh()
    instance = SA214(device=device, eos_data=[BGP_OUTPUT, LOCAL_ONLY])
    instance.instance_commands[failed_command].output = None
    instance.instance_commands[failed_command].errors = ["permission denied"]
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.ERROR
    assert tuple(_get_atomic_vulnerability_ids(result) for result in instance.result.atomic_results) == (
        ("CVE-2026-120980",),
        ("CVE-2026-120981",),
    )
    command = ("show bgp instance vrf all", "show bgp vpls signaling")[failed_command]
    label = ("BGP instance presence", "BGP VPLS signaling instance presence")[failed_command]
    for result in instance.result.atomic_results:
        assert result.messages == [f"The test could not determine the {label} because '{command}' could not be collected."]


@pytest.mark.parametrize("reverse", [False, True])
async def test_reported_instance_survives_malformed_sibling(reverse: bool) -> None:
    """Exercise ADR0004 through command parsing and both atomic assessments."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280CR3-32P4")
    entries = [("GOOD", {}), ("BROKEN", [])]
    instance = SA214(device, eos_data=[BGP_OUTPUT, {"instances": dict(reversed(entries) if reverse else entries)}])
    await instance.test()
    assert instance.result.result is AntaTestStatus.FAILURE
    assert len(instance.result.atomic_results) == 2
    for result in instance.result.atomic_results:
        assert isinstance(result, _AdvisoryAtomicTestResult)
        assert result.messages == [AFFECTED_MESSAGE]
        assert result.remediation == EXPECTED_REMEDIATION


@pytest.mark.parametrize("errors", [["BGP inactive"], ["% BGP inactive"]])
async def test_exact_inactive_bgp_excludes_failed_signaling(errors: list[str]) -> None:
    """The shared BGP contract handles inactive agents independently of signaling."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280CR3-32P4")
    await device.refresh()
    instance = SA214(device, eos_data=["", {}])
    for command in instance.instance_commands:
        command.output = None
        command.errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.SUCCESS
    assert len(instance.result.atomic_results) == 2
    for result in instance.result.atomic_results:
        assert result.messages == ["The device is not affected because the BGP feature is disabled."]


@pytest.mark.parametrize("errors", [["permission denied"], ["BGP inactive", "permission denied"], ["BGP inactive during collection failure"]])
async def test_other_bgp_errors_do_not_exclude_exposure(errors: list[str]) -> None:
    """Neither substring matches nor mixed failures may be treated as disablement."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280CR3-32P4")
    await device.refresh()
    instance = SA214(device, eos_data=["", LOCAL_ONLY])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.ERROR
    for result in instance.result.atomic_results:
        assert result.messages == ["The test could not determine the BGP instance presence because 'show bgp instance vrf all' could not be collected."]


@pytest.mark.parametrize("failed_command", [0, 1])
async def test_independent_feature_absence_excludes_collection_failure(failed_command: int) -> None:
    """A valid negative observation remains decisive despite the other command failing."""
    device = OfflineAntaDevice("sa214")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280CR3-32P4")
    await device.refresh()
    instance = SA214(device, eos_data=["BGP is disabled for VRF default", {"instances": {}}])
    instance.instance_commands[failed_command].output = None
    instance.instance_commands[failed_command].errors = ["permission denied"]
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.SUCCESS
    feature = "BGP VPLS signaling" if failed_command == 0 else "BGP feature"
    for result in instance.result.atomic_results:
        assert result.messages == [f"The device is not affected because the {feature} is disabled."]
