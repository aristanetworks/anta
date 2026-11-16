# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Independent version-boundary and end-to-end tests for SA-0201 revision 1.3."""

# pylint: disable=duplicate-code

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.findings.models import AffectedResult, ComponentVersionAssessment, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import AllOf, ChangeSoftwareVersion, FixedRelease, KnownFixedReleases, OperationalAction, RemediationPlan, SoftwareTarget
from anta._advisory.results import _AdvisoryAtomicTestResult, _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryStatus
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_201 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    FIXED_RELEASES,
    SA201,
    _assess_sa201,
    _compatible_terminattr_fixes,
    _terminattr_version_assessment,
)
from tests.units.anta_tests import (
    build_eos_platform,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
PACKAGE_SOURCE = FactSource("show version detail", FactSourceKind.COMMAND)
PACKAGE: dict[str, object] = {"details": {"packages": {"TerminAttr-core": {"version": "v1.46.2", "release": "1"}}}}
FIXED_PACKAGE: dict[str, object] = {"details": {"packages": {"TerminAttr-core": {"version": "v1.46.3", "release": "1"}}}}

# Expected source boundaries and remediation are independent from production literals.
EXPECTED_EOS_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, hotfix=2, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, hotfix=2, suffix="M")),
)
EXPECTED_EOS_ACTION = ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 3, suffix="M"), KnownFixedReleases(EXPECTED_EOS_FIXED_RELEASES))
EXPECTED_VERIFY_TERMINATTR = OperationalAction("Verify TerminAttr is outside the affected versions and supported on the target EOS release; upgrade it if needed.")
EXPECTED_UPGRADE_TERMINATTR = OperationalAction(
    "Upgrade TerminAttr to a fixed release supported on the target EOS release; confirm compatibility with Arista before selecting the release."
)
EXPECTED_EOS_PLAN = RemediationPlan(AllOf((EXPECTED_EOS_ACTION, EXPECTED_VERIFY_TERMINATTR)))
EXPECTED_COMBINED_PLAN = RemediationPlan(AllOf((EXPECTED_EOS_ACTION, EXPECTED_UPGRADE_TERMINATTR)))
EXPECTED_COMPONENT_ONLY_PLAN = RemediationPlan(
    OperationalAction("Upgrade TerminAttr to a fixed release supported on EOS 4.36.3.2M; confirm compatibility with Arista before selecting the release.")
)
expected_result = partial(build_expected_advisory_result, "CVE-2026-111943")

_DATA: AntaUnitTestData = {
    (SA201, "both-versions-affected"): {
        "version": build_eos_version("4.36.3M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.3M' is affected and TerminAttr 'v1.46.2' is affected.",
            EXPECTED_COMBINED_PLAN,
        ),
    },
    (SA201, "fixed-terminattr-does-not-clear-affected-eos"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": [FIXED_PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because TerminAttr 'v1.46.3' is outside the affected releases and EOS version '4.36.3M' is affected.",
            EXPECTED_EOS_PLAN,
        ),
    },
    (SA201, "fixed-eos-does-not-clear-affected-terminattr"): {
        "version": build_eos_version("4.36.3.2M"),
        "eos_data": [PACKAGE],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.3.2M' is outside the affected releases and TerminAttr 'v1.46.2' is affected.",
            EXPECTED_COMPONENT_ONLY_PLAN,
        ),
    },
    (SA201, "both-versions-outside-affected-releases"): {
        "version": build_eos_version("4.36.3.2M"),
        "eos_data": [FIXED_PACKAGE],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.36.3.2M' is outside the affected releases and TerminAttr 'v1.46.3' is outside the affected releases.",
            None,
        ),
    },
    (SA201, "affected-eos-with-missing-terminattr"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.3M' is affected.",
            EXPECTED_EOS_PLAN,
        ),
    },
    (SA201, "fixed-eos-with-missing-terminattr"): {
        "version": build_eos_version("4.36.3.2M"),
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the TerminAttr version because the 'show version detail' output is incomplete.",
            None,
        ),
    },
}

# Reduced version/package pairs observed through native eAPI collection in the lab.
# Keep original build labels in findings while assessing their numeric releases.
for _name, _eos, _terminattr, _message, _component_action in (
    (
        "lab-affected-cloudeos",
        "4.36.0.1F-cloud",
        "v1.44.0",
        "The device is affected because EOS version '4.36.0.1F-cloud' is affected and TerminAttr 'v1.44.0' is affected.",
        EXPECTED_UPGRADE_TERMINATTR,
    ),
    (
        "lab-affected-eos-with-devel-terminattr",
        "4.32.1F",
        "v1.32.99_devel",
        "The device is affected because EOS version '4.32.1F' is affected and TerminAttr 'v1.32.99_devel' is affected.",
        EXPECTED_UPGRADE_TERMINATTR,
    ),
    (
        "lab-affected-eos-with-rel-terminattr",
        "4.35.0.2F",
        "v1.41.0_quinn.1_rel",
        "The device is affected because EOS version '4.35.0.2F' is affected and TerminAttr 'v1.41.0_quinn.1_rel' is affected.",
        EXPECTED_UPGRADE_TERMINATTR,
    ),
    (
        "lab-fixed-veos",
        "4.37.0F",
        "v1.47.0",
        "The device is not affected because EOS version '4.37.0F' is outside the affected releases and TerminAttr 'v1.47.0' is outside the affected releases.",
        None,
    ),
    (
        "lab-fixed-cloudeos",
        "4.37.0F-cloud",
        "v1.47.0",
        "The device is not affected because EOS version '4.37.0F-cloud' is outside the affected releases and TerminAttr 'v1.47.0' is outside the affected releases.",
        None,
    ),
):
    _plan = (
        RemediationPlan(
            AllOf(
                (
                    ChangeSoftwareVersion(SoftwareTarget.EOS, parse_eos_version(_eos).unwrap(), KnownFixedReleases(EXPECTED_EOS_FIXED_RELEASES)),
                    _component_action,
                )
            )
        )
        if _component_action is not None
        else None
    )
    _DATA[SA201, _name] = {
        "version": build_eos_version(_eos),
        "eos_data": [{"details": {"packages": {"TerminAttr-core": {"version": _terminattr}}}}],
        "expected": expected_result(AntaTestStatus.FAILURE if _plan is not None else AntaTestStatus.SUCCESS, _message, _plan),
    }


def version_fact(version: str | None = "4.36.3.2M") -> Fact[EosVersionFact]:
    """Construct EOS metadata independently of collection."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.1.0F", True),
        ("4.27.99M", True),
        ("4.28.0F", True),
        ("4.28.14M", True),
        ("4.28.14.1M", True),
        ("4.28.15M", True),
        ("4.28.99M", True),
        ("4.29.0F", True),
        ("4.29.99M", True),
        ("4.30.0F", True),
        ("4.30.99M", True),
        ("4.31.0F", True),
        ("4.31.99M", True),
        ("4.32.0F", True),
        ("4.32.99M", True),
        ("4.33.0F", True),
        ("4.33.11M", True),
        ("4.33.11.1M", True),
        ("4.33.11.2M", False),
        ("4.33.11.3M", False),
        ("4.33.12M", False),
        ("4.34.0F", True),
        ("4.34.9M", True),
        ("4.34.9.1M", True),
        ("4.34.9.2M", False),
        ("4.34.9.3M", False),
        ("4.34.10M", False),
        ("4.35.0F", True),
        ("4.35.7M", True),
        ("4.35.7.1M", True),
        ("4.35.7.2M", False),
        ("4.35.7.3M", False),
        ("4.35.8M", False),
        ("4.36.0F", True),
        ("4.36.3M", True),
        ("4.36.3.1M", True),
        ("4.36.3.2M", False),
        ("4.36.3.3M", False),
        ("4.36.4M", False),
        ("4.37.0F", False),
        ("5.0.0F", False),
    ],
)
def test_eos_source_boundaries(version: str, affected: bool) -> None:
    """Check affected trains and the newly published fixed hotfix boundaries."""
    expected = AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED
    assert evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status is expected


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("v0.99.99", True),
        ("v1.0.0", True),
        *((f"v1.{minor}.99", True) for minor in range(31)),
        ("v1.31.0", True),
        ("v1.31.17", True),
        ("v1.31.18", False),
        ("v1.32.99", True),
        ("v1.33.99", True),
        ("v1.34.0", True),
        ("v1.34.14", True),
        ("v1.34.15", False),
        ("v1.35.99", True),
        ("v1.36.99", True),
        ("v1.37.0", True),
        ("v1.37.14", True),
        ("v1.37.15", False),
        ("v1.38.99", True),
        ("v1.39.99", True),
        ("v1.40.0", True),
        ("v1.40.14", True),
        ("v1.40.15", False),
        ("v1.41.99", True),
        ("v1.42.99", True),
        ("v1.43.0", True),
        ("v1.43.10", True),
        ("v1.43.11", False),
        ("v1.44.99", True),
        ("v1.45.99", True),
        ("v1.46.0", True),
        ("v1.46.2", True),
        ("v1.46.3", False),
        ("v1.47.0", False),
        ("v2.0.0", False),
    ],
)
def test_component_source_boundaries(version: str, affected: bool) -> None:
    """Check every component train, including scope boundaries without a published release recommendation."""
    result = _terminattr_version_assessment(TerminAttrVersionFact(version).available(PACKAGE_SOURCE))
    assert isinstance(result, ComponentVersionAssessment)
    assert result.relation is (VersionRelation.AFFECTED if affected else VersionRelation.OUTSIDE_SCOPE)


@pytest.mark.parametrize("suffix", ["_devel", "_quinn.1_rel"])
@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("v1.31.17", True),
        ("v1.31.18", True),
        ("v1.31.19", False),
        ("v1.34.14", True),
        ("v1.34.15", True),
        ("v1.34.16", False),
        ("v1.37.14", True),
        ("v1.37.15", True),
        ("v1.37.16", False),
        ("v1.40.14", True),
        ("v1.40.15", True),
        ("v1.40.16", False),
        ("v1.43.10", True),
        ("v1.43.11", True),
        ("v1.43.12", False),
        ("v1.46.2", True),
        ("v1.46.3", True),
        ("v1.46.4", False),
    ],
)
def test_component_build_labels_preserve_numeric_boundaries(version: str, suffix: str, affected: bool) -> None:
    """A labelled build at the first fixed patch cannot claim the final release's fix."""
    fact = TerminAttrVersionFact(version + suffix).available(PACKAGE_SOURCE)
    result = _terminattr_version_assessment(fact)
    assert isinstance(result, ComponentVersionAssessment)
    assert result.relation is (VersionRelation.AFFECTED if affected else VersionRelation.OUTSIDE_SCOPE)
    assert result.fact == fact


@pytest.mark.parametrize(
    ("version", "status"),
    [
        ("v1.32.99_devel", AdvisoryStatus.AFFECTED),
        ("v1.41.0_quinn.1_rel", AdvisoryStatus.AFFECTED),
        ("v1.46.2_devel", AdvisoryStatus.AFFECTED),
        ("v1.46.3_devel", AdvisoryStatus.AFFECTED),
        ("v1.46.4_devel", AdvisoryStatus.NOT_AFFECTED),
    ],
)
async def test_suffixed_component_on_fixed_eos(version: str, status: AdvisoryStatus) -> None:
    """Exercise suffix parsing where affected EOS cannot mask a component parsing error."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version("4.36.3.2M").unwrap()
    await device.refresh()
    instance = SA201(device=device, eos_data=[{"details": {"packages": {"TerminAttr-core": {"version": version}}}}])
    await instance.test()

    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is status
    assert version in atomic.messages[0]
    assert atomic.remediation == (EXPECTED_COMPONENT_ONLY_PLAN if status is AdvisoryStatus.AFFECTED else None)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("4.26.9M", ("v1.31.18",)),
        ("4.27.0F", ("v1.34.15", "v1.31.18")),
        ("4.27.99M", ("v1.34.15", "v1.31.18")),
        ("4.28.0F", ("v1.37.15", "v1.34.15", "v1.31.18")),
        ("4.29.0F", ("v1.40.15", "v1.37.15", "v1.34.15", "v1.31.18")),
        ("4.29.99M", ("v1.40.15", "v1.37.15", "v1.34.15", "v1.31.18")),
        ("4.30.0F", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15", "v1.34.15", "v1.31.18")),
        ("4.31.10M", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15", "v1.34.15", "v1.31.18")),
        ("4.31.11M", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15", "v1.34.15")),
        ("4.32.11M", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15", "v1.34.15")),
        ("4.32.12M", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15")),
        ("4.33.10M", ("v1.46.3", "v1.43.11", "v1.40.15", "v1.37.15")),
        ("4.33.11M", ("v1.46.3", "v1.43.11", "v1.40.15")),
        ("4.34.8M", ("v1.46.3", "v1.43.11", "v1.40.15")),
        ("4.34.9M", ("v1.46.3", "v1.43.11")),
        ("4.35.7M", ("v1.46.3", "v1.43.11")),
        ("4.35.8M", ("v1.46.3",)),
        ("4.36.3M", ("v1.46.3",)),
        ("4.36.3.2M", ()),
        ("4.37.0F", ()),
    ],
)
def test_component_fix_eos_compatibility(version: str, expected: tuple[str, ...]) -> None:
    """Never suggest an independently fixed TerminAttr release outside its source-supported EOS interval."""
    assert tuple(str(release.version) for release in _compatible_terminattr_fixes(parse_eos_version(version).unwrap())) == expected


@pytest.mark.parametrize("model", ["cEOSLab", "vEOS", "CloudEOS", "DCS-7150S-64", "unknown", None])
async def test_platform_identity_does_not_limit_software_assessment(model: str | None) -> None:
    """Platform metadata cannot exclude an affected software version."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version("4.36.3M").unwrap()
    device.platform = build_eos_platform(model) if model is not None else None
    await device.refresh()
    instance = SA201(device=device, eos_data=[PACKAGE])
    await instance.test()

    assert instance.result.result is AntaTestStatus.FAILURE
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is AdvisoryStatus.AFFECTED


@pytest.mark.parametrize(
    ("eos_version", "component_version", "result_type"),
    [
        ("4.36.3M", "v1.46.2", AffectedResult),
        ("4.28.15M", "v1.31.18", AffectedResult),
        ("4.36.3M", "v1.46.3", AffectedResult),
        ("4.36.3.2M", "v1.46.2", AffectedResult),
        ("4.36.3.2M", "v1.46.3", NotAffectedResult),
        ("4.36.3M", None, AffectedResult),
        (None, "v1.46.2", AffectedResult),
        ("4.36.3.2M", None, ErrorResult),
        (None, "v1.46.3", ErrorResult),
        (None, None, ErrorResult),
    ],
)
def test_version_decision_matrix(eos_version: str | None, component_version: str | None, result_type: type) -> None:
    """Known affected software is decisive; neither missing evidence nor a fixed other component clears it."""
    component = (
        TerminAttrVersionFact(component_version).available(PACKAGE_SOURCE)
        if component_version is not None
        else TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, PACKAGE_SOURCE)
    )
    result = _assess_sa201(version_fact(eos_version), component)
    assert isinstance(result, result_type)


def test_all_required_unavailable_facts_are_retained() -> None:
    """Report both missing versions when neither establishes impact."""
    component = TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, PACKAGE_SOURCE)
    result = _assess_sa201(version_fact(None), component)
    assert isinstance(result, ErrorResult)
    assert result.problems == (version_fact(None), component)


@pytest.mark.parametrize("version", ["1.46.2", "v1.46", "v1.46.2-dev", "v1.46.2_", "v1.46.2_bad label", "v1.46.2_bad/label", "v1.46.2_rel\n", "invalid"])
@pytest.mark.parametrize(("eos_version", "result_type"), [("4.36.3M", AffectedResult), ("4.36.3.2M", ErrorResult)])
def test_invalid_component_version_cannot_clear_affected_eos(version: str, eos_version: str, result_type: type) -> None:
    """Malformed component metadata is an error only when needed to decide impact."""
    result = _assess_sa201(version_fact(eos_version), TerminAttrVersionFact(version).available(PACKAGE_SOURCE))
    assert isinstance(result, result_type)
    if isinstance(result, ErrorResult):
        assert result.problems[0].problem is FactProblemKind.INVALID


@pytest.mark.parametrize("eos_version", ["4.37.0F", "4.36.3.2M", "4.35.7.2M", "4.34.9.2M", "4.33.11.2M"])
@pytest.mark.parametrize(("package", "status"), [(PACKAGE, AdvisoryStatus.AFFECTED), (FIXED_PACKAGE, AdvisoryStatus.NOT_AFFECTED)])
async def test_fixed_eos_still_requires_fixed_terminattr(eos_version: str, package: dict[str, object], status: AdvisoryStatus) -> None:
    """Every published fixed EOS branch still assesses the installed component independently."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version(eos_version).unwrap()
    await device.refresh()
    instance = SA201(device=device, eos_data=[package])
    await instance.test()
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is status


@pytest.mark.parametrize("eos_version", ["4.36.3M", "4.36.3.2M"])
@pytest.mark.parametrize("errors", [["Permission denied"], ["This command is not supported on this hardware platform"]])
async def test_component_collection_failure_does_not_soften_affected_eos(eos_version: str, errors: list[str]) -> None:
    """A failed component command cannot turn established EOS impact into Error."""
    device = OfflineAntaDevice("test")
    device.version = parse_eos_version(eos_version).unwrap()
    await device.refresh()
    instance = SA201(device=device, eos_data=[PACKAGE])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is (AdvisoryStatus.AFFECTED if eos_version == "4.36.3M" else AdvisoryStatus.ERROR)
    if eos_version == "4.36.3M":
        assert atomic.remediation == EXPECTED_EOS_PLAN


def test_combined_upgrade_does_not_recommend_a_component_for_the_old_eos() -> None:
    """An EOS 4.28 upgrade must not pin TA 1.37.15, unsupported on the recommended fixed EOS releases."""
    result = _assess_sa201(version_fact("4.28.14M"), TerminAttrVersionFact("v1.37.14").available(PACKAGE_SOURCE))
    assert isinstance(result, AffectedResult)
    resolution = result.remediation.resolution
    assert isinstance(resolution, AllOf)
    assert resolution.items[1] == EXPECTED_UPGRADE_TERMINATTR


def test_source_metadata_and_command_contract() -> None:
    """Collect only the installed TerminAttr version, never client configuration."""
    assert ADVISORY.sa_number == "0201"
    assert ADVISORY.last_updated == date(2026, 11, 4)
    assert tuple(vulnerability.id for vulnerability in ADVISORY.vulnerabilities) == ("CVE-2026-111943",)
    assert ADVISORY.vulnerabilities[0].severity is _AdvisoryVulnerabilitySeverity.CRITICAL
    assert FIXED_RELEASES == EXPECTED_EOS_FIXED_RELEASES
    assert len(SA201.commands) == 1
    command = SA201.commands[0]
    assert isinstance(command, AntaCommand)
    assert (command.command, command.ofmt, command.revision) == ("show version detail", "json", 1)


@pytest.mark.parametrize(
    ("name", "status"),
    [
        ("both-versions-affected", AdvisoryStatus.AFFECTED),
        ("both-versions-outside-affected-releases", AdvisoryStatus.NOT_AFFECTED),
        ("fixed-eos-with-missing-terminattr", AdvisoryStatus.ERROR),
    ],
)
async def test_exact_end_to_end_finding(name: str, status: AdvisoryStatus) -> None:
    """Check exact reporter prose and private semantic fields omitted by the generic harness."""
    case = _DATA[SA201, name]
    device = OfflineAntaDevice("test")
    device.version = case.get("version")
    device.platform = case.get("platform")
    await device.refresh()
    instance = SA201(device=device, eos_data=case["eos_data"])
    await instance.test()

    expected_messages = case["expected"].get("messages", [])
    assert instance.result.messages == [f"Verify CVE-2026-111943. - {message}" for message in expected_messages]
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert _get_atomic_vulnerability_ids(atomic) == ("CVE-2026-111943",)
    assert atomic.messages == expected_messages
    assert atomic.advisory_status is status
