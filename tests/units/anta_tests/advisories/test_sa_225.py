# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 225."""

from __future__ import annotations

import asyncio
from datetime import date
from functools import partial
from typing import TYPE_CHECKING

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.interfaces import InterfaceSpeed, InterfaceSpeedFact
from anta._advisory.facts.models import FactProblemKind, FactSource, FactSourceKind
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ConfigurationAssessment, ErrorResult, NotAffectedResult, PlatformAssessment, PlatformRelation
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._eos.platform import PlatformComponentIdentity, PlatformComponentRole, PlatformFamily, PlatformType
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_225 import ADVISORY, AFFECTED_VERSION_MATRIX, SA225, _assess_sa225
from tests.units._advisory.test_optional_commands import NoOpAntaDevice
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Generic ANTA test collection.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
SPEED_SOURCE = FactSource("show running-config sanitized all section ^interface", FactSourceKind.COMMAND)
DEFAULT_CONFIG = "interface Ethernet3/1\n   no shutdown\n   no speed\ninterface Ethernet5/1\n   speed auto 1g\n"
CONSTRAINED_CONFIG = "interface Ethernet3/1\n   speed auto 1g\ninterface Ethernet5/1\n   no speed\n"
MODULES = {"modules": {"3": {"modelName": "CCS-750XM-48TX-LC"}, "5": {"modelName": "CCS-750X-48TP-LC"}}}
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
        FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 7, hotfix=1, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 6, suffix="M"),
)
expected = partial(build_expected_advisory_result, "CVE-2026-121369")
_DATA: AntaUnitTestData = {
    (SA225, "affected-default-speed"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CCS-758-CH-F", MODULES),
        "eos_data": [DEFAULT_CONFIG],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is affected, platform 'CCS-758-CH-F' is within the affected platform scope, "
            "and the interface default or unbounded automatic speed configuration is configured.",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA225, "constrained-speed-only-affected-card"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CCS-758-CH-F", MODULES),
        "eos_data": [CONSTRAINED_CONFIG],
        "expected": expected(
            AntaTestStatus.SUCCESS, "The device is not affected because the interface default or unbounded automatic speed configuration is not configured.", None
        ),
    },
    (SA225, "lane-constrained-speed"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CCS-758-CH-F", MODULES),
        "eos_data": ["interface Ethernet3/1\n   no phy media base-t negotiation unsupported speed\n   speed 100g-4\n"],
        "expected": expected(
            AntaTestStatus.SUCCESS, "The device is not affected because the interface default or unbounded automatic speed configuration is not configured.", None
        ),
    },
    (SA225, "fixed-exact-hotfix"): {
        "version": build_eos_version("4.34.7.1M"),
        "platform": None,
        "eos_data": [""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.34.7.1M' is outside the affected releases.", None),
    },
    (SA225, "excluded-platform"): {
        "version": None,
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'cEOSLab' is outside the affected platform scope.", None),
    },
    (SA225, "excluded-linecards-on-affected-chassis"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CCS-758-CH-F", {"modules": {"3": {"modelName": "CCS-750X-48TP-LC"}}}),
        "eos_data": [""],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the installed components of platform 'CCS-758-CH-F' are outside the affected component scope.",
            None,
        ),
    },
    (SA225, "missing-full-default-speed"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("CCS-758-CH-F", MODULES),
        "eos_data": ["interface Ethernet3/1\n"],
        "expected": expected(
            AntaTestStatus.ERROR,
            (
                "The test could not determine the Ethernet interface speed configuration because "
                "the 'show running-config sanitized all section ^interface' output is incomplete."
            ),
            None,
        ),
    },
}


def version_fact(version: str = "4.35.6M") -> Fact[EosVersionFact]:
    """Construct a typed source-independent release observation."""
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


def platform_fact(*models: str, slots: tuple[str | None, ...] | None = None) -> Fact[PlatformIdentityFact]:
    """Construct a complete 750X inventory with explicit linecard slots."""
    slots = slots if slots is not None else tuple(str(index + 3) for index in range(len(models)))
    modules = tuple(PlatformComponentIdentity(model, PlatformComponentRole.LINE_CARD, slot) for model, slot in zip(models, slots, strict=True))
    return PlatformIdentityFact("CCS-758-CH-F", PlatformType.CHASSIS, modules, frozenset({PlatformFamily.SERIES_750_X})).available(SOURCE)


def speeds_fact(*observations: tuple[str, str]) -> Fact[InterfaceSpeedFact]:
    """Construct neutral per-interface observations for pure assessment tests."""
    return InterfaceSpeedFact.from_interfaces(tuple(InterfaceSpeed(*item) for item in observations)).available(SPEED_SOURCE)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.33.99M", False),
        ("4.34.0F", False),
        ("4.34.1F", False),
        ("4.34.1.1F", False),
        ("4.34.2F", True),
        ("4.34.6M", True),
        ("4.34.7M", True),
        ("4.34.7.0M", True),
        ("4.34.7.1M", False),
        ("4.34.7.2M", False),
        ("4.34.8M", False),
        ("4.35.0F", True),
        ("4.35.6M", True),
        ("4.35.7M", False),
        ("4.35.8M", False),
        ("4.36.0F", True),
        ("4.36.1F", True),
        ("4.36.1M", True),
        ("4.36.2F", False),
        ("4.36.2M", False),
        ("4.36.3M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_version_boundaries(version: str, affected: bool) -> None:
    """Independently spell out introduction and every exact source fix boundary."""
    result = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert result.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


@pytest.mark.parametrize("model", ["CCS-750XM-48TX-LC", "CCS-750XPM-48NH-LC", "CCS-750XPM-48TXH-LC"])
@pytest.mark.parametrize("speed", ["no speed", "speed auto", "speed auto 1g", "speed forced 10000full"])
def test_exact_cards_and_configuration(model: str, speed: str) -> None:
    """Each exact SKU uses persistent source-required speed, never link state."""
    result = _assess_sa225(version_fact(), platform_fact(model), speeds_fact(("Ethernet3/1", speed)))
    assert isinstance(result, AffectedResult if speed in {"no speed", "speed auto"} else NotAffectedResult)


@pytest.mark.parametrize("model", ["CCS-750X-48TP-LC", "CCS-750XM-48TXH-LC", "CCS-750XPM-48TX-LC"])
def test_other_linecards(model: str) -> None:
    """Similar model strings cannot broaden the controlled source's exact list."""
    unavailable = InterfaceSpeedFact.unavailable(FactProblemKind.MISSING, SPEED_SOURCE)
    platform = platform_fact(model)
    result = _assess_sa225(version_fact(), platform, unavailable)
    assert isinstance(result, NotAffectedResult)
    (assessment,) = result.decisive
    assert isinstance(assessment, PlatformAssessment)
    assert assessment.relation is PlatformRelation.COMPONENTS_OUTSIDE_SCOPE
    assert assessment.fact is platform


@pytest.mark.parametrize("family", [family for family in PlatformFamily if family not in {PlatformFamily.SERIES_750_X, PlatformFamily.SERIES_750}])
def test_excluded_platform_families(family: PlatformFamily) -> None:
    """Every resolved family outside the source's modular 750X scope is excluded."""
    platform = PlatformIdentityFact("excluded", PlatformType.FIXED, (), frozenset({family})).available(SOURCE)
    assert isinstance(
        _assess_sa225(EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE), platform, InterfaceSpeedFact.unavailable(FactProblemKind.MISSING, SPEED_SOURCE)),
        NotAffectedResult,
    )


def test_mixed_cards_slots_and_pending_power() -> None:
    """Constrained unaffected-card ports cannot mask any affected-card exposure."""
    platform = platform_fact("CCS-750XM-48TX-LC", "CCS-750X-48TP-LC", "CCS-750XPM-48NH-LC", slots=("3", "5", "6"))
    exposed = speeds_fact(("Ethernet3/1", "speed auto 1g"), ("Ethernet5/1", "speed auto 1g"), ("Ethernet6/1", "no speed"))
    result = _assess_sa225(version_fact(), platform, exposed)
    assert isinstance(result, AffectedResult)
    condition = result.conditions[0]
    assert isinstance(condition, ConfigurationAssessment)
    assert isinstance(condition.fact.value, InterfaceSpeedFact)
    assert condition.fact.value.interfaces == (InterfaceSpeed("Ethernet3/1", "speed auto 1g"), InterfaceSpeed("Ethernet6/1", "no speed"))
    constrained = speeds_fact(("Ethernet3/1", "speed auto 1g"), ("Ethernet5/1", "no speed"), ("Ethernet6/1", "speed auto 1g"))
    assert isinstance(_assess_sa225(version_fact(), platform, constrained), NotAffectedResult)


def test_missing_slot_or_speed() -> None:
    """Missing card-to-interface correlation is an error unless exposure is proved."""
    platform = platform_fact("CCS-750XM-48TX-LC", "CCS-750XPM-48NH-LC")
    assert isinstance(_assess_sa225(version_fact(), platform, speeds_fact(("Ethernet3/1", "speed auto 1g"))), ErrorResult)
    assert isinstance(_assess_sa225(version_fact(), platform, speeds_fact(("Ethernet3/1", "no speed"))), AffectedResult)
    assert isinstance(_assess_sa225(version_fact(), platform_fact("CCS-750XM-48TX-LC", slots=(None,)), speeds_fact(("Ethernet3/1", "no speed"))), ErrorResult)
    assert isinstance(_assess_sa225(version_fact(), platform_fact(), speeds_fact(("Ethernet3/1", "no speed"))), ErrorResult)


def test_all_required_problems_and_fixed_short_circuit() -> None:
    """Retain each unavailable required observation, but allow independent fixes."""
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    speed = InterfaceSpeedFact.unavailable(FactProblemKind.UNSUPPORTED, SPEED_SOURCE)
    result = _assess_sa225(version, platform, speed)
    assert isinstance(result, ErrorResult)
    assert result.problems == (version, platform, speed)
    assert isinstance(_assess_sa225(version_fact("4.34.7.1M"), platform, speed), NotAffectedResult)


def test_full_class_exact_rendering_and_attribution() -> None:
    """Check exact public wording, remediation and single-CVE atomic attribution."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("CCS-758-CH-F", MODULES)
    instance = SA225(device, eos_data=[DEFAULT_CONFIG])
    asyncio.run(instance.test())
    assert instance.result.messages == [
        (
            "Verify CVE-2026-121369. - The device is affected because EOS version '4.35.6M' is affected, "
            "platform 'CCS-758-CH-F' is within the affected platform scope, "
            "and the interface default or unbounded automatic speed configuration is configured."
        )
    ]
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-121369",)
    assert atomic.remediation == EXPECTED_REMEDIATION
    assert ADVISORY.sa_number == "0225"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25047-security-advisory-0225"


@pytest.mark.parametrize(("version", "status"), [("4.35.6M", AntaTestStatus.ERROR), ("4.35.7M", AntaTestStatus.SUCCESS)])
def test_command_failure_is_scoped_and_attributed(version: str, status: AntaTestStatus) -> None:
    """Actual command failure remains atomic and cannot conceal a decisive fix."""
    device = NoOpAntaDevice("unit-test")
    device.version = build_eos_version(version)
    device.platform = build_eos_platform("CCS-758-CH-F", MODULES)
    instance = SA225(device)
    instance.instance_commands[0].errors = ["invalid command"]
    asyncio.run(instance.test())
    assert instance.result.result is status
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-121369",)
    if status is AntaTestStatus.ERROR:
        assert instance.result.messages == [
            (
                "Verify CVE-2026-121369. - The test could not determine the Ethernet interface speed configuration "
                "because 'show running-config sanitized all section ^interface' could not be collected."
            )
        ]


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("other_slot", ["3", "4", "5"])
@pytest.mark.parametrize(
    ("broken_speed", "problem"),
    [
        ("description missing speed", FactProblemKind.MISSING),
        ("speed invalid", FactProblemKind.MALFORMED),
        ("no speed\n   speed auto 1g", FactProblemKind.CONTRADICTORY),
    ],
)
@pytest.mark.parametrize("speed", ["no speed", "speed auto 1g"])
def test_interface_errors_do_not_erase_exposure(reverse: bool, other_slot: str, broken_speed: str, problem: FactProblemKind, speed: str) -> None:
    """Evaluate relevant slot uncertainty only when no affected port proves exposure."""
    sections = [f"interface Ethernet3/1\n   {speed}\n", f"interface Ethernet{other_slot}/2\n   {broken_speed}\n"]
    command = InterfaceSpeedFact.commands[0].model_copy()
    # Cover slot 4 when it is not the deliberately broken slot.
    if other_slot != "4":
        sections.append("interface Ethernet4/1\n   speed auto 1g\n")
    command.output = "".join(reversed(sections) if reverse else sections)
    speeds = InterfaceSpeedFact.derive(OfflineAntaDevice("unit-test"), (command,))
    platform = platform_fact("CCS-750XM-48TX-LC", "CCS-750XPM-48NH-LC", "CCS-750X-48TP-LC")
    result = _assess_sa225(version_fact(), platform, speeds)
    if speed == "no speed":
        assert isinstance(result, AffectedResult)
        assert result.remediation == EXPECTED_REMEDIATION
    elif other_slot == "5":
        assert isinstance(result, NotAffectedResult)
    else:
        assert isinstance(result, ErrorResult)
        assert tuple(item.problem for item in result.problems) == (problem,)
        assert result.problems[0].source == SPEED_SOURCE


def test_scoped_speed_problems_are_aggregated_with_missing_version() -> None:
    """Scope correlation must not let an unavailable release hide speed problems."""
    command = InterfaceSpeedFact.commands[0].model_copy()
    command.output = "interface Ethernet3/1\n   speed invalid\ninterface Ethernet4/1\n   description missing speed\n"
    speeds = InterfaceSpeedFact.derive(OfflineAntaDevice("unit-test"), (command,))
    version = EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    result = _assess_sa225(version, platform_fact("CCS-750XM-48TX-LC", "CCS-750XPM-48NH-LC"), speeds)
    assert isinstance(result, ErrorResult)
    assert tuple(item.problem for item in result.problems) == (FactProblemKind.MISSING, FactProblemKind.MALFORMED, FactProblemKind.MISSING)
    assert tuple(item.source for item in result.problems) == (SOURCE, SPEED_SOURCE, SPEED_SOURCE)


_DATA[(SA225, "affected-despite-incomplete-unaffected-port")] = {
    "version": build_eos_version("4.35.6M"),
    "platform": build_eos_platform("CCS-758-CH-F", MODULES),
    "eos_data": [DEFAULT_CONFIG + "interface Ethernet5/2\n   description missing speed\n"],
    "expected": expected(
        AntaTestStatus.FAILURE,
        "The device is affected because EOS version '4.35.6M' is affected, platform 'CCS-758-CH-F' is within the affected platform scope, "
        "and the interface default or unbounded automatic speed configuration is configured.",
        EXPECTED_REMEDIATION,
    ),
}


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("speed", ["no speed", "speed auto 1g"])
@pytest.mark.parametrize(
    "extra_modules",
    [
        {"5": {}},
        {"5": {"modelName": "UNRECOGNIZED-MODULE"}},
        {"5": {"typeDescription": "Linecard"}},
        {"Linecard5": {"modelName": "CCS-750XPM-48NH-LC"}},
    ],
)
def test_incomplete_inventory_does_not_erase_proven_exposure(reverse: bool, speed: str, extra_modules: dict[str, dict[str, str]]) -> None:
    """Use actual metadata parsing and the complete advisory for mixed inventory."""
    modules = {"3": {"modelName": "CCS-750XM-48TX-LC"}, **extra_modules}
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("CCS-758-CH-F", {"modules": dict(reversed(list(modules.items()))) if reverse else modules})
    instance = SA225(device, eos_data=[f"interface Ethernet3/1\n   {speed}\n"])
    asyncio.run(instance.test())
    assert instance.result.result is (AntaTestStatus.FAILURE if speed == "no speed" else AntaTestStatus.ERROR)
    if speed == "no speed":
        assert instance.result.messages == [
            (
                "Verify CVE-2026-121369. - The device is affected because EOS version '4.35.6M' is affected, "
                "platform 'CCS-758-CH-F' is within the affected platform scope, "
                "and the interface default or unbounded automatic speed configuration is configured."
            )
        ]
        atomic = instance.result.atomic_results[0]
        assert isinstance(atomic, _AdvisoryAtomicTestResult)
        assert atomic.remediation == EXPECTED_REMEDIATION
    else:
        assert "platform identity" in instance.result.messages[0]


@pytest.mark.parametrize("slot", [None, "Linecard3"])
def test_an_affected_card_requires_its_own_valid_slot(slot: str | None) -> None:
    """Uncorrelated speed evidence cannot establish exposure for an unresolved card."""
    result = _assess_sa225(version_fact(), platform_fact("CCS-750XM-48TX-LC", slots=(slot,)), speeds_fact(("Ethernet3/1", "no speed")))
    assert isinstance(result, ErrorResult)
    assert tuple(problem.problem for problem in result.problems) == (FactProblemKind.INVALID,)


def test_unresolved_inventory_and_speed_errors_are_aggregated() -> None:
    """No proven exposure means both inventory and relevant speed failures matter."""
    device = OfflineAntaDevice("unit-test")
    identity = build_eos_platform("CCS-758-CH-F", {"modules": {"3": {"modelName": "CCS-750XM-48TX-LC"}, "5": {}}})
    assert identity is not None
    platform = PlatformIdentityFact.from_identity(identity).available(SOURCE)
    command = InterfaceSpeedFact.commands[0].model_copy()
    command.output = "interface Ethernet3/1\n   speed invalid\n"
    speeds = InterfaceSpeedFact.derive(device, (command,))
    result = _assess_sa225(EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE), platform, speeds)
    assert isinstance(result, ErrorResult)
    assert {problem.definition for problem in result.problems} == {EosVersionFact, PlatformIdentityFact, InterfaceSpeedFact}
    assert len(result.problems) == 3
