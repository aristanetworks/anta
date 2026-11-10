# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 223."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Literal, TypeAlias
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.bfd import SbfdInitiatorRoundTripDelayFact, SbfdReflectorProxyFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactProblemKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_223 import (
    ADVISORY,
    CVE_121294_AFFECTED_VERSIONS,
    CVE_121295_AFFECTED_VERSIONS,
    SA223,
    _assess_reflector_proxy,
    _assess_round_trip_delay,
)
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.fact_builders import SOURCE

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
REFLECTOR_PROXY_ID = "CVE-2026-121294"
ROUND_TRIP_DELAY_ID = "CVE-2026-121295"
COMMAND = "show running-config section sbfd"


def expected_remediation(version: str) -> RemediationPlan:
    """Build the advisory's software resolution independently of the implementation constants."""
    return RemediationPlan(
        ChangeSoftwareVersion(
            software=SoftwareTarget.EOS,
            current_version=parse_eos_version(version).unwrap(),
            destination=KnownFixedReleases(
                (
                    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
                    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
                    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
                    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
                    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
                )
            ),
        )
    )


# Version boundaries spelled out from the advisory's affected-release lists and its fixed-release list.
SHARED_BOUNDARIES = [
    ("4.36.0F", True),
    ("4.36.2F", True),
    ("4.36.2.1F", True),
    ("4.36.3M", False),
    ("4.35.0F", True),
    ("4.35.6M", True),
    ("4.35.6.1M", True),
    ("4.35.7M", False),
    ("4.34.0F", True),
    ("4.34.8M", True),
    ("4.34.8.1M", True),
    ("4.34.9M", False),
    ("4.33.0F", True),
    ("4.33.10M", True),
    ("4.33.10.1M", True),
    ("4.33.11M", False),
    ("4.32.0F", True),
    ("4.32.99M", True),
    ("4.31.0F", True),
    ("4.31.99M", True),
    ("4.30.0F", True),
    ("4.29.0F", True),
    ("4.29.99M", True),
    ("4.27.99M", False),
    ("4.22.0F", False),
    ("4.37.0F", False),
    ("4.37.1F", False),
    ("4.38.0F", False),
    ("5.0.0F", False),
]


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        *SHARED_BOUNDARIES,
        ("4.28.0F", False),
        ("4.28.1F", False),
        ("4.28.1.1F", False),
        ("4.28.2F", True),
        ("4.28.2.1F", True),
        ("4.28.10M", True),
    ],
)
def test_reflector_proxy_version_boundaries(version: str, affected: bool) -> None:
    """CVE-2026-121294 starts at 4.28.2F and is fixed in each listed release."""
    status = evaluate_version(parse_eos_version(version).unwrap(), CVE_121294_AFFECTED_VERSIONS).affected_status
    assert status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        *SHARED_BOUNDARIES,
        ("4.28.0F", False),
        ("4.28.2F", False),
        ("4.28.10M", False),
    ],
)
def test_round_trip_delay_version_boundaries(version: str, affected: bool) -> None:
    """CVE-2026-121295 starts with the 4.29 train and is fixed in each listed release."""
    status = evaluate_version(parse_eos_version(version).unwrap(), CVE_121295_AFFECTED_VERSIONS).affected_status
    assert status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def version_fact(version: str | None) -> Fact[EosVersionFact]:
    """Build an EOS version fact, or an unavailable one when no version is given."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


def platform_fact(family: PlatformFamily | None, platform_type: PlatformType = PlatformType.FIXED) -> Fact[PlatformIdentityFact]:
    """Build a platform identity fact for one family, or an unavailable one."""
    if family is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return PlatformIdentityFact(model=family.value, type=platform_type, modules=(), platform_families=frozenset({family})).available(SOURCE)


def assess_both(
    version: str | None = "4.35.6M",
    family: PlatformFamily | None = PlatformFamily.SERIES_7280_R3,
    *,
    proxy: FeatureState | FactProblemKind = FeatureState.ENABLED,
    round_trip: FeatureState | FactProblemKind = FeatureState.ENABLED,
) -> tuple[VulnerabilityResult, VulnerabilityResult]:
    """Run both pure assessments from independently constructed facts."""
    proxy_fact = (
        SbfdReflectorProxyFact.unavailable(proxy, SOURCE) if isinstance(proxy, FactProblemKind) else SbfdReflectorProxyFact(proxy, "10.0.0.1").available(SOURCE)
    )
    delay_fact = (
        SbfdInitiatorRoundTripDelayFact.unavailable(round_trip, SOURCE)
        if isinstance(round_trip, FactProblemKind)
        else SbfdInitiatorRoundTripDelayFact(round_trip).available(SOURCE)
    )
    version_value, platform_value = version_fact(version), platform_fact(family)
    return (
        _assess_reflector_proxy(version_value, platform_value, proxy_fact),
        _assess_round_trip_delay(version_value, platform_value, delay_fact),
    )


AFFECTED_FAMILIES = [
    PlatformFamily.SERIES_710,
    PlatformFamily.SERIES_720_D,
    PlatformFamily.SERIES_720_XP,
    PlatformFamily.SERIES_722_XPM,
    PlatformFamily.SERIES_750_X,
    PlatformFamily.SERIES_7010_TX,
    PlatformFamily.SERIES_7020_R,
    PlatformFamily.SERIES_7020_R4,
    PlatformFamily.SERIES_7280_R,
    PlatformFamily.SERIES_7280_R2,
    PlatformFamily.SERIES_7280_R3,
    PlatformFamily.SERIES_7280_R4,
    PlatformFamily.SERIES_7500_R,
    PlatformFamily.SERIES_7500_R2,
    PlatformFamily.SERIES_7500_R3,
    PlatformFamily.SERIES_7800_R3,
    PlatformFamily.SERIES_7800_R4,
    PlatformFamily.SERIES_7700_R4,
    PlatformFamily.CLOUDEOS,
    PlatformFamily.CEOS_LAB,
    PlatformFamily.VEOS_LAB,
    PlatformFamily.CVX,
]
EXPLICITLY_UNAFFECTED_FAMILIES = [
    PlatformFamily.AWE_5000,
    PlatformFamily.AWE_7200_R,
    PlatformFamily.SERIES_7300_X,
    PlatformFamily.SERIES_7300_X3,
    PlatformFamily.SERIES_7320_X,
    PlatformFamily.SERIES_7358_X4,
    PlatformFamily.SERIES_7368_X4,
    PlatformFamily.SERIES_7388_X5,
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
]


@pytest.mark.parametrize("family", AFFECTED_FAMILIES)
def test_affected_platform_families(family: PlatformFamily) -> None:
    """Every listed affected platform family is in scope for both vulnerabilities."""
    proxy, round_trip = assess_both(family=family)
    for result, vulnerability_id in ((proxy, REFLECTOR_PROXY_ID), (round_trip, ROUND_TRIP_DELAY_ID)):
        assert isinstance(result, AffectedResult)
        assert result.vulnerability_id == vulnerability_id
        assert result.remediation == expected_remediation("4.35.6M")


@pytest.mark.parametrize("family", EXPLICITLY_UNAFFECTED_FAMILIES)
def test_explicitly_unaffected_platform_families(family: PlatformFamily) -> None:
    """Every listed unaffected EOS family is excluded even when the EOS version is unavailable."""
    for result in assess_both(None, family):
        assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize(
    ("model", "affected"),
    [
        ("DCS-7280SR2-48YC6-F", True),
        ("DCS-7280SR3-48YC8", True),
        ("CCS-720DT-48S", True),
        ("CCS-720XP-48ZC2", True),
        ("DCS-7010TX-48", True),
        ("DCS-7020SR-24C2", True),
        ("DCS-DL-7700R4C-38PE", True),
        ("vEOS-lab", True),
        ("cEOSLab", True),
        ("CloudEOS", True),
        ("vEOS", True),
        ("DCS-7050SX3-48YC8", False),
        ("DCS-7060XE7", False),
        ("DCS-7170-64C", False),
        ("DCS-7130-48LBE", False),
        ("AWE-5310", False),
        ("AWE-7230R", False),
    ],
)
def test_resolved_platform_models(model: str, affected: bool) -> None:
    """Resolved model identities follow the advisory's affected and unaffected platform lists."""
    platform = build_eos_platform(model)
    assert platform is not None
    identity = PlatformIdentityFact.from_identity(platform).available(SOURCE)
    result = _assess_reflector_proxy(
        EosVersionFact.from_version(EOSVersion(4, 34, 8, suffix="M")).available(SOURCE),
        identity,
        SbfdReflectorProxyFact(FeatureState.ENABLED, "10.0.0.1").available(SOURCE),
    )
    assert isinstance(result, AffectedResult if affected else NotAffectedResult)


@pytest.mark.parametrize(
    ("modules", "affected"),
    [
        ({"Linecard3": {"modelName": "7500R3-36CQ-LC"}, "Supervisor1": {"modelName": "DCS-7500-SUP2"}}, True),
        ({"Linecard3": {"modelName": "7800R3-36P-LC"}, "Supervisor1": {"modelName": "DCS-7800-SUP1A"}}, True),
        ({"Linecard3": {"modelName": "7500E-36Q-LC"}, "Supervisor1": {"modelName": "DCS-7500-SUP2"}}, False),
    ],
)
def test_modular_platform_identity(modules: dict[str, dict[str, str]], affected: bool) -> None:
    """Modular platform scope is established from installed line cards."""
    model = "DCS-7808-CH" if "7800R3" in str(modules) else "DCS-7504N"
    platform = build_eos_platform(model, {"modules": modules})
    assert platform is not None
    result = _assess_round_trip_delay(
        EosVersionFact.from_version(EOSVersion(4, 34, 8, suffix="M")).available(SOURCE),
        PlatformIdentityFact.from_identity(platform).available(SOURCE),
        SbfdInitiatorRoundTripDelayFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(result, AffectedResult if affected else NotAffectedResult)


def test_chassis_without_modules_is_error() -> None:
    """A chassis without module identity cannot prove platform scope."""
    platform = build_eos_platform("DCS-7504N")
    assert platform is not None
    result = _assess_reflector_proxy(
        EosVersionFact.from_version(EOSVersion(4, 34, 8, suffix="M")).available(SOURCE),
        PlatformIdentityFact.from_identity(platform).available(SOURCE),
        SbfdReflectorProxyFact(FeatureState.ENABLED, "10.0.0.1").available(SOURCE),
    )
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (PlatformIdentityFact,)


def test_unknown_platform_is_error() -> None:
    """An unrecognized model cannot prove a source exclusion."""
    platform = build_eos_platform("DCS-UNRECOGNIZED")
    assert platform is not None
    result = _assess_round_trip_delay(
        EosVersionFact.from_version(EOSVersion(4, 34, 8, suffix="M")).available(SOURCE),
        PlatformIdentityFact.from_identity(platform).available(SOURCE),
        SbfdInitiatorRoundTripDelayFact(FeatureState.ENABLED).available(SOURCE),
    )
    assert isinstance(result, ErrorResult)


def test_vulnerabilities_are_independent() -> None:
    """Each S-BFD setting only exposes its own vulnerability."""
    proxy, round_trip = assess_both(proxy=FeatureState.ENABLED, round_trip=FeatureState.DISABLED)
    assert isinstance(proxy, AffectedResult)
    assert isinstance(round_trip, NotAffectedResult)
    proxy, round_trip = assess_both(proxy=FeatureState.DISABLED, round_trip=FeatureState.ENABLED)
    assert isinstance(proxy, NotAffectedResult)
    assert isinstance(round_trip, AffectedResult)


def test_distinct_introduction_boundaries() -> None:
    """4.28.2F is affected only through the reflector proxy."""
    proxy, round_trip = assess_both("4.28.2F")
    assert isinstance(proxy, AffectedResult)
    assert proxy.remediation == expected_remediation("4.28.2F")
    assert isinstance(round_trip, NotAffectedResult)


def test_absent_setting_bypasses_unavailable_scope() -> None:
    """A disabled S-BFD setting is decisive even when version and platform are unavailable."""
    for result in assess_both(None, None, proxy=FeatureState.DISABLED, round_trip=FeatureState.DISABLED):
        assert isinstance(result, NotAffectedResult)


def test_fixed_release_bypasses_unavailable_inputs() -> None:
    """A fixed release decides safety independently of unavailable platform and configuration."""
    for result in assess_both("4.35.7M", None, proxy=FactProblemKind.MALFORMED, round_trip=FactProblemKind.MALFORMED):
        assert isinstance(result, NotAffectedResult)


def test_all_required_problems_are_preserved() -> None:
    """Unavailable scope and exposure evidence are reported together for each vulnerability."""
    proxy, round_trip = assess_both(None, None, proxy=FactProblemKind.MALFORMED, round_trip=FactProblemKind.MISSING)
    assert isinstance(proxy, ErrorResult)
    assert tuple(problem.definition for problem in proxy.problems) == (EosVersionFact, PlatformIdentityFact, SbfdReflectorProxyFact)
    assert isinstance(round_trip, ErrorResult)
    assert tuple(problem.definition for problem in round_trip.problems) == (EosVersionFact, PlatformIdentityFact, SbfdInitiatorRoundTripDelayFact)


def test_metadata_uses_allocated_identity() -> None:
    """Metadata uses the allocated SA number, both CVEs, and the approved batch date."""
    assert ADVISORY.sa_number == "0223"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25045-security-advisory-0223"
    assert tuple((v.id, v.severity) for v in ADVISORY.vulnerabilities) == (
        (REFLECTOR_PROXY_ID, _AdvisoryVulnerabilitySeverity.MEDIUM),
        (ROUND_TRIP_DELAY_ID, _AdvisoryVulnerabilitySeverity.HIGH),
    )


def expected(
    status: Status,
    proxy: tuple[Status, str, RemediationPlan | None],
    round_trip: tuple[Status, str, RemediationPlan | None],
    remediations: list[RemediationPlan],
) -> UnitTestResult:
    """Build parent and per-vulnerability atomic expectations."""
    atomic_results: list[AtomicResult] = []
    for vulnerability_id, (atomic_status, message, remediation) in ((REFLECTOR_PROXY_ID, proxy), (ROUND_TRIP_DELAY_ID, round_trip)):
        atomic: AtomicResult = {"description": f"Verify {vulnerability_id}.", "result": atomic_status, "messages": [message]}
        if remediation is not None:
            atomic["remediation"] = remediation
        atomic_results.append(atomic)
    return {"result": status, "messages": [proxy[1], round_trip[1]], "remediations": remediations, "atomic_results": atomic_results}


def affected_message(version: str, platform: str, setting: str) -> str:
    """Return the rendered affected finding."""
    return f"The device is affected because EOS version '{version}' is affected, platform '{platform}' is within the affected platform scope, and {setting}."


PROXY_ENABLED = "the S-BFD reflector proxy is enabled"
DELAY_ENABLED = "the S-BFD initiator round-trip delay measurement is enabled"
PROXY_DISABLED = "The device is not affected because the S-BFD reflector proxy is disabled."
DELAY_DISABLED = "The device is not affected because the S-BFD initiator round-trip delay measurement is disabled."
PROXY_INVALID = f"The test could not determine the S-BFD reflector proxy state because the '{COMMAND}' output is invalid."
DELAY_INVALID = f"The test could not determine the S-BFD initiator round-trip delay measurement state because the '{COMMAND}' output is invalid."
VERSION_MISSING = "The test could not determine the EOS version because it is missing from device metadata."
PLATFORM_MISSING = "The test could not determine the platform identity because it is missing from device metadata."

# Captured from vEOS-lab 4.36.2F and DCS-7280SR2-48YC6 4.32.0F with configured S-BFD and no S-BFD sessions.
NO_SBFD = ""
REFLECTOR = "router bfd\n   sbfd\n      reflector local-discriminator 10.0.0.1\n"
REFLECTOR_PROXY = "router bfd\n   sbfd\n      reflector local-discriminator 10.0.0.1 proxy\n"
ROUND_TRIP_DELAY = "router bfd\n   sbfd\n      initiator measurement delay round-trip\n"
BOTH = "router bfd\n   sbfd\n      initiator measurement delay round-trip\n      reflector local-discriminator 10.0.0.1 proxy\n"
ROUND_TRIP_DELAY_WITH_TE_POLICY = (
    "router bfd\n"
    "   sbfd\n"
    "      initiator measurement delay round-trip\n"
    "router traffic-engineering\n"
    "   segment-routing\n"
    "      policy endpoint 10.1.1.1 color 100\n"
    "         sbfd remote-discriminator 10.0.0.9\n"
)
PROXY_WITH_UNKNOWN_MEASUREMENT = "router bfd\n   sbfd\n      initiator measurement delay one-way\n      reflector local-discriminator 10.0.0.1 proxy\n"
ROUND_TRIP_DELAY_WITH_MALFORMED_REFLECTOR = "router bfd\n   sbfd\n      initiator measurement delay round-trip\n      reflector local-discriminator 10.0.0.1 relay\n"
F, S, E = AntaTestStatus.FAILURE, AntaTestStatus.SUCCESS, AntaTestStatus.ERROR

_DATA: AntaUnitTestData = {
    (SA223, "affected-both-veos-4-36-2f"): {
        "version": build_eos_version("4.36.2F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [BOTH, BOTH],
        "expected": expected(
            F,
            (F, affected_message("4.36.2F", "vEOS-lab", PROXY_ENABLED), expected_remediation("4.36.2F")),
            (F, affected_message("4.36.2F", "vEOS-lab", DELAY_ENABLED), expected_remediation("4.36.2F")),
            [expected_remediation("4.36.2F")],
        ),
    },
    (SA223, "affected-proxy-only-7280sr2-4-32-0f"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform("DCS-7280SR2-48YC6-F"),
        "eos_data": [REFLECTOR_PROXY, REFLECTOR_PROXY],
        "expected": expected(
            F,
            (F, affected_message("4.32.0F", "DCS-7280SR2-48YC6-F", PROXY_ENABLED), expected_remediation("4.32.0F")),
            (S, DELAY_DISABLED, None),
            [expected_remediation("4.32.0F")],
        ),
    },
    (SA223, "affected-round-trip-only-with-te-policy-7280sr2"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform("DCS-7280SR2-48YC6-F"),
        "eos_data": [ROUND_TRIP_DELAY_WITH_TE_POLICY, ROUND_TRIP_DELAY_WITH_TE_POLICY],
        "expected": expected(
            F,
            (S, PROXY_DISABLED, None),
            (F, affected_message("4.32.0F", "DCS-7280SR2-48YC6-F", DELAY_ENABLED), expected_remediation("4.32.0F")),
            [expected_remediation("4.32.0F")],
        ),
    },
    (SA223, "affected-proxy-only-4-28-2f-floor"): {
        "version": build_eos_version("4.28.2F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [BOTH, BOTH],
        "expected": expected(
            F,
            (F, affected_message("4.28.2F", "vEOS-lab", PROXY_ENABLED), expected_remediation("4.28.2F")),
            (S, "The device is not affected because EOS version '4.28.2F' is outside the affected releases.", None),
            [expected_remediation("4.28.2F")],
        ),
    },
    (SA223, "not-affected-reflector-without-proxy-missing-scope"): {
        "version": None,
        "platform": None,
        "eos_data": [REFLECTOR, REFLECTOR],
        "expected": expected(S, (S, PROXY_DISABLED, None), (S, DELAY_DISABLED, None), []),
    },
    (SA223, "not-affected-no-sbfd"): {
        "version": build_eos_version("4.34.0F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [NO_SBFD, NO_SBFD],
        "expected": expected(S, (S, PROXY_DISABLED, None), (S, DELAY_DISABLED, None), []),
    },
    (SA223, "not-affected-fixed-4-37-0f"): {
        "version": build_eos_version("4.37.0F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [BOTH, BOTH],
        "expected": expected(
            S,
            (S, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
            (S, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
            [],
        ),
    },
    (SA223, "not-affected-excluded-platform-missing-version"): {
        "version": None,
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [BOTH, BOTH],
        "expected": expected(
            S,
            (S, "The device is not affected because platform 'DCS-7050SX3-48YC8' is outside the affected platform scope.", None),
            (S, "The device is not affected because platform 'DCS-7050SX3-48YC8' is outside the affected platform scope.", None),
            [],
        ),
    },
    (SA223, "error-missing-scope"): {
        "version": None,
        "platform": None,
        "eos_data": [BOTH, BOTH],
        "expected": expected(E, (E, f"{VERSION_MISSING} {PLATFORM_MISSING}", None), (E, f"{VERSION_MISSING} {PLATFORM_MISSING}", None), []),
    },
    (SA223, "error-uninterpretable-configuration"): {
        "version": build_eos_version("4.36.2F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [BOTH + BOTH, BOTH + BOTH],
        "expected": expected(E, (E, PROXY_INVALID, None), (E, DELAY_INVALID, None), []),
    },
    (SA223, "affected-proxy-with-unrecognized-measurement"): {
        "version": build_eos_version("4.36.2F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [PROXY_WITH_UNKNOWN_MEASUREMENT, PROXY_WITH_UNKNOWN_MEASUREMENT],
        "expected": expected(
            E,
            (F, affected_message("4.36.2F", "vEOS-lab", PROXY_ENABLED), expected_remediation("4.36.2F")),
            (E, DELAY_INVALID, None),
            [expected_remediation("4.36.2F")],
        ),
    },
    (SA223, "affected-round-trip-with-malformed-reflector"): {
        "version": build_eos_version("4.36.2F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [ROUND_TRIP_DELAY_WITH_MALFORMED_REFLECTOR, ROUND_TRIP_DELAY_WITH_MALFORMED_REFLECTOR],
        "expected": expected(
            E,
            (E, PROXY_INVALID, None),
            (F, affected_message("4.36.2F", "vEOS-lab", DELAY_ENABLED), expected_remediation("4.36.2F")),
            [expected_remediation("4.36.2F")],
        ),
    },
}


async def run_with_command_errors(version: str, errors: list[str]) -> list[_AdvisoryAtomicTestResult]:
    """Run SA223 through the ANTA wrapper with every S-BFD command collection failing with the given errors."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version(version)
    device.platform = build_eos_platform("vEOS-lab")
    await device.refresh()
    instance = SA223(device=device, eos_data=["", ""])
    assert len(instance.instance_commands) == 2
    for command in instance.instance_commands:
        command.output = None
        command.errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    atomics = [atomic for atomic in instance.result.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult)]
    assert len(atomics) == len(instance.result.atomic_results) == 2
    assert [atomic.vulnerability_ids for atomic in atomics] == [(REFLECTOR_PROXY_ID,), (ROUND_TRIP_DELAY_ID,)]
    return atomics


@pytest.mark.parametrize(
    ("errors", "reason"),
    [
        pytest.param(["This command is not supported on this hardware platform"], "is not supported", id="unsupported"),
        pytest.param(["permission denied"], "could not be collected", id="collection-failed"),
    ],
)
async def test_failed_sbfd_collection_is_structured_error(errors: list[str], reason: str) -> None:
    """Failed or unsupported collection on affected software is a per-vulnerability error attributed to the command."""
    proxy, round_trip = await run_with_command_errors("4.36.2F", errors)
    assert proxy.result is round_trip.result is AntaTestStatus.ERROR
    assert proxy.messages == [f"The test could not determine the S-BFD reflector proxy state because '{COMMAND}' {reason}."]
    assert round_trip.messages == [f"The test could not determine the S-BFD initiator round-trip delay measurement state because '{COMMAND}' {reason}."]
    assert proxy.remediation is round_trip.remediation is None


async def test_fixed_software_excludes_failed_sbfd_collection() -> None:
    """A failed S-BFD command cannot hide an independently fixed release."""
    for atomic in await run_with_command_errors("4.37.0F", ["permission denied"]):
        assert atomic.result is AntaTestStatus.SUCCESS
        assert atomic.messages == ["The device is not affected because EOS version '4.37.0F' is outside the affected releases."]
