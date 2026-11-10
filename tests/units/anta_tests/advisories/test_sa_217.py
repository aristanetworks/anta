# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 217."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.aaa import Dot1xRadiusAccountingFact
from anta._advisory.facts.dot1x import (
    Dot1xAuthenticatorInterface,
    Dot1xAuthenticatorInterfacesFact,
    Dot1xDhcpProfilingFact,
    Dot1xDhcpProfilingOption,
    Dot1xPortControl,
    Dot1xSystemAuthControlFact,
)
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, Fact, FactProblemKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.remediation import ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, RemediationPlan, SoftwareTarget
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_217 import ADVISORY, AFFECTED_VERSION_MATRIX, SA217, _assess_sa217
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Parameterized advisory harness.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.dot1x_outputs import dot1x_all, dot1x_interface
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult

VULNERABILITY_ID = "CVE-2026-120977"
SOURCE_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)


def remediation_from(current: EOSVersion) -> RemediationPlan:
    """Build the expected software-version plan independently of the implementation."""
    return RemediationPlan(ChangeSoftwareVersion(software=SoftwareTarget.EOS, current_version=current, destination=KnownFixedReleases(SOURCE_FIXED_RELEASES)))


expected = partial(build_expected_advisory_result, VULNERABILITY_ID)


def test_source_version_boundaries() -> None:
    """Encode the 4.31.2F introduction, every first fixed release, and older or newer trains."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.30.9M", AffectedStatus.NOT_AFFECTED),
            ("4.31.0F", AffectedStatus.NOT_AFFECTED),
            ("4.31.1F", AffectedStatus.NOT_AFFECTED),
            ("4.31.1.1F", AffectedStatus.NOT_AFFECTED),
            ("4.31.2F", AffectedStatus.AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.9.1M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.5.1M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.2.1F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("5.0.0F", AffectedStatus.NOT_AFFECTED),
        ),
    )


def platform_fact(model: str) -> Fact[PlatformIdentityFact]:
    """Build normalized platform identity from one EOS model."""
    platform = build_eos_platform(model)
    return PlatformIdentityFact.from_identity(platform).available(SOURCE) if platform else PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)


def family_fact(family: PlatformFamily) -> Fact[PlatformIdentityFact]:
    """Build a fixed-system platform identity belonging to exactly one family."""
    return PlatformIdentityFact(model=family.value, type=PlatformType.FIXED, modules=(), platform_families=frozenset({family})).available(SOURCE)


def system_auth_control(state: FeatureState = FeatureState.ENABLED) -> Fact[Dot1xSystemAuthControlFact]:
    """Build global 802.1X system authentication control state."""
    return Dot1xSystemAuthControlFact(state).available(SOURCE)


def authenticators(*port_controls: Dot1xPortControl) -> Fact[Dot1xAuthenticatorInterfacesFact]:
    """Build authenticator interfaces with one interface per port-control mode."""
    interfaces = tuple(Dot1xAuthenticatorInterface(f"Ethernet{index}", mode) for index, mode in enumerate(port_controls, start=1))
    state = ConfigurationState.CONFIGURED if interfaces else ConfigurationState.NOT_CONFIGURED
    return Dot1xAuthenticatorInterfacesFact(state, interfaces).available(SOURCE)


def profiling(*options: Dot1xDhcpProfilingOption) -> Fact[Dot1xDhcpProfilingFact]:
    """Build configured DHCP profiling options."""
    state = ConfigurationState.CONFIGURED if options else ConfigurationState.NOT_CONFIGURED
    return Dot1xDhcpProfilingFact(state, frozenset(options)).available(SOURCE)


def accounting(state: FeatureState = FeatureState.ENABLED) -> Fact[Dot1xRadiusAccountingFact]:
    """Build 802.1X RADIUS accounting state."""
    return Dot1xRadiusAccountingFact(state).available(SOURCE)


def assess(**overrides: Any) -> VulnerabilityResult:  # noqa: ANN401 - Each override is one precisely typed fact.
    """Assess an affected baseline with selected facts replaced."""
    facts: dict[str, Any] = {
        "version": eos_version_fact("4.32.0F"),
        "platform": platform_fact("DCS-7050SX3-48YC12-F"),
        "system_auth_control": system_auth_control(),
        "authenticators": authenticators(Dot1xPortControl.AUTO),
        "profiling": profiling(Dot1xDhcpProfilingOption.HOSTNAME),
        "accounting": accounting(),
    }
    facts.update(overrides)
    return _assess_sa217(**facts)


def missing(definition: type[Any]) -> Any:  # noqa: ANN401 - Returns the unavailable form of the requested fact.
    """Build an unavailable fact of the requested definition."""
    return definition.unavailable(FactProblemKind.MISSING, SOURCE)


def test_affected_baseline_remediation() -> None:
    """All four source conditions on an affected release and platform require the software fix."""
    result = assess()
    assert isinstance(result, AffectedResult)
    assert result.vulnerability_id == VULNERABILITY_ID
    assert result.remediation == remediation_from(EOSVersion(4, 32, 0, suffix="F"))


@pytest.mark.parametrize("option", list(Dot1xDhcpProfilingOption))
def test_each_profiling_option_alone_is_sufficient(option: Dot1xDhcpProfilingOption) -> None:
    """Any single DHCP profiling option satisfies the OR condition."""
    assert isinstance(assess(profiling=profiling(option)), AffectedResult)


@pytest.mark.parametrize("port_control", list(Dot1xPortControl))
def test_every_port_control_mode_is_an_authenticator(port_control: Dot1xPortControl) -> None:
    """The authenticator role alone satisfies the interface condition; port-control auto is not required."""
    assert isinstance(assess(authenticators=authenticators(port_control)), AffectedResult)


@pytest.mark.parametrize(
    ("override", "decisive"),
    [
        pytest.param({"system_auth_control": system_auth_control(FeatureState.DISABLED)}, Dot1xSystemAuthControlFact, id="global-disabled"),
        pytest.param({"system_auth_control": system_auth_control(FeatureState.UNSUPPORTED)}, Dot1xSystemAuthControlFact, id="dot1x-unsupported"),
        pytest.param({"authenticators": authenticators()}, Dot1xAuthenticatorInterfacesFact, id="no-authenticator"),
        pytest.param({"profiling": profiling()}, Dot1xDhcpProfilingFact, id="no-profiling"),
        pytest.param({"accounting": accounting(FeatureState.DISABLED)}, Dot1xRadiusAccountingFact, id="no-radius-accounting"),
    ],
)
def test_each_missing_prerequisite_is_decisive(override: dict[str, Any], decisive: type[Any]) -> None:
    """Each required condition independently closes exposure, even with unavailable scope evidence."""
    result = assess(version=missing(EosVersionFact), platform=missing(PlatformIdentityFact), **override)
    assert isinstance(result, NotAffectedResult)
    assert len(result.decisive) == 1
    evidence = result.decisive[0]
    assert isinstance(evidence, AvailableFact)
    assert isinstance(evidence.value, decisive)


@pytest.mark.parametrize(
    "unavailable",
    [
        pytest.param({"system_auth_control": missing(Dot1xSystemAuthControlFact)}, id="global"),
        pytest.param({"authenticators": missing(Dot1xAuthenticatorInterfacesFact)}, id="authenticator"),
        pytest.param({"profiling": missing(Dot1xDhcpProfilingFact)}, id="profiling"),
        pytest.param({"accounting": missing(Dot1xRadiusAccountingFact)}, id="accounting"),
    ],
)
def test_absent_prerequisite_bypasses_other_unavailable_prerequisites(unavailable: dict[str, Any]) -> None:
    """A decisively absent condition wins over unrelated unavailable conditions."""
    facts = {"accounting": accounting(FeatureState.DISABLED)} if "accounting" not in unavailable else {"profiling": profiling()}
    assert isinstance(assess(**unavailable, **facts), NotAffectedResult)


def test_fixed_release_bypasses_unavailable_platform_and_prerequisites() -> None:
    """A first fixed release decides scope even when other evidence is unavailable."""
    result = assess(
        version=eos_version_fact("4.35.6M"),
        platform=missing(PlatformIdentityFact),
        system_auth_control=missing(Dot1xSystemAuthControlFact),
        accounting=missing(Dot1xRadiusAccountingFact),
    )
    assert isinstance(result, NotAffectedResult)


def test_excluded_platform_bypasses_unavailable_version_and_prerequisites() -> None:
    """A virtual platform exclusion decides scope even when other evidence is unavailable."""
    result = assess(version=missing(EosVersionFact), platform=platform_fact("cEOSLab"), profiling=missing(Dot1xDhcpProfilingFact))
    assert isinstance(result, NotAffectedResult)


def test_all_unavailable_inputs_are_aggregated() -> None:
    """Every required unavailable input is retained in declaration order."""
    result = _assess_sa217(
        missing(EosVersionFact),
        missing(PlatformIdentityFact),
        missing(Dot1xSystemAuthControlFact),
        missing(Dot1xAuthenticatorInterfacesFact),
        missing(Dot1xDhcpProfilingFact),
        Dot1xRadiusAccountingFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
    )
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (
        EosVersionFact,
        PlatformIdentityFact,
        Dot1xSystemAuthControlFact,
        Dot1xAuthenticatorInterfacesFact,
        Dot1xDhcpProfilingFact,
        Dot1xRadiusAccountingFact,
    )


def test_unavailable_prerequisite_on_affected_scope_is_error() -> None:
    """An established scope cannot hide a missing required condition."""
    result = assess(accounting=missing(Dot1xRadiusAccountingFact))
    assert isinstance(result, ErrorResult)
    assert tuple(problem.definition for problem in result.problems) == (Dot1xRadiusAccountingFact,)


@pytest.mark.parametrize("model", ["DCS-UNRECOGNIZED", "DCS-7304"])
def test_unknown_or_incomplete_platform_is_error(model: str) -> None:
    """Unrecognized identity or a chassis without discovered modules cannot prove scope."""
    assert isinstance(assess(platform=platform_fact(model)), ErrorResult)


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
        PlatformFamily.SERIES_7260_X,
        PlatformFamily.SERIES_7260_X3,
        PlatformFamily.SERIES_7280_R,
        PlatformFamily.SERIES_7280_R2,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7280_R4,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7060_X,
        PlatformFamily.SERIES_7060_X2,
        PlatformFamily.SERIES_7060_X4,
        PlatformFamily.SERIES_7060_X5,
        PlatformFamily.SERIES_7060_X6,
        PlatformFamily.SERIES_7300_X,
        PlatformFamily.SERIES_7300_X3,
        PlatformFamily.SERIES_7320_X,
        PlatformFamily.SERIES_7358_X4,
        PlatformFamily.SERIES_7368_X4,
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_7800_R4,
    ],
)
def test_affected_platform_families(family: PlatformFamily) -> None:
    """Every listed physical family is within scope."""
    assert isinstance(assess(platform=family_fact(family)), AffectedResult)


@pytest.mark.parametrize("model", ["DCS-7060XE7-32", "CCS-720DT-48S", "CCS-722XPM-48ZY8", "CCS-710P-16P", "DCS-7010TX-48", "DCS-7020SR-24C2"])
def test_affected_platform_models(model: str) -> None:
    """Real model names resolve into listed families, including the 7060XE7 within the 7060X series."""
    assert isinstance(assess(platform=platform_fact(model)), AffectedResult)


@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_7130,
        PlatformFamily.SERIES_7170,
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
    """Every explicitly unaffected EOS product is outside scope."""
    assert isinstance(assess(platform=family_fact(family)), NotAffectedResult)


@pytest.mark.parametrize(
    "family",
    [PlatformFamily.SERIES_7050_X, PlatformFamily.SERIES_7050_X2, PlatformFamily.SERIES_7280_E, PlatformFamily.SERIES_7500_E, PlatformFamily.SERIES_7720_R4],
)
def test_unlisted_platform_families(family: PlatformFamily) -> None:
    """Families absent from the affected list are outside scope."""
    assert isinstance(assess(platform=family_fact(family)), NotAffectedResult)


@pytest.mark.parametrize("model", ["cEOSLab", "vEOS-lab", "CloudEOS", "vEOS"])
def test_virtual_platform_models(model: str) -> None:
    """Virtual EOS is excluded even when it accepts the configuration."""
    assert isinstance(assess(platform=platform_fact(model)), NotAffectedResult)


def test_metadata_uses_allocated_identity() -> None:
    """Metadata uses the allocated SA and CVE identifiers and the implementation date."""
    assert ADVISORY.sa_number == "0217"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities) == (VULNERABILITY_ID,)


EXPOSED_INTERFACES = {"Ethernet20": dot1x_interface("controlled"), "Ethernet21": dot1x_interface("forceAuth")}


def accounting_methods(*methods: str, action: str = "startStop") -> dict[str, object]:
    """Return ``show aaa methods accounting`` with one default 802.1X method list."""
    dot1x: dict[str, object] = {"defaultMethods": list(methods), "consoleMethods": []}
    if methods:
        dot1x = {"defaultAction": action, **dot1x}
    return {
        "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
        "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
        "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
        "dot1xAcctMethods": {"dot1x": dot1x},
    }


def dot1x_config(*options: str, accounting_line: str = "aaa accounting dot1x default start-stop group radius") -> str:
    """Return ``show running-config section dot1x`` as captured on EOS 4.32.0F."""
    return (
        f"{accounting_line}\n"
        "dot1x\n"
        "   captive-portal start limit infinite\n" + "".join(f"   radius av-pair dhcp {option}\n" for option in options) + "interface Ethernet20\n"
        "   dot1x pae authenticator\n"
        "   dot1x port-control auto\n"
        "interface Ethernet21\n"
        "   dot1x pae authenticator\n"
        "dot1x system-auth-control\n"
    )


NO_RADIUS_GROUPS: dict[str, object] = {"radiusServers": [], "groups": {}, "srcIntf": {}, "lastCounterClearTime": 0.0}
NAMED_RADIUS_GROUP: dict[str, object] = {
    "radiusServers": [],
    "groups": {"ACCT": {"serverGroup": "RADIUS", "members": []}},
    "srcIntf": {},
    "lastCounterClearTime": 0.0,
}
HARDWARE_MODEL = "DCS-7050SX3-48YC12-F"
AFFECTED_MESSAGE = (
    "The device is affected because EOS version '{version}' is affected, platform '{model}' is within the affected platform scope, "
    "the 802.1X system authentication control is enabled, the 802.1X authenticator interface configuration is configured, "
    "the 802.1X DHCP profiling configuration is configured, and the 802.1X RADIUS accounting is enabled."
)


def affected(version: str, model: str = HARDWARE_MODEL) -> UnitTestResult:
    """Build the expected affected result for one version and platform."""
    current = build_eos_version(version)
    assert current is not None
    return expected(AntaTestStatus.FAILURE, AFFECTED_MESSAGE.format(version=version, model=model), remediation_from(current))


def not_affected(reason: str) -> UnitTestResult:
    """Build the expected not-affected result."""
    return expected(AntaTestStatus.SUCCESS, f"The device is not affected because {reason}.", None)


def positive(
    *,
    dot1x: dict[str, object] | None = None,
    config: str | None = None,
    methods: tuple[str, ...] = ("group radius",),
    action: str = "startStop",
    radius: object = None,
) -> list[Any]:
    """Return command outputs for an exposed configuration, with selected outputs replaced."""
    dot1x_output = dot1x_all(interfaces=EXPOSED_INTERFACES) if dot1x is None else dot1x
    return [
        dot1x_output,
        dot1x_output,
        dot1x_config("hostname") if config is None else config,
        accounting_methods(*methods, action=action),
        NO_RADIUS_GROUPS if radius is None else radius,
    ]


_DATA: AntaUnitTestData = {
    (SA217, "affected-hardware-sample"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(),
        "expected": affected("4.32.0F"),
    },
    (SA217, "affected-introduction-release"): {
        "version": build_eos_version("4.31.2F"),
        "platform": build_eos_platform("CCS-720XP-48ZC2"),
        "eos_data": positive(),
        "expected": affected("4.31.2F", "CCS-720XP-48ZC2"),
    },
    (SA217, "affected-4.35-named-radius-group-stop-only"): {
        "version": build_eos_version("4.35.5M"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(methods=("ACCT",), action="stopOnly", radius=NAMED_RADIUS_GROUP),
        "expected": affected("4.35.5M"),
    },
    (SA217, "affected-4.32-named-radius-group"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(methods=("group ACCT",), radius=NAMED_RADIUS_GROUP),
        "expected": affected("4.32.0F"),
    },
    (SA217, "affected-global-without-current-supplicant-force-authorized-only"): {
        "version": build_eos_version("4.36.2F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(dot1x=dot1x_all(interfaces={"Ethernet21": dot1x_interface("forceAuth")})),
        "expected": affected("4.36.2F"),
    },
    (SA217, "affected-all-three-profiling-options-explicit-no-dhcp-snooping"): {
        "version": build_eos_version("4.34.7M"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(config=dot1x_config("hostname", "parameter-request-list", "vendor-class-id")),
        "expected": affected("4.34.7M"),
    },
    (SA217, "affected-authenticator-beside-incomplete-interface"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(dot1x=dot1x_all(interfaces={"Ethernet20": dot1x_interface("controlled"), "Ethernet21": {}})),
        "expected": affected("4.32.0F"),
    },
    (SA217, "affected-profiling-beside-unrecognized-option"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(config=dot1x_config("client-identifier", "hostname")),
        "expected": affected("4.32.0F"),
    },
    (SA217, "affected-radius-group-beside-malformed-group"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(
            methods=("group ACCT",),
            radius={"radiusServers": [], "groups": {"BROKEN": {"members": []}, "ACCT": {"serverGroup": "RADIUS", "members": []}}},
        ),
        "expected": affected("4.32.0F"),
    },
    (SA217, "error-only-unrecognized-profiling-option"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(config=dot1x_config("client-identifier")),
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X DHCP profiling configuration because the 'show running-config section dot1x' output is invalid.",
            None,
        ),
    },
    (SA217, "not-affected-global-disabled-missing-scope"): {
        "version": None,
        "platform": None,
        "eos_data": positive(dot1x=dot1x_all(system_auth_control=False, interfaces=EXPOSED_INTERFACES)),
        "expected": not_affected("the 802.1X system authentication control is disabled"),
    },
    (SA217, "not-affected-no-authenticator-interface"): {
        "version": None,
        "platform": None,
        "eos_data": positive(dot1x=dot1x_all(interfaces={})),
        "expected": not_affected("the 802.1X authenticator interface configuration is not configured"),
    },
    (SA217, "not-affected-no-profiling-option"): {
        "version": None,
        "platform": None,
        "eos_data": positive(config=dot1x_config()),
        "expected": not_affected("the 802.1X DHCP profiling configuration is not configured"),
    },
    (SA217, "not-affected-no-accounting"): {
        "version": None,
        "platform": None,
        "eos_data": positive(methods=()),
        "expected": not_affected("the 802.1X RADIUS accounting is disabled"),
    },
    (SA217, "not-affected-logging-accounting-only"): {
        "version": None,
        "platform": None,
        "eos_data": positive(methods=("logging",)),
        "expected": not_affected("the 802.1X RADIUS accounting is disabled"),
    },
    (SA217, "not-affected-first-fixed-release"): {
        "version": build_eos_version("4.33.10M"),
        "platform": None,
        "eos_data": positive(),
        "expected": not_affected("EOS version '4.33.10M' is outside the affected releases"),
    },
    (SA217, "not-affected-before-introduction"): {
        "version": build_eos_version("4.31.1F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(),
        "expected": not_affected("EOS version '4.31.1F' is outside the affected releases"),
    },
    (SA217, "not-affected-veos-lab"): {
        "version": build_eos_version("4.35.3F"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": positive(methods=("radius",)),
        "expected": not_affected("platform 'vEOS-lab' is outside the affected platform scope"),
    },
    (SA217, "error-missing-version"): {
        "version": None,
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(),
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the EOS version because it is missing from device metadata.", None),
    },
    (SA217, "error-incomplete-dot1x-and-radius"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": positive(dot1x={"interfaces": {"Ethernet20": {}}}, methods=("group ACCT",), radius={"radiusServers": []}),
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X system authentication control state because the 'show dot1x all' output is incomplete. "
            "The test could not determine the 802.1X authenticator interfaces because the 'show dot1x all' output is incomplete. "
            "The test could not determine the 802.1X RADIUS accounting state because the 'show radius' output is incomplete.",
            None,
        ),
    },
    (SA217, "error-invalid-port-control-and-accounting"): {
        "version": build_eos_version("4.32.0F"),
        "platform": build_eos_platform(HARDWARE_MODEL),
        "eos_data": [
            dot1x_all(interfaces={"Ethernet20": dot1x_interface("auto")}),
            dot1x_all(interfaces={"Ethernet20": dot1x_interface("auto")}),
            dot1x_config("hostname"),
            {"dot1xAcctMethods": {"dot1x": {"defaultMethods": "group radius"}}},
            NO_RADIUS_GROUPS,
        ],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X authenticator interfaces because the 'show dot1x all' output is invalid. "
            "The test could not determine the 802.1X RADIUS accounting state because the 'show aaa methods accounting' output is invalid.",
            None,
        ),
    },
}


def test_commands_are_derived_from_required_facts() -> None:
    """Each fact receives its own command, including the shared 802.1X command."""
    commands = [command for command in SA217.commands if isinstance(command, AntaCommand)]
    assert len(commands) == len(SA217.commands)
    assert [command.command for command in commands] == [
        "show dot1x all",
        "show dot1x all",
        "show running-config section dot1x",
        "show aaa methods accounting",
        "show radius",
    ]


UNSUPPORTED = "This command is not supported on this hardware platform"
FAILED = "invalid command"


async def run_with_errors(errors: dict[int, str], eos_data: list[Any], *, version: str = "4.32.0F", model: str = HARDWARE_MODEL) -> SA217:
    """Run the advisory through the ANTA test wrapper with selected commands reporting one error."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version(version)
    device.platform = build_eos_platform(model)
    test_instance = cast("Any", SA217)(device=device, eos_data=eos_data)
    for index, error in errors.items():
        test_instance.instance_commands[index].output = None
        test_instance.instance_commands[index].errors = [error]
    test_instance.collect = AsyncMock()
    await test_instance.test()
    return cast("SA217", test_instance)


async def test_unsupported_dot1x_is_not_affected() -> None:
    """A platform without 802.1X support cannot have the required system authentication control."""
    result = (await run_with_errors({0: UNSUPPORTED, 1: UNSUPPORTED}, positive())).result
    assert result.result is AntaTestStatus.SUCCESS
    assert result.atomic_results[0].messages == ["The device is not affected because the 802.1X system authentication control is not supported."]


async def test_unsupported_accounting_command_is_error() -> None:
    """Unsupported accounting evidence is reported with its own command source."""
    result = (await run_with_errors({3: UNSUPPORTED}, positive())).result
    assert result.result is AntaTestStatus.ERROR
    assert result.atomic_results[0].messages == [
        "The test could not determine the 802.1X RADIUS accounting state because 'show aaa methods accounting' is not supported."
    ]
    assert _get_atomic_vulnerability_ids(result.atomic_results[0]) == (VULNERABILITY_ID,)


AFFECTED_SAMPLE_MESSAGE = AFFECTED_MESSAGE.format(version="4.32.0F", model=HARDWARE_MODEL)


@pytest.mark.parametrize(
    ("errors", "eos_data", "version", "model", "status", "message"),
    [
        pytest.param(
            {2: FAILED},
            positive(),
            "4.35.6M",
            HARDWARE_MODEL,
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases.",
            id="fixed-release-with-failed-configuration",
        ),
        pytest.param(
            {2: UNSUPPORTED},
            positive(),
            "4.35.3F",
            "vEOS-lab",
            AntaTestStatus.SUCCESS,
            "The device is not affected because platform 'vEOS-lab' is outside the affected platform scope.",
            id="excluded-platform-with-unsupported-configuration",
        ),
        pytest.param(
            dict.fromkeys(range(5), FAILED),
            positive(),
            "4.35.3F",
            "vEOS-lab",
            AntaTestStatus.SUCCESS,
            "The device is not affected because platform 'vEOS-lab' is outside the affected platform scope.",
            id="excluded-platform-with-every-command-failed",
        ),
        pytest.param(
            {2: FAILED, 3: FAILED},
            positive(dot1x=dot1x_all(system_auth_control=False, interfaces=EXPOSED_INTERFACES)),
            "4.32.0F",
            HARDWARE_MODEL,
            AntaTestStatus.SUCCESS,
            "The device is not affected because the 802.1X system authentication control is disabled.",
            id="absent-condition-with-other-failures",
        ),
        pytest.param(
            {4: FAILED},
            positive(methods=("radius",)),
            "4.32.0F",
            HARDWARE_MODEL,
            AntaTestStatus.FAILURE,
            AFFECTED_SAMPLE_MESSAGE,
            id="builtin-radius-with-failed-show-radius",
        ),
        pytest.param(
            {2: FAILED},
            positive(),
            "4.32.0F",
            HARDWARE_MODEL,
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X DHCP profiling configuration because 'show running-config section dot1x' could not be collected.",
            id="needed-configuration-failed",
        ),
        pytest.param(
            {4: FAILED},
            positive(methods=("group ACCT",)),
            "4.32.0F",
            HARDWARE_MODEL,
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X RADIUS accounting state because 'show radius' could not be collected.",
            id="named-group-with-failed-show-radius",
        ),
        pytest.param(
            {0: FAILED, 1: FAILED, 3: FAILED},
            positive(),
            "4.32.0F",
            HARDWARE_MODEL,
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X system authentication control state because 'show dot1x all' could not be collected. "
            "The test could not determine the 802.1X authenticator interfaces because 'show dot1x all' could not be collected. "
            "The test could not determine the 802.1X RADIUS accounting state because 'show aaa methods accounting' could not be collected.",
            id="every-needed-failure-retains-its-source",
        ),
    ],
)
async def test_command_failures_are_assessed_with_other_evidence(
    errors: dict[int, str], eos_data: list[Any], version: str, model: str, status: AntaTestStatus, message: str
) -> None:
    """Command failures reach the assessment, so they cannot override decisive evidence and are reported only when needed."""
    result = (await run_with_errors(errors, eos_data, version=version, model=model)).result
    assert result.result is status
    assert len(result.atomic_results) == 1
    assert result.atomic_results[0].messages == [message]
    assert _get_atomic_vulnerability_ids(result.atomic_results[0]) == (VULNERABILITY_ID,)
