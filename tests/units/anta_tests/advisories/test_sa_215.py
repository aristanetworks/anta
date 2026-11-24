# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 215."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING, Any

import pytest

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.dot1x import Dot1xControlledAuthenticatorInterfacesFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import FactProblemKind, FactSource, FactSourceKind
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, PlatformAssessment, PlatformRelation
from anta._advisory.models import _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.models import AntaCommand
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_215 import ADVISORY, AFFECTED_VERSION_MATRIX, SA215, _assess_sa215
from tests.units.anta_tests import build_eos_platform, build_eos_version, test  # noqa: F401 - Generic advisory test collection.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result
from tests.units.anta_tests.advisories.dot1x_outputs import dot1x_all, dot1x_interface
from tests.units.anta_tests.advisories.fact_builders import SOURCE, assert_version_statuses, eos_version_fact

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact
    from tests.units.anta_tests import AntaUnitTestData

VULNERABILITY_ID = "CVE-2026-120983"
AFFECTED_PLATFORM = "DCS-7050CX3-32S"
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
expected_result = partial(build_expected_advisory_result, VULNERABILITY_ID)


def authenticator_fact(interfaces: object, *, system_control: bool = True) -> Fact[Dot1xControlledAuthenticatorInterfacesFact]:
    """Use the existing controlled inventory to normalize effective authenticator evidence."""
    command = Dot1xControlledAuthenticatorInterfacesFact.commands[0].model_copy(
        update={"output": dot1x_all(interfaces=interfaces, system_auth_control=system_control)}
    )
    return Dot1xControlledAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))


def platform_fact(model: str | None, modules: dict[str, Any] | None = None) -> Fact[PlatformIdentityFact]:
    """Build platform identity for direct assessment tests."""
    platform = build_eos_platform(model, modules)
    if platform is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return PlatformIdentityFact.from_identity(platform).available(SOURCE)


def module(slot: str, model: str) -> dict[str, Any]:
    """Return `show module` output with one card."""
    return {"modules": {slot: {"modelName": model}}}


def test_sa215_version_boundaries() -> None:
    """Cover the published fixes, including 4.37.0F, and keep unfixed older trains open-ended."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.38.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.1F", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.37.0.1F", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.1.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.5.99M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.9.1M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.0F", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.5M", AffectedStatus.AFFECTED),
            ("4.22.1F", AffectedStatus.AFFECTED),
        ),
    )


@pytest.mark.parametrize(
    ("model", "modules", "relation"),
    [
        pytest.param("CCS-710P-16P", None, PlatformRelation.AFFECTED, id="710"),
        pytest.param("CCS-720DF-48Y", None, PlatformRelation.AFFECTED, id="720D"),
        pytest.param("CCS-720XDM-48ZC2-F", None, PlatformRelation.AFFECTED, id="720XDM-in-720D"),
        pytest.param("CCS-720XP-48ZC2", None, PlatformRelation.AFFECTED, id="720XP"),
        pytest.param("CCS-722XPM-48TH-6SY-F", None, PlatformRelation.AFFECTED, id="722XPM"),
        pytest.param("DCS-7010TX-48", None, PlatformRelation.AFFECTED, id="7010TX"),
        pytest.param("DCS-7328-F", module("Linecard3", "7320X-32C-LC"), PlatformRelation.AFFECTED, id="7320X"),
        pytest.param("DCS-7060CX-32S", None, PlatformRelation.AFFECTED, id="7060X"),
        pytest.param("DCS-7060XE7", None, PlatformRelation.AFFECTED, id="7060XE7"),
        pytest.param("DCS-7060CX2-32S", None, PlatformRelation.AFFECTED, id="7060X2"),
        pytest.param("DCS-7060DX4-32", None, PlatformRelation.AFFECTED, id="7060X4"),
        pytest.param("DCS-7060DX5-64S", None, PlatformRelation.AFFECTED, id="7060X5"),
        pytest.param("DCS-7060X6-64PE", None, PlatformRelation.AFFECTED, id="7060X6"),
        pytest.param("DCS-7260CX-64", None, PlatformRelation.AFFECTED, id="7260X"),
        pytest.param("DCS-7260CX3-64", None, PlatformRelation.AFFECTED, id="7260X3"),
        pytest.param("DCS-7308", module("Linecard3", "7300X-32Q-LC"), PlatformRelation.AFFECTED, id="7300X"),
        pytest.param("DCS-7308X3", module("Linecard3", "7300X3-48YC4-LC"), PlatformRelation.AFFECTED, id="7300X3"),
        pytest.param("DCS-7050CX3-32S", None, PlatformRelation.AFFECTED, id="7050X3"),
        pytest.param("DCS-7050CX4-40D", None, PlatformRelation.AFFECTED, id="7050X4"),
        pytest.param("CCS-755-CH", module("Linecard3", "CCS-750X-48ZXP-LC"), PlatformRelation.AFFECTED, id="750X"),
        pytest.param("DCS-7250QX-64", None, PlatformRelation.AFFECTED, id="7250X"),
        pytest.param("DCS-7358-CH", module("Switchcard1", "7358X4-SC"), PlatformRelation.AFFECTED, id="7358X4"),
        pytest.param("DCS-7368-CH", module("Switchcard1", "7368X4-SC"), PlatformRelation.AFFECTED, id="7368X4"),
        pytest.param("DCS-7388-CH", module("Switchcard1", "7388X5-SC"), PlatformRelation.AFFECTED, id="7388X5"),
        pytest.param("DCS-7289-CH", module("Switchcard1", "7289R3A-SC"), PlatformRelation.OUTSIDE_SCOPE, id="not-listed-7289R3A"),
        pytest.param("DCS-DS-7720R4-128PE", None, PlatformRelation.OUTSIDE_SCOPE, id="not-listed-7720R4"),
        pytest.param("DCS-7280SE-64", None, PlatformRelation.OUTSIDE_SCOPE, id="not-listed-7280E"),
        pytest.param("DCS-7020SR-32C2", None, PlatformRelation.OUTSIDE_SCOPE, id="7020R"),
        pytest.param("DCS-7020R4-10QC-4DF", None, PlatformRelation.OUTSIDE_SCOPE, id="7020R4"),
        pytest.param("DCS-7130L-48", None, PlatformRelation.OUTSIDE_SCOPE, id="7130"),
        pytest.param("DCS-7170B-64C", None, PlatformRelation.OUTSIDE_SCOPE, id="7170"),
        pytest.param("DCS-7280SR-48C6", None, PlatformRelation.OUTSIDE_SCOPE, id="7280R"),
        pytest.param("DCS-7280CR2-60", None, PlatformRelation.OUTSIDE_SCOPE, id="7280R2"),
        pytest.param("DCS-7280CR3-32P4", None, PlatformRelation.OUTSIDE_SCOPE, id="7280R3"),
        pytest.param("DCS-7280R4-32QF-32DF-F", None, PlatformRelation.OUTSIDE_SCOPE, id="7280R4"),
        pytest.param("DCS-7504N", module("Linecard3", "7500E-36Q-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7500E"),
        pytest.param("DCS-7504N", module("Linecard3", "7500R-36CQ-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7500R"),
        pytest.param("DCS-7504N", module("Linecard3", "7500R2-36CQ-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7500R2"),
        pytest.param("DCS-7504N", module("Linecard3", "7500R3-36CQ-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7500R3"),
        pytest.param("DCS-7804-CH", module("Linecard3", "7800R3-36P-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7800R3"),
        pytest.param("DCS-7804-CH", module("Linecard3", "7800R4-36PE-LC"), PlatformRelation.OUTSIDE_SCOPE, id="7800R4"),
        pytest.param("DCS-DL-7700R4C-38PE-B", None, PlatformRelation.OUTSIDE_SCOPE, id="7700R4"),
        pytest.param("AWE-5310", None, PlatformRelation.OUTSIDE_SCOPE, id="AWE-5000"),
        pytest.param("AWE-7220RP-5TH-2S", None, PlatformRelation.OUTSIDE_SCOPE, id="AWE-7200R"),
        pytest.param("ZTX-7230S-4TX-4S-F", None, PlatformRelation.OUTSIDE_SCOPE, id="ZTX-7200"),
        pytest.param("CloudEOS", None, PlatformRelation.OUTSIDE_SCOPE, id="CloudEOS"),
        pytest.param("cEOSLab", None, PlatformRelation.OUTSIDE_SCOPE, id="cEOS-lab"),
        pytest.param("vEOS-lab", None, PlatformRelation.OUTSIDE_SCOPE, id="vEOS-lab"),
        pytest.param("vEOS", None, PlatformRelation.OUTSIDE_SCOPE, id="CVX"),
    ],
)
def test_sa215_platform_scope(model: str, modules: dict[str, Any] | None, relation: PlatformRelation) -> None:
    """Assess only the explicitly listed affected platform families."""
    finding = _assess_sa215(eos_version_fact("4.36.1F"), platform_fact(model, modules), authenticator_fact({"Ethernet3": dot1x_interface("controlled")}))

    if relation is PlatformRelation.AFFECTED:
        assert isinstance(finding, AffectedResult)
        platform_assessment = finding.context[1]
    else:
        assert isinstance(finding, NotAffectedResult)
        platform_assessment = finding.decisive[0]
    assert isinstance(platform_assessment, PlatformAssessment)
    assert platform_assessment.relation is relation


@pytest.mark.parametrize("model", ["unknown-platform", "DCS-7289-CH", "DCS-7308"])
def test_unresolved_platform_identity_remains_an_error(model: str) -> None:
    """Unknown models and chassis without component identity cannot establish platform scope."""
    result = _assess_sa215(eos_version_fact("4.36.1F"), platform_fact(model), authenticator_fact({"Ethernet3": dot1x_interface("controlled")}))
    assert isinstance(result, ErrorResult)


def test_sa215_metadata_and_commands() -> None:
    """Keep assigned identity and collect only the existing controlled authenticator command."""
    assert ADVISORY.url == "https://www.arista.com/en/support/advisories-notices/security-advisory/25037-security-advisory-0215"
    assert ADVISORY.sa_number == "0215"
    assert ADVISORY.title == "Security Advisory 0215"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.vulnerabilities[0].id == VULNERABILITY_ID
    assert ADVISORY.vulnerabilities[0].severity is _AdvisoryVulnerabilitySeverity.HIGH
    commands = [(command.command, command.revision, command.ofmt) for command in SA215.commands if isinstance(command, AntaCommand)]
    assert commands == [("show dot1x all", 1, "json")]


@pytest.mark.parametrize("mode", ["controlled", "forceAuth", "forceUnauth"])
@pytest.mark.parametrize("system_control", [False, True])
@pytest.mark.parametrize("host_mode", [None, "singleHost", "multiHost", "authAllHost"])
def test_only_controlled_authenticator_qualifies(mode: str, system_control: bool, host_mode: object) -> None:
    """Only enabled global control plus auto qualifies, independently of host mode."""
    auth = authenticator_fact({"Ethernet3": {"portControl": mode, "hostMode": host_mode}}, system_control=system_control)
    result = _assess_sa215(eos_version_fact("4.36.1F"), platform_fact(AFFECTED_PLATFORM), auth)
    assert isinstance(result, AffectedResult if system_control and mode == "controlled" else NotAffectedResult)
    if isinstance(result, AffectedResult):
        assert result.remediation == REMEDIATION


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("positive", [False, True])
@pytest.mark.parametrize("name", ["Ethernet2", ""])
def test_partial_authenticator_evidence_preserves_presence_or_required_uncertainty(reverse: bool, positive: bool, name: str) -> None:
    """A valid auto port wins in either order; otherwise incomplete coverage remains Error."""
    records: list[tuple[str, object]] = [(name, None)]
    if positive:
        records.append(("Ethernet3", dot1x_interface("controlled")))
    interfaces = dict(reversed(records) if reverse else records)
    result = _assess_sa215(eos_version_fact("4.36.1F"), platform_fact(AFFECTED_PLATFORM), authenticator_fact(interfaces))
    assert isinstance(result, AffectedResult if positive else ErrorResult)


@pytest.mark.parametrize("interfaces", [{}, {"Ethernet3": dot1x_interface("forceAuth")}, {"Ethernet3": dot1x_interface("forceUnauth")}])
def test_no_auto_authenticators_establishes_absence(interfaces: object) -> None:
    """An empty or entirely forced inventory excludes the required controlled state."""
    assert isinstance(_assess_sa215(eos_version_fact("4.36.1F"), platform_fact(AFFECTED_PLATFORM), authenticator_fact(interfaces)), NotAffectedResult)


@pytest.mark.parametrize("decisive", ["software", "platform", "disabled-global-control", "no-ports"])
def test_independent_exclusions_override_unavailable_inputs(decisive: str) -> None:
    """A proven absent prerequisite can close the screen despite unrelated failures."""
    version = eos_version_fact("4.37.0F") if decisive == "software" else EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = platform_fact("vEOS-lab") if decisive == "platform" else PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    if decisive == "disabled-global-control":
        auth = authenticator_fact(None, system_control=False)
    elif decisive == "no-ports":
        auth = authenticator_fact({})
    else:
        auth = Dot1xControlledAuthenticatorInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE)
    assert isinstance(_assess_sa215(version, platform, auth), NotAffectedResult)


def test_all_required_failures_are_retained() -> None:
    """Without a positive or independent exclusion, retain every unavailable required source."""
    result = _assess_sa215(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        Dot1xControlledAuthenticatorInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show dot1x all", FactSourceKind.COMMAND)),
    )
    assert isinstance(result, ErrorResult)
    assert len(result.problems) == 3
    assert {problem.source.name for problem in result.problems} == {SOURCE.name, "show dot1x all"}


def test_command_errors_are_deferred_for_independent_scope_exclusions() -> None:
    """A collection failure reaches the advisory so fixed software can still establish safety."""
    instance = SA215(OfflineAntaDevice("unit-test"))
    command = instance.instance_commands[0]
    command.errors = ["transport failure"]
    assert instance.failed_commands == []
    auth = Dot1xControlledAuthenticatorInterfacesFact.derive(instance.device, (command,))
    assert isinstance(_assess_sa215(eos_version_fact("4.36.1F"), platform_fact(AFFECTED_PLATFORM), auth), ErrorResult)
    assert isinstance(_assess_sa215(eos_version_fact("4.37.0F"), platform_fact(AFFECTED_PLATFORM), auth), NotAffectedResult)


_DATA: AntaUnitTestData = {
    (SA215, "affected-controlled-authenticator"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform(AFFECTED_PLATFORM),
        "eos_data": [dot1x_all(interfaces={"Ethernet3": dot1x_interface("controlled")})],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                "The device is affected because EOS version '4.36.1F' is affected, platform "
                "'DCS-7050CX3-32S' is within the affected platform scope, and the 802.1X "
                "controlled authenticator configuration is configured."
            ),
            REMEDIATION,
        ),
    },
    (SA215, "not-affected-disabled-global-control"): {
        "version": None,
        "platform": None,
        "eos_data": [dot1x_all(interfaces={"Ethernet3": dot1x_interface("controlled")}, system_auth_control=False)],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the 802.1X controlled authenticator configuration is not configured.",
            None,
        ),
    },
    (SA215, "not-affected-no-authenticator-including-supplicant-only"): {
        "version": None,
        "platform": None,
        "eos_data": [dot1x_all()],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the 802.1X controlled authenticator configuration is not configured.",
            None,
        ),
    },
    (SA215, "not-affected-fixed-437-release"): {
        "version": build_eos_version("4.37.0F"),
        "platform": build_eos_platform(AFFECTED_PLATFORM),
        "eos_data": [dot1x_all(interfaces={"Ethernet3": dot1x_interface("controlled")})],
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA215, "error-missing-global-control"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform(AFFECTED_PLATFORM),
        "eos_data": [{"interfaces": {"Ethernet3": dot1x_interface("controlled")}}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the 802.1X controlled authenticator interfaces because the 'show dot1x all' output is incomplete.",
            None,
        ),
    },
}
