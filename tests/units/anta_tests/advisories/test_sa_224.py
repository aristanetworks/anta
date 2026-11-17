# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 224."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.ptp import PtpGlobalFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories import _ADVISORY_TESTS, get_catalog
from anta.tests.advisories.sa_224 import ADVISORY, AFFECTED_PLATFORM_FAMILIES, AFFECTED_VERSION_MATRIX, FIXED_RELEASES, SA224, _assess_sa224
from tests.units.anta_tests import (
    build_eos_platform,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
PTP_SOURCE = FactSource("show ptp", FactSourceKind.COMMAND)
PTP_ENABLED = {
    "ptpMode": "ptpBoundaryClock",
    "ptpProfile": "ptpDefaultProfile",
    "ptpClockSummary": {
        "clockIdentity": "00:1c:73:ff:ff:00:00:01",
        "gmClockIdentity": "00:1c:73:ff:ff:00:00:01",
        "numberOfSlavePorts": 0,
        "numberOfMasterPorts": 0,
        "offsetFromMaster": 0,
        "meanPathDelay": 0,
        "stepsRemoved": 0,
        "skew": 1.0,
    },
    "ptpIntfSummaries": {},
}
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 34, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
EXPECTED_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 34, 1, suffix="F"))
expected = partial(build_expected_advisory_result, "CVE-2026-121370")

_DATA: AntaUnitTestData = {
    (SA224, "affected-global-ptp-with-no-interfaces"): {
        "version": build_eos_version("4.34.1F"),
        "platform": build_eos_platform("CCS-758-CH-F"),
        "eos_data": [PTP_ENABLED],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.34.1F' is affected, platform 'CCS-758-CH-F' is within the affected platform scope, "
            "and the PTP feature is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA224, "not-affected-explicit-disabled"): {
        "version": None,
        "platform": None,
        "eos_data": [{"ptpMode": "ptpDisabled", "ptpIntfSummaries": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the PTP feature is disabled", None),
    },
    (SA224, "not-affected-omitted-disabled-mode"): {
        "version": None,
        "platform": None,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the PTP feature is disabled", None),
    },
    (SA224, "not-affected-fixed-release"): {
        "version": build_eos_version("4.34.2F"),
        "platform": None,
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.34.2F' is outside the affected releases", None),
    },
    (SA224, "not-affected-virtual-platform"): {
        "version": None,
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'cEOSLab' is outside the affected platform scope", None),
    },
    (SA224, "error-incomplete-json"): {
        "version": build_eos_version("4.34.1F"),
        "platform": build_eos_platform("CCS-758-CH-F"),
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the global PTP state because the 'show ptp' output is incomplete", None),
    },
    (SA224, "error-empty-explicit-mode"): {
        "version": build_eos_version("4.34.1F"),
        "platform": build_eos_platform("CCS-758-CH-F"),
        "eos_data": [{"ptpMode": "", "ptpIntfSummaries": {}}],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the global PTP state because the 'show ptp' output is invalid", None),
    },
    (SA224, "error-all-required-inputs-unavailable"): {
        "version": None,
        "platform": None,
        "eos_data": [{"ptpMode": True, "ptpIntfSummaries": {}}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the platform identity because it is missing from device metadata. "
            "The test could not determine the global PTP state because the 'show ptp' output is invalid.",
            None,
        ),
    },
}


@pytest.mark.parametrize(
    "mode",
    [
        "ptpBoundaryClock",
        "ptpOneStepBoundaryClock",
        "ptpEndToEndTransparentClock",
        "ptpPeerToPeerTransparentClock",
        "ptpOrdinaryMasterClock",
        "ptpGeneralized",
        "ptpOneStepEndToEndTransparentClock",
        "ptpOneStepPeerToPeerTransparentClock",
        "ptpFutureMode",
        "unknown",
    ],
)
async def test_non_disabled_ptp_modes_are_affected(device: AntaDevice, mode: str) -> None:
    """Every non-disabled mode exposes in-scope software/platforms, including new modes."""
    device.version = build_eos_version("4.34.1F")
    device.platform = build_eos_platform("CCS-758-CH-F")
    instance = SA224(device=device, eos_data=[{"ptpMode": mode, "ptpIntfSummaries": {}}])
    await instance.test()
    assert instance.result.result is AntaTestStatus.FAILURE
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-121370",)
    assert atomic.messages == [
        (
            "The device is affected because EOS version '4.34.1F' is affected, platform 'CCS-758-CH-F' is within the affected platform scope, "
            "and the PTP feature is enabled."
        ),
    ]
    assert atomic.remediation == EXPECTED_REMEDIATION


def platform_fact(model: str | None) -> Fact[PlatformIdentityFact]:
    """Build platform identity from the same metadata normalization as collection."""
    if model is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = build_eos_platform(model)
    assert platform is not None
    return PlatformIdentityFact.from_identity(platform).available(SOURCE)


def ptp_fact(state: FeatureState = FeatureState.ENABLED) -> Fact[PtpGlobalFact]:
    """Build one available global PTP fact."""
    return PtpGlobalFact(state).available(PTP_SOURCE)


def test_version_boundaries() -> None:
    """Encode introduction and every affected/fixed train independently."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.28.99M", AffectedStatus.NOT_AFFECTED),
            ("4.29.1F", AffectedStatus.NOT_AFFECTED),
            ("4.29.1.99F", AffectedStatus.NOT_AFFECTED),
            ("4.29.2F", AffectedStatus.AFFECTED),
            ("4.29.99M", AffectedStatus.AFFECTED),
            ("4.30.0F", AffectedStatus.AFFECTED),
            ("4.30.99M", AffectedStatus.AFFECTED),
            ("4.31.0F", AffectedStatus.AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.8.99M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.1F", AffectedStatus.AFFECTED),
            ("4.34.1.99F", AffectedStatus.AFFECTED),
            ("4.34.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("5.0.0F", AffectedStatus.NOT_AFFECTED),
        ),
    )


def test_platform_scope() -> None:
    """Retain the advisory's specific 750X restriction."""
    assert {PlatformFamily.SERIES_750_X} == AFFECTED_PLATFORM_FAMILIES


def test_fixed_releases() -> None:
    """Keep each named fixed train in remediation choices."""
    assert (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 34, 2, suffix="F")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ) == FIXED_RELEASES


def test_advisory_metadata() -> None:
    """Preserve the assigned advisory identity, CVE, and approved date."""
    assert ADVISORY.sa_number == "0224"
    assert ADVISORY.title == "Security Advisory 0224"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25046-security-advisory-0224"
    assert len(ADVISORY.vulnerabilities) == 1
    assert ADVISORY.vulnerabilities[0].id == "CVE-2026-121370"
    assert ADVISORY.vulnerabilities[0].severity is _AdvisoryVulnerabilitySeverity.HIGH


def test_global_ptp_exposure() -> None:
    """Assess global enablement independently of interface counts or workaround state."""
    finding = _assess_sa224(eos_version_fact("4.34.1F"), platform_fact("CCS-758-CH-F"), ptp_fact())
    assert isinstance(finding, AffectedResult)
    assert finding.vulnerability_id == "CVE-2026-121370"
    assert finding.remediation == EXPECTED_REMEDIATION


def test_disabled_ptp_short_circuits_missing_scope() -> None:
    """Explicit disabled PTP decisively excludes exposure without scope metadata."""
    disabled = ptp_fact(FeatureState.DISABLED)
    finding = _assess_sa224(EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE), platform_fact(None), disabled)
    assert isinstance(finding, NotAffectedResult)
    assert finding.decisive == (disabled,)


def test_fixed_software_short_circuits_other_unavailable_facts() -> None:
    """Fixed software independently excludes exposure."""
    finding = _assess_sa224(
        eos_version_fact("4.33.9M"),
        platform_fact(None),
        PtpGlobalFact.unavailable(FactProblemKind.COLLECTION_FAILED, PTP_SOURCE),
    )
    assert isinstance(finding, NotAffectedResult)


@pytest.mark.parametrize("missing", [(0,), (1,), (2,), (0, 1), (0, 2), (1, 2), (0, 1, 2)])
def test_all_required_unavailable_facts_are_retained(missing: tuple[int, ...]) -> None:
    """Retain every applicable unavailable input on the evaluated path."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE) if 0 in missing else eos_version_fact("4.34.1F")
    platform = platform_fact(None if 1 in missing else "CCS-758-CH-F")
    ptp = PtpGlobalFact.unavailable(FactProblemKind.UNSUPPORTED, PTP_SOURCE) if 2 in missing else ptp_fact()
    finding = _assess_sa224(version, platform, ptp)
    assert isinstance(finding, ErrorResult)
    expected_definitions = (EosVersionFact, PlatformIdentityFact, PtpGlobalFact)
    assert tuple(problem.definition for problem in finding.problems) == tuple(expected_definitions[i] for i in missing)


@pytest.mark.parametrize("model", ["CCS-755-CH", "CCS-758-CH-F"])
def test_affected_chassis_identity(model: str) -> None:
    """Both 750X chassis identities establish affected family scope."""
    finding = _assess_sa224(eos_version_fact("4.34.1F"), platform_fact(model), ptp_fact())
    assert isinstance(finding, AffectedResult)


@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_710,
        PlatformFamily.SERIES_720_D,
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_722_XPM,
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
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R3,
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
def test_excluded_platform_families(family: PlatformFamily) -> None:
    """Every explicitly excluded EOS family independently excludes exposure."""
    platform = PlatformIdentityFact(model=family.value, type=PlatformType.FIXED, modules=(), platform_families=frozenset({family})).available(SOURCE)
    finding = _assess_sa224(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        platform,
        PtpGlobalFact.unavailable(FactProblemKind.UNSUPPORTED, PTP_SOURCE),
    )
    assert isinstance(finding, NotAffectedResult)


@pytest.mark.parametrize("model", ["DCS-UNRECOGNIZED", "DCS-7508N"])
def test_incomplete_platform_identity_is_error(model: str) -> None:
    """Unknown or incomplete modular identity cannot prove exclusion."""
    finding = _assess_sa224(eos_version_fact("4.34.1F"), platform_fact(model), ptp_fact())
    assert isinstance(finding, ErrorResult)
    assert finding.problems[0].definition is PlatformIdentityFact


@pytest.mark.parametrize("case_name", [name for _, name in _DATA])
async def test_exact_atomic_results(device: AntaDevice, case_name: str) -> None:
    """Check complete finding text, remediation, and the single CVE attribution."""
    case = _DATA[(SA224, case_name)]
    device.version = case.get("version")
    device.platform = case.get("platform")
    instance = SA224(device=device, eos_data=case["eos_data"])
    await instance.test()
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-121370",)
    assert atomic.result is case["expected"]["result"]
    expected_result = case["expected"]
    assert "messages" in expected_result
    message = expected_result["messages"][0]
    assert atomic.messages == [message if message.endswith(".") else f"{message}."]
    plans = expected_result.get("remediations", [])
    assert atomic.remediation == (plans[0] if plans else None)


@pytest.mark.parametrize(
    ("errors", "message"),
    [
        (["This command is not supported on this hardware platform"], "The test could not determine the global PTP state because 'show ptp' is not supported."),
        (["permission denied"], "The test could not determine the global PTP state because 'show ptp' could not be collected."),
    ],
)
async def test_failed_ptp_collection_is_structured_error(errors: list[str], message: str) -> None:
    """Unsupported and failed required collection preserve atomic command attribution."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.34.1F")
    device.platform = build_eos_platform("CCS-758-CH-F")
    await device.refresh()
    instance = SA224(device=device, eos_data=[{}])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.ERROR
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-121370",)
    assert atomic.messages == [message]
    assert atomic.remediation is None


async def test_fixed_software_excludes_failed_ptp_collection() -> None:
    """A failed optional command cannot hide an independently fixed release."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.36.3M")
    await device.refresh()
    instance = SA224(device=device, eos_data=[{}])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = ["permission denied"]
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.SUCCESS
    assert len(instance.result.atomic_results) == 1
    assert instance.result.atomic_results[0].messages == [
        "The device is not affected because EOS version '4.36.3M' is outside the affected releases.",
    ]


def test_catalog_registration_and_command_contract() -> None:
    """Expose the class in the default catalog with exactly its global PTP command."""
    assert SA224 in _ADVISORY_TESTS
    assert any(definition.test is SA224 for definition in get_catalog().tests)
    assert len(SA224.commands) == 1
    command = SA224.commands[0]
    assert isinstance(command, AntaCommand)
    assert command.command == "show ptp"
    assert command.revision == 2
