# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Independent source, assessment, and projection contracts for SA229."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management_queues import ManagementSingleQueueBootFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind, FeatureState
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, NotAffectedResult
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import ChangeSoftwareVersion, NextPublishedFixedRelease, RemediationPlan, SoftwareTarget
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._advisory.status import AdvisoryStatus
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories import _ADVISORY_TESTS, get_catalog
from anta.tests.advisories.sa_229 import ADVISORY, AFFECTED_PLATFORM_FAMILIES, AFFECTED_VERSION_MATRIX, FIXED_RELEASES, SA229, _assess_sa229
from tests.units.anta_tests import (
    build_eos_platform,
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, eos_version_fact
from tests.units.anta_tests.advisories.sa229_data import BOOT_ABSENT, BOOT_ENABLED, BOOT_REQUOTED

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
BOOT_SOURCE = FactSource("show event-handler", FactSourceKind.COMMAND)
BOOT_INACTIVE = ManagementSingleQueueBootFact(FeatureState.DISABLED).available(BOOT_SOURCE)
EXPECTED_REMEDIATION = RemediationPlan(ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 35, 6, suffix="M"), NextPublishedFixedRelease()))
expected = partial(build_expected_advisory_result, "CVE-2026-99288")

_DATA: AntaUnitTestData = {
    (SA229, "affected-with-requoted-boot-action"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280SR3M-48YC8-F"),
        "eos_data": [BOOT_REQUOTED],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because platform 'DCS-7280SR3M-48YC8-F' is within the affected platform scope and EOS version '4.35.6M' is affected.",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA229, "affected-without-boot-control"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [BOOT_ABSENT],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because platform 'vEOS-lab' is within the affected platform scope and EOS version '4.35.6M' is affected.",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA229, "excluded-software-without-platform"): {
        "version": build_eos_version("4.21.2.99F"),
        "platform": None,
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.21.2.99F' is outside the affected releases.", None),
    },
    (SA229, "cloudeos-without-version"): {
        "version": None,
        "platform": build_eos_platform("CloudEOS"),
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'CloudEOS' is outside the affected platform scope.", None),
    },
    (SA229, "awe-with-affected-version"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("AWE-7200R"),
        "eos_data": [{}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'AWE-7200R' is outside the affected platform scope.", None),
    },
    (SA229, "both-scope-facts-missing"): {
        "version": None,
        "platform": None,
        "eos_data": [BOOT_ABSENT],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata. "
            "The test could not determine the platform identity because it is missing from device metadata.",
            None,
        ),
    },
    (SA229, "unknown-platform"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("UNRECOGNIZED"),
        "eos_data": [BOOT_ABSENT],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the platform identity because device metadata is invalid.", None),
    },
    (SA229, "inconclusive-recognized-boot-control"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280SR3M-48YC8-F"),
        "eos_data": [BOOT_ENABLED],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.35.6M' is affected, "
            "platform 'DCS-7280SR3M-48YC8-F' is within the affected platform scope, and the interface management single-receive-queue boot control is enabled. "
            "Unresolved: effective receive-channel coverage within the supported non-Bash observation contract is device state not exposed.",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA229, "error-required-handler-output-missing"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7280SR3M-48YC8-F"),
        "eos_data": [{}],
        "expected": expected(
            AntaTestStatus.ERROR, "The test could not determine the single-receive-queue boot action because the 'show event-handler' output is incomplete.", None
        ),
    },
}


def platform_fact(model: str | None) -> Fact[PlatformIdentityFact]:
    """Construct normalized platform evidence using the repository parser."""
    if model is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    identity = build_eos_platform(model)
    assert identity is not None
    return PlatformIdentityFact.from_identity(identity).available(SOURCE)


def test_version_boundaries() -> None:
    """Preserve the introduction boundary and every unfixed train independently."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.20.99M", AffectedStatus.NOT_AFFECTED),
            ("4.21.0F", AffectedStatus.NOT_AFFECTED),
            ("4.21.2F", AffectedStatus.NOT_AFFECTED),
            ("4.21.2.99F", AffectedStatus.NOT_AFFECTED),
            ("4.21.3F", AffectedStatus.AFFECTED),
            ("4.21.3.1F", AffectedStatus.AFFECTED),
            ("4.21.99M", AffectedStatus.AFFECTED),
            ("4.22.0F", AffectedStatus.AFFECTED),
            ("4.23.0F", AffectedStatus.AFFECTED),
            ("4.24.0F", AffectedStatus.AFFECTED),
            ("4.25.0F", AffectedStatus.AFFECTED),
            ("4.26.0F", AffectedStatus.AFFECTED),
            ("4.27.0F", AffectedStatus.AFFECTED),
            ("4.28.0F", AffectedStatus.AFFECTED),
            ("4.29.0F", AffectedStatus.AFFECTED),
            ("4.30.0F", AffectedStatus.AFFECTED),
            ("4.31.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.11M", AffectedStatus.AFFECTED),
            ("4.33.11.1M", AffectedStatus.AFFECTED),
            ("4.33.11.2M", AffectedStatus.AFFECTED),
            ("4.33.11.3M", AffectedStatus.AFFECTED),
            ("4.33.12M", AffectedStatus.AFFECTED),
            ("4.34.0F", AffectedStatus.AFFECTED),
            ("4.34.9M", AffectedStatus.AFFECTED),
            ("4.34.9.1M", AffectedStatus.AFFECTED),
            ("4.34.9.2M", AffectedStatus.AFFECTED),
            ("4.34.9.3M", AffectedStatus.AFFECTED),
            ("4.34.10M", AffectedStatus.AFFECTED),
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.AFFECTED),
            ("4.35.7.1M", AffectedStatus.AFFECTED),
            ("4.35.7.2M", AffectedStatus.AFFECTED),
            ("4.35.7.3M", AffectedStatus.AFFECTED),
            ("4.35.8M", AffectedStatus.AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.3M", AffectedStatus.AFFECTED),
            ("4.36.3.1M", AffectedStatus.AFFECTED),
            ("4.36.3.2M", AffectedStatus.AFFECTED),
            ("4.36.3.3M", AffectedStatus.AFFECTED),
            ("4.36.4M", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.AFFECTED),
            ("4.37.0.1F", AffectedStatus.AFFECTED),
            ("4.37.1F", AffectedStatus.AFFECTED),
            ("4.37.99M", AffectedStatus.AFFECTED),
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("5.0.0F", AffectedStatus.NOT_AFFECTED),
        ),
    )


@pytest.mark.parametrize("model", ["CloudEOS", "AWE-5000", "AWE-7200R"])
def test_excluded_platform_short_circuits_unavailable_version(model: str) -> None:
    """Each excluded product establishes safety independently of version collection."""
    finding = _assess_sa229(EosVersionFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE), platform_fact(model), BOOT_INACTIVE)
    assert isinstance(finding, NotAffectedResult)
    assert finding.vulnerability_id == "CVE-2026-99288"
    assert len(finding.decisive) == 1


@pytest.mark.parametrize("version", ["4.21.2.99F", "4.38.0F", "5.0.0F"])
def test_excluded_software_short_circuits_unavailable_platform(version: str) -> None:
    """Software exclusion is decisive even when platform evidence is unavailable."""
    assert isinstance(_assess_sa229(eos_version_fact(version), platform_fact(None), BOOT_INACTIVE), NotAffectedResult)


@pytest.mark.parametrize("problem", list(FactProblemKind))
@pytest.mark.parametrize("missing", [(0,), (1,), (0, 1)])
def test_all_required_unavailable_facts_are_retained(problem: FactProblemKind, missing: tuple[int, ...]) -> None:
    """Preserve every required problem and its source without claiming device safety."""
    versions = (eos_version_fact("4.35.6M").value, eos_version_fact("4.38.0F").value) if problem is FactProblemKind.CONTRADICTORY else ()
    platforms = (
        tuple(
            PlatformIdentityFact(model=family.value, type=PlatformType.VIRTUAL, modules=(), platform_families=frozenset({family}))
            for family in (PlatformFamily.VEOS_LAB, PlatformFamily.CLOUDEOS)
        )
        if problem is FactProblemKind.CONTRADICTORY
        else ()
    )
    version = EosVersionFact.unavailable(problem, SOURCE, observations=versions) if 0 in missing else eos_version_fact("4.35.6M")
    platform = PlatformIdentityFact.unavailable(problem, SOURCE, observations=platforms) if 1 in missing else platform_fact("vEOS-lab")
    finding = _assess_sa229(version, platform, BOOT_INACTIVE)
    assert isinstance(finding, ErrorResult)
    assert tuple(item.definition for item in finding.problems) == tuple((EosVersionFact, PlatformIdentityFact)[i] for i in missing)
    assert all(item.problem is problem and item.source == SOURCE for item in finding.problems)
    assert tuple(item.observations for item in finding.problems) == tuple((versions, platforms)[i] for i in missing)


@pytest.mark.parametrize("model", ["UNRECOGNIZED", "DCS-7508N"])
def test_unknown_or_incomplete_platform_is_error(model: str) -> None:
    """Unknown or incomplete identity cannot establish platform scope."""
    finding = _assess_sa229(eos_version_fact("4.35.6M"), platform_fact(model), BOOT_INACTIVE)
    assert isinstance(finding, ErrorResult)
    assert tuple((item.definition, item.problem) for item in finding.problems) == ((PlatformIdentityFact, FactProblemKind.INVALID),)


@pytest.mark.parametrize("model", ["DCS-7150S-24", "DCS-7160-48YC6", "DCS-7050SX2-72Q"])
def test_known_unlisted_platforms_are_outside_scope(model: str) -> None:
    """Do not extend the published platform list to every recognized EOS family."""
    finding = _assess_sa229(EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE), platform_fact(model), BOOT_INACTIVE)
    assert isinstance(finding, NotAffectedResult)


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
        PlatformFamily.ZTX_7200,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CVX,
    ],
)
def test_affected_platform_families(family: PlatformFamily) -> None:
    """Exercise each published affected EOS family supported by platform classification."""
    platform = PlatformIdentityFact(model=family.value, type=PlatformType.FIXED, modules=(), platform_families=frozenset({family})).available(SOURCE)
    finding = _assess_sa229(eos_version_fact("4.35.6M"), platform, BOOT_INACTIVE)
    assert isinstance(finding, AffectedResult)
    assert finding.remediation == EXPECTED_REMEDIATION
    assert finding.vulnerability_id == "CVE-2026-99288"


@pytest.mark.parametrize("model", ["cEOSLab", "vEOS-lab", "vEOS"])
def test_virtual_platform_models_remain_affected(model: str) -> None:
    """Exclude CloudEOS specifically rather than excluding all virtual devices."""
    assert isinstance(_assess_sa229(eos_version_fact("4.35.6M"), platform_fact(model), BOOT_INACTIVE), AffectedResult)


def test_7060xe7_series_prefix_is_affected() -> None:
    """The published XE7 series prefix is recognized by the existing 7060X classifier."""
    # This is a synthetic series-prefix input, not a captured device SKU.
    identity = build_eos_platform("DCS-7060XE7")
    assert identity is not None
    assert identity.type is PlatformType.FIXED
    assert identity.platform_families == {PlatformFamily.SERIES_7060_X}
    finding = _assess_sa229(eos_version_fact("4.35.6M"), PlatformIdentityFact.from_identity(identity).available(SOURCE), BOOT_INACTIVE)
    assert isinstance(finding, AffectedResult)


def test_modular_platform_with_complete_inventory_is_affected() -> None:
    """An affected linecard family identifies a modular device in scope."""
    identity = build_eos_platform("DCS-7508N", {"modules": {"Linecard1": {"modelName": "DCS-7500R3-48YCQ-LC"}}})
    assert identity is not None
    finding = _assess_sa229(eos_version_fact("4.35.6M"), PlatformIdentityFact.from_identity(identity).available(SOURCE), BOOT_INACTIVE)
    assert isinstance(finding, AffectedResult)


@pytest.mark.parametrize("case_name", [name for _, name in _DATA])
async def test_exact_atomic_results(device: AntaDevice, case_name: str) -> None:
    """Check exact diagnostics, remediation, semantic status, and single-CVE attribution."""
    case = _DATA[(SA229, case_name)]
    device.version = case.get("version")
    device.platform = case.get("platform")
    instance = SA229(device=device, eos_data=case["eos_data"])
    await instance.test()
    assert instance.result.result is case["expected"]["result"]
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-99288",)
    expected_result = case["expected"]
    assert "messages" in expected_result
    assert atomic.messages == expected_result["messages"]
    plans = case["expected"].get("remediations", [])
    assert atomic.remediation == (plans[0] if plans else None)
    expected_semantic = (
        AdvisoryStatus.INCONCLUSIVE
        if case_name.startswith("inconclusive-")
        else {
            AntaTestStatus.FAILURE: AdvisoryStatus.AFFECTED,
            AntaTestStatus.SUCCESS: AdvisoryStatus.NOT_AFFECTED,
            AntaTestStatus.ERROR: AdvisoryStatus.ERROR,
        }[case["expected"]["result"]]
    )
    assert atomic.advisory_status is expected_semantic


def test_metadata_and_registration() -> None:
    """Register the published revision and CVE without inventing fixed releases."""
    assert ADVISORY.sa_number == "0229"
    assert ADVISORY.title == "Security Advisory 0229"
    assert ADVISORY.last_updated == date(2026, 11, 24)
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25220-security-advisory-0229"
    assert tuple((item.id, item.severity) for item in ADVISORY.vulnerabilities) == (("CVE-2026-99288", _AdvisoryVulnerabilitySeverity.HIGH),)
    assert FIXED_RELEASES == ()
    assert not AFFECTED_PLATFORM_FAMILIES & {PlatformFamily.CLOUDEOS, PlatformFamily.AWE_5000, PlatformFamily.AWE_7200_R}
    assert SA229 in _ADVISORY_TESTS
    assert any(definition.test is SA229 for definition in get_catalog().tests)
    assert len(SA229.commands) == 1
    (command,) = SA229.commands
    assert isinstance(command, AntaCommand)
    assert command.command == "show event-handler"
    assert command.revision == 1
    assert command.ofmt == "json"


@pytest.mark.parametrize(
    ("state", "result_type"), [(FeatureState.ENABLED, InconclusiveResult), (FeatureState.DISABLED, AffectedResult), (FeatureState.UNSUPPORTED, ErrorResult)]
)
def test_boot_control_result(state: FeatureState, result_type: type) -> None:
    """Only configured control presence is observed; effectiveness is never inferred."""
    boot = ManagementSingleQueueBootFact(state).available(BOOT_SOURCE)
    finding = _assess_sa229(eos_version_fact("4.35.6M"), platform_fact("DCS-7280SR3M-48YC8-F"), boot)
    assert isinstance(finding, result_type)
    if isinstance(finding, InconclusiveResult):
        assert finding.remediation == EXPECTED_REMEDIATION
        assert len(finding.unresolved) == 1
        assert "non-Bash observation contract" in finding.unresolved[0].subject


def test_all_three_required_problems_are_retained() -> None:
    """Unavailable native evidence remains Error alongside missing scope metadata."""
    finding = _assess_sa229(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        platform_fact(None),
        ManagementSingleQueueBootFact.unavailable(FactProblemKind.MALFORMED, BOOT_SOURCE),
    )
    assert isinstance(finding, ErrorResult)
    assert tuple(item.definition for item in finding.problems) == (EosVersionFact, PlatformIdentityFact, ManagementSingleQueueBootFact)
    assert tuple(item.source for item in finding.problems) == (SOURCE, SOURCE, BOOT_SOURCE)


@pytest.mark.parametrize("exclude_by", ["software", "platform"])
def test_scope_exclusion_ignores_unavailable_boot_control(exclude_by: str) -> None:
    """Independently excluded scope does not require the native handler observation."""
    finding = _assess_sa229(
        eos_version_fact("4.38.0F" if exclude_by == "software" else "4.35.6M"),
        platform_fact(None if exclude_by == "software" else "CloudEOS"),
        ManagementSingleQueueBootFact.unavailable(FactProblemKind.COLLECTION_FAILED, BOOT_SOURCE),
    )
    assert isinstance(finding, NotAffectedResult)


@pytest.mark.parametrize(
    ("errors", "reason"), [(["permission denied"], "could not be collected"), (["This command is not supported on this hardware platform"], "is not supported")]
)
async def test_native_command_failure_is_error_not_inconclusive(errors: list[str], reason: str) -> None:
    """Permission and support failures of the required show command do not soften the result."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280SR3M-48YC8-F")
    await device.refresh()
    instance = SA229(device=device, eos_data=[BOOT_ENABLED])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = errors
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.ERROR
    assert len(instance.result.atomic_results) == 1
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.vulnerability_ids == ("CVE-2026-99288",)
    assert atomic.advisory_status is AdvisoryStatus.ERROR
    assert atomic.messages == [f"The test could not determine the single-receive-queue boot action because 'show event-handler' {reason}."]
    assert atomic.remediation is None


async def test_scope_exclusion_survives_actual_optional_command_failure() -> None:
    """A failed show command cannot mask independently excluded software."""
    device = OfflineAntaDevice("unit-test")
    device.version = build_eos_version("4.38.0F")
    await device.refresh()
    instance = SA229(device=device, eos_data=[{}])
    instance.instance_commands[0].output = None
    instance.instance_commands[0].errors = ["permission denied"]
    instance.collect = AsyncMock()
    await instance.test()
    assert instance.result.result is AntaTestStatus.SUCCESS
    assert instance.result.atomic_results[0].messages == ["The device is not affected because EOS version '4.38.0F' is outside the affected releases."]


async def test_account_allowed_only_native_show_never_receives_bash() -> None:
    """The real collection path works with a one-command allowlist."""

    class NativeShowOnlyDevice(OfflineAntaDevice):
        """Reject any attempted collection beyond the single native show command."""

        async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
            """Return the captured handler only for the explicitly allowed command."""
            _ = collection_id
            assert command.command == "show event-handler"
            command.output = BOOT_ENABLED

    device = NativeShowOnlyDevice("native-show-only")
    device.version = build_eos_version("4.35.6M")
    device.platform = build_eos_platform("DCS-7280SR3M-48YC8-F")
    await device.refresh()
    instance = SA229(device=device)
    await instance.test()
    assert instance.result.result is AntaTestStatus.FAILURE
    atomic = instance.result.atomic_results[0]
    assert isinstance(atomic, _AdvisoryAtomicTestResult)
    assert atomic.advisory_status is AdvisoryStatus.INCONCLUSIVE
    assert [command.command for command in instance.instance_commands] == ["show event-handler"]
