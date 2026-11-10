# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 216."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import cast

import pytest

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.dot1x import Dot1xControlledAuthenticatorInterfacesFact, Dot1xSupplicantInterfacesFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.macsec import MacsecProfilesFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactsBase, FactSource, FactSourceKind
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ConfigurationAssessment, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily, PlatformType
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_216 import ADVISORY, AFFECTED_VERSION_MATRIX, FIXED_RELEASES, SA216, _assess_sa216
from tests.units.anta_tests import AntaUnitTestData, build_eos_platform, build_eos_version, test  # noqa: F401 - Generic ANTA test collection.
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

SOURCE = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
AUTH_OUTPUT = {"systemAuthControl": True, "interfaces": {"Ethernet3": {"portControl": "controlled"}}}
MAC_OUTPUT = {"sources": {"dmf": {"profiles": {}}, "cli": {"profiles": {"PROFILE": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}}}}}
EXPECTED_FIXES = (
    FixedRelease(EOSVersion(4, 37, 0, suffix="F")),
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
REMEDIATION = software_version_plan(EXPECTED_FIXES, current_version=EOSVersion(4, 35, 6, suffix="M"))


def version_fact(version: str = "4.35.6M") -> Fact[EosVersionFact]:
    """Build a source-independent normalized release."""
    return EosVersionFact.from_version(parse_eos_version(version).unwrap()).available(SOURCE)


def platform_fact(family: PlatformFamily = PlatformFamily.SERIES_7050_X3) -> Fact[PlatformIdentityFact]:
    """Build a fully identified family independently of implementation constants."""
    return PlatformIdentityFact("identified-platform", PlatformType.FIXED, (), frozenset({family})).available(SOURCE)


def auth_fact(entries: dict[str, object] | None = None, *, system_control: bool = True) -> Fact[Dot1xControlledAuthenticatorInterfacesFact]:
    """Parse the captured authenticator interface shape without runtime prerequisites."""
    entries = {"Ethernet3": {"portControl": "controlled"}} if entries is None else entries
    command = Dot1xControlledAuthenticatorInterfacesFact.commands[0].model_copy(update={"output": {"systemAuthControl": system_control, "interfaces": entries}})
    return Dot1xControlledAuthenticatorInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))


def mac_fact(profiles: dict[str, object] | None = None, *, other: dict[str, object] | None = None) -> Fact[MacsecProfilesFact]:
    """Parse independent source-qualified profiles and interface bindings."""
    profiles = {"PROFILE": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}} if profiles is None else profiles
    sources = {"cli": {"profiles": profiles}}
    if other is not None:
        sources["dmf"] = {"profiles": other}
    command = MacsecProfilesFact.commands[0].model_copy(update={"output": {"sources": sources}})
    return MacsecProfilesFact.derive(OfflineAntaDevice("unit-test"), (command,))


def supplicant_fact(entries: dict[str, object] | None = None) -> Fact[Dot1xSupplicantInterfacesFact]:
    """Observe the separate configured-role map without status or SSL prerequisites."""
    command = Dot1xSupplicantInterfacesFact.commands[0].model_copy(update={"output": {"interfaces": entries or {}}})
    return Dot1xSupplicantInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))


@pytest.mark.parametrize("reverse", [False, True])
def test_supplicant_positive_survives_unrelated_role_and_record_errors(reverse: bool) -> None:
    """An unused supplicant witness survives a failed authenticator command."""
    entries = [("Ethernet3", {"eapMethod": "tls", "sslProfileName": "", "status": "unused"}), ("Ethernet2", None)]
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        Dot1xControlledAuthenticatorInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE),
        mac_fact(),
        supplicant_fact(dict(reversed(entries) if reverse else entries)),
    )
    assert isinstance(result, AffectedResult)
    condition = result.conditions[0]
    assert isinstance(condition, ConfigurationAssessment)
    supplicant = condition.fact.value
    assert isinstance(supplicant, Dot1xSupplicantInterfacesFact)
    assert supplicant.interfaces[0].name == "Ethernet3"


def test_authenticator_positive_survives_failed_supplicant_command() -> None:
    """Either role's complete positive is independently sufficient."""
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        auth_fact(),
        mac_fact(),
        Dot1xSupplicantInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show dot1x supplicant", FactSourceKind.COMMAND)),
    )
    assert isinstance(result, AffectedResult)


@pytest.mark.parametrize("key_source", ["dot1x", None])
def test_supplicant_uses_same_interface_and_key_source_rules(key_source: str | None) -> None:
    """A default key source cannot make an otherwise configured supplicant exposed."""
    profile: dict[str, object] = {"interfaces": ["Ethernet3"]}
    if key_source is not None:
        profile["primaryKeySource"] = key_source
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact({}), mac_fact({"PROFILE": profile}), supplicant_fact({"Ethernet3": {"status": "unused"}}))
    assert isinstance(result, AffectedResult if key_source == "dot1x" else NotAffectedResult)


def test_split_supplicant_and_profile_do_not_correlate() -> None:
    """Configured supplicants on another interface do not satisfy the conjunction."""
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact({}), mac_fact(), supplicant_fact({"Ethernet2": {"status": "unused"}}))
    assert isinstance(result, NotAffectedResult)


def test_authenticator_absence_does_not_hide_unavailable_supplicant_inventory() -> None:
    """Both role inventories are needed to conclude the configured role is absent."""
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        auth_fact({}),
        mac_fact(),
        Dot1xSupplicantInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show dot1x supplicant", FactSourceKind.COMMAND)),
    )
    assert isinstance(result, ErrorResult)
    assert {problem.source.name for problem in result.problems} == {"show dot1x supplicant"}


@pytest.mark.parametrize(
    ("version", "affected"),
    [
        ("4.21.99M", False),
        ("4.22.0F", True),
        ("4.22.99M", True),
        ("4.31.99.99M", True),
        ("4.32.0F", True),
        ("4.32.99.99M", True),
        ("4.33.0F", True),
        ("4.33.9.99M", True),
        ("4.33.10M", False),
        ("4.33.10.1M", False),
        ("4.34.0F", True),
        ("4.34.8.99M", True),
        ("4.34.9M", False),
        ("4.34.9.1M", False),
        ("4.35.0F", True),
        ("4.35.6.99M", True),
        ("4.35.7M", False),
        ("4.35.7.1M", False),
        ("4.36.0F", True),
        ("4.36.2.99F", True),
        ("4.36.3M", False),
        ("4.36.3.1M", False),
        ("4.37.0F", False),
        ("4.38.0F", False),
        ("5.0.0F", False),
    ],
)
def test_software_boundaries(version: str, affected: bool) -> None:
    """Use the introduction and named fixes, keeping unfixed older trains open-ended."""
    result = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
    assert result.affected_status is (AffectedStatus.AFFECTED if affected else AffectedStatus.NOT_AFFECTED)


def test_metadata_and_fixed_software_remediation() -> None:
    """Preserve assigned identity, CVSSv3 severity, exact fix labels, and date."""
    assert ADVISORY.sa_number == "0216"
    assert ADVISORY.last_updated == date(2026, 11, 10)
    assert ADVISORY.vulnerabilities[0].id == "CVE-2026-120976"
    assert ADVISORY.vulnerabilities[0].severity.value == "medium"
    assert tuple(str(fix.version) for fix in FIXED_RELEASES) == ("4.37.0F", "4.36.3M", "4.35.7M", "4.34.9M", "4.33.10M")
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), mac_fact(), supplicant=supplicant_fact())
    assert isinstance(result, AffectedResult)
    assert result.remediation == REMEDIATION
    assert result.vulnerability_id == "CVE-2026-120976"


@pytest.mark.parametrize("mode", ["controlled", "forceAuth", "forceUnauth"])
@pytest.mark.parametrize("system_control", [False, True])
def test_authenticator_requires_global_control_and_auto(mode: str, system_control: bool) -> None:
    """Only effective auto control establishes the authenticator branch."""
    result = _assess_sa216(
        version_fact(), platform_fact(), auth_fact({"Ethernet3": {"portControl": mode}}, system_control=system_control), mac_fact(), supplicant_fact()
    )
    assert isinstance(result, AffectedResult if system_control and mode == "controlled" else NotAffectedResult)


@pytest.mark.parametrize("mode", ["forceAuth", "forceUnauth"])
def test_controlled_authenticator_on_other_port_does_not_qualify_forced_macsec(mode: str) -> None:
    """A device-wide positive cannot substitute for same-interface control."""
    result = _assess_sa216(
        version_fact(), platform_fact(), auth_fact({"Ethernet2": {"portControl": "controlled"}, "Ethernet3": {"portControl": mode}}), mac_fact(), supplicant_fact()
    )
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("system_control", [False, True])
def test_supplicant_does_not_require_authenticator_control(system_control: bool) -> None:
    """An independent supplicant witness survives disabled authenticator control."""
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        auth_fact({"Ethernet3": {"portControl": "forceUnauth"}}, system_control=system_control),
        mac_fact(),
        supplicant_fact({"Ethernet3": {"status": "unused", "sslProfileName": ""}}),
    )
    assert isinstance(result, AffectedResult)


@pytest.mark.parametrize(
    "profiles",
    [
        {},
        {"PROFILE": {"primaryKeySource": "dot1x", "interfaces": []}},
        {"PROFILE": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet2"]}},
        {"DEFAULT": {"interfaces": ["Ethernet3"]}},
        {"STATIC": {"primaryKeySource": "cli", "interfaces": ["Ethernet3"]}},
    ],
)
def test_captured_negative_controls(profiles: dict[str, object]) -> None:
    """Absent binding, split interfaces and a non-dot1x key source do not correlate."""
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), mac_fact(profiles), supplicant=supplicant_fact())
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("broken_side", ["authenticator", "profile", "both"])
def test_complete_witness_survives_unrelated_incomplete_scope(reverse: bool, broken_side: str) -> None:
    """Either traversal order preserves the complete Ethernet3 witness."""
    auth = [("Ethernet3", {"portControl": "controlled"})]
    profiles = [("VALID", {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]})]
    if broken_side in {"authenticator", "both"}:
        auth.append(("Ethernet2", {}))
    if broken_side in {"profile", "both"}:
        profiles.append(("BROKEN", {"primaryKeySource": None, "interfaces": ["Ethernet2"]}))
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        auth_fact(dict(reversed(auth) if reverse else auth)),
        mac_fact(dict(reversed(profiles) if reverse else profiles)),
        supplicant=supplicant_fact(),
    )
    assert isinstance(result, AffectedResult)
    auth_condition, macsec_condition = result.conditions
    assert isinstance(auth_condition, ConfigurationAssessment)
    assert isinstance(macsec_condition, ConfigurationAssessment)
    assert isinstance(auth_condition.fact.value, Dot1xControlledAuthenticatorInterfacesFact)
    assert isinstance(macsec_condition.fact.value, MacsecProfilesFact)
    assert auth_condition.fact.value.interfaces[0].name == "Ethernet3"
    assert macsec_condition.fact.value.profiles[0].interfaces == ("Ethernet3",)


@pytest.mark.parametrize("broken_side", ["authenticator", "profile", "both"])
def test_relevant_incomplete_scope_prevents_safe_result(broken_side: str) -> None:
    """No complete witness plus potentially overlapping uncertainty must be Error."""
    auth = auth_fact({"Ethernet3": {}}) if broken_side in {"authenticator", "both"} else auth_fact()
    macsec = mac_fact({"BROKEN": {"primaryKeySource": None, "interfaces": ["Ethernet3"]}}) if broken_side in {"profile", "both"} else mac_fact()
    result = _assess_sa216(version_fact(), platform_fact(), auth, macsec, supplicant=supplicant_fact())
    assert isinstance(result, ErrorResult)
    expected_sources = (
        {"show dot1x all"}
        if broken_side == "authenticator"
        else {"show mac security profile"}
        if broken_side == "profile"
        else {"show dot1x all", "show mac security profile"}
    )
    assert {problem.source.name for problem in result.problems} == expected_sources


def test_known_disjoint_errors_do_not_poison_absence() -> None:
    """A broken authenticator on Ethernet2 cannot correlate to profiles only on Ethernet3."""
    result = _assess_sa216(
        version_fact(),
        platform_fact(),
        auth_fact({"Ethernet2": {}}),
        mac_fact(),
        supplicant=supplicant_fact(),
    )
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("broken", ["interface-name", "profile-name", "source-name", "profile-bindings", "source-inventory"])
@pytest.mark.parametrize("positive", [False, True])
def test_unknown_sibling_scope_preserves_decisive_presence(broken: str, reverse: bool, positive: bool) -> None:
    """Unknown sibling scope is uncertainty, not a contradiction of a known witness."""
    auth_entries = [("Ethernet3", {"portControl": "controlled"})] if positive or broken != "interface-name" else []
    profile_entries = [("VALID", {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]})] if positive or broken == "interface-name" else []
    if broken == "interface-name":
        auth_entries.append(("", {}))
    if broken == "profile-name":
        profile_entries.append(("", {}))
    if broken == "profile-bindings":
        profile_entries.append(("BROKEN", {"primaryKeySource": "dot1x"}))
    sources = [("cli", {"profiles": dict(reversed(profile_entries) if reverse else profile_entries)})]
    if broken in {"source-name", "source-inventory"}:
        sources.append(("" if broken == "source-name" else "dmf", {}))
    mac_command = MacsecProfilesFact.commands[0].model_copy(update={"output": {"sources": dict(reversed(sources) if reverse else sources)}})
    macsec = MacsecProfilesFact.derive(OfflineAntaDevice("unit-test"), (mac_command,))
    result = _assess_sa216(
        version_fact(), platform_fact(), auth_fact(dict(reversed(auth_entries) if reverse else auth_entries)), macsec, supplicant=supplicant_fact()
    )
    assert isinstance(result, AffectedResult if positive else ErrorResult)


def test_non_dot1x_profile_errors_are_outside_key_source_scope() -> None:
    """A known different key source excludes that profile despite missing bindings."""
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), mac_fact({"STATIC": {"primaryKeySource": "cli"}}), supplicant=supplicant_fact())
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("source", ["cli", "dmf"])
def test_all_profile_sources_are_observed(source: str) -> None:
    """The assessment cannot silently ignore a dot1x-keyed non-CLI profile."""
    macsec = mac_fact() if source == "cli" else mac_fact({}, other={"PROFILE": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}})
    assert isinstance(_assess_sa216(version_fact(), platform_fact(), auth_fact(), macsec, supplicant=supplicant_fact()), AffectedResult)


@pytest.mark.parametrize("other_key", ["dot1x", "cli"])
def test_additional_profile_record_does_not_veto_dot1x_attachment(other_key: str) -> None:
    """Even synthetic duplicate bindings cannot erase an established positive."""
    macsec = mac_fact(other={"OTHER": {"primaryKeySource": other_key, "interfaces": ["Ethernet3"]}})
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), macsec, supplicant=supplicant_fact())
    assert isinstance(result, AffectedResult)


def test_unrelated_additional_bindings_preserve_another_complete_witness() -> None:
    """Additional records on Ethernet2 cannot erase a complete Ethernet3 witness."""
    macsec = mac_fact(
        {"VALID": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}, "CONFLICT": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet2"]}},
        other={"OTHER": {"interfaces": ["Ethernet2"]}},
    )
    assert isinstance(_assess_sa216(version_fact(), platform_fact(), auth_fact(), macsec, supplicant=supplicant_fact()), AffectedResult)


def test_multiple_non_dot1x_records_remain_outside_key_source_scope() -> None:
    """Additional records cannot create the independently absent dot1x key source."""
    macsec = mac_fact({"DEFAULT": {"interfaces": ["Ethernet3"]}}, other={"STATIC": {"primaryKeySource": "cli", "interfaces": ["Ethernet3"]}})
    assert isinstance(_assess_sa216(version_fact(), platform_fact(), auth_fact(), macsec, supplicant=supplicant_fact()), NotAffectedResult)


@pytest.mark.parametrize("decisive", ["software", "platform", "authenticator", "macsec"])
def test_independent_exclusions_ignore_unavailable_other_inputs(decisive: str) -> None:
    """One conclusively absent prerequisite can establish safety independently."""
    version = version_fact("4.37.0F") if decisive == "software" else EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = platform_fact(PlatformFamily.VEOS_LAB) if decisive == "platform" else PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    dot1x = auth_fact({}) if decisive == "authenticator" else Dot1xControlledAuthenticatorInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE)
    macsec = mac_fact({}) if decisive == "macsec" else MacsecProfilesFact.unavailable(FactProblemKind.UNSUPPORTED, SOURCE)
    assert isinstance(_assess_sa216(version, platform, dot1x, macsec, supplicant=supplicant_fact()), NotAffectedResult)


def test_all_required_unavailable_commands_and_metadata_are_reported() -> None:
    """Retain every required source failure when no decisive exclusion exists."""
    result = _assess_sa216(
        EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE),
        PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE),
        Dot1xControlledAuthenticatorInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show dot1x all", FactSourceKind.COMMAND)),
        MacsecProfilesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show mac security profile", FactSourceKind.COMMAND)),
        supplicant=Dot1xSupplicantInterfacesFact.unavailable(FactProblemKind.COLLECTION_FAILED, FactSource("show dot1x supplicant", FactSourceKind.COMMAND)),
    )
    assert isinstance(result, ErrorResult)
    assert len(result.problems) == 5
    assert {problem.source.name for problem in result.problems} == {"device metadata", "show dot1x all", "show mac security profile", "show dot1x supplicant"}


@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_7388_X5,
        PlatformFamily.SERIES_7500_R,
        PlatformFamily.SERIES_7500_R2,
        PlatformFamily.SERIES_7800_R3,
        PlatformFamily.SERIES_722_XPM,
        PlatformFamily.SERIES_750_X,
        PlatformFamily.SERIES_7050_X3,
        PlatformFamily.SERIES_7050_X4,
        PlatformFamily.SERIES_7170,
        PlatformFamily.SERIES_7289_R3A,
        PlatformFamily.SERIES_7500_R3,
        PlatformFamily.SERIES_7800_R4,
    ],
)
def test_source_families_and_approved_identity_mappings(family: PlatformFamily) -> None:
    """Cover the literal families and approved 7388/7289 family mappings."""
    assert isinstance(_assess_sa216(version_fact(), platform_fact(family), auth_fact(), mac_fact(), supplicant=supplicant_fact()), AffectedResult)


@pytest.mark.parametrize(
    "family",
    [
        PlatformFamily.SERIES_720_XP,
        PlatformFamily.SERIES_7280_R3,
        PlatformFamily.SERIES_7700_R4,
        PlatformFamily.CEOS_LAB,
        PlatformFamily.VEOS_LAB,
        PlatformFamily.CLOUDEOS,
        PlatformFamily.CVX,
        PlatformFamily.ZTX_7000,
        PlatformFamily.ZTX_7200,
    ],
)
def test_explicitly_excluded_families(family: PlatformFamily) -> None:
    """Related names, virtual platforms and new families do not widen restricted scope."""
    assert isinstance(_assess_sa216(version_fact(), platform_fact(family), auth_fact(), mac_fact(), supplicant=supplicant_fact()), NotAffectedResult)


@pytest.mark.parametrize(("model", "module"), [("DCS-7388", "7388X5-SC"), ("DCS-7289-CH-F", "7289R3AK-SC")])
def test_modular_mapping_uses_actual_component_identity(model: str, module: str) -> None:
    """A generic chassis alone is insufficient; installed cards resolve its family."""
    identity = build_eos_platform(model, {"modules": {"SwitchCard1": {"modelName": module}}})
    assert identity is not None
    platform = PlatformIdentityFact.from_identity(identity).available(SOURCE)
    assert isinstance(_assess_sa216(version_fact(), platform, auth_fact(), mac_fact(), supplicant=supplicant_fact()), AffectedResult)
    incomplete = build_eos_platform(model)
    assert incomplete is not None
    platform = PlatformIdentityFact.from_identity(incomplete).available(SOURCE)
    assert isinstance(_assess_sa216(version_fact(), platform, auth_fact(), mac_fact(), supplicant=supplicant_fact()), ErrorResult)


def test_command_and_fact_container_contract() -> None:
    """The public class uses metadata and three explicit revision-one observations."""
    facts = cast("type[FactsBase]", SA216.__dict__["Facts"])
    assert tuple(facts.definitions()) == ("version", "platform", "dot1x", "macsec", "supplicant")
    instance = SA216(OfflineAntaDevice("unit-test"))
    assert [(command.command, command.ofmt, command.revision) for command in instance.instance_commands] == [
        ("show dot1x all", "json", 1),
        ("show mac security profile", "json", 1),
        ("show dot1x supplicant", "json", 1),
    ]


expected = partial(build_expected_advisory_result, "CVE-2026-120976")
_DATA: AntaUnitTestData = {
    (SA216, "affected-supplicant-same-interface"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [{"systemAuthControl": True, "interfaces": {}}, MAC_OUTPUT, {"interfaces": {"Ethernet3": {"status": "unused", "sslProfileName": ""}}}],
        "expected": expected(AntaTestStatus.FAILURE, "The device is affected because EOS version '4.35.6M' is affected", REMEDIATION),
    },
    (SA216, "error-missing-supplicant-inventory"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [{"systemAuthControl": True, "interfaces": {}}, MAC_OUTPUT, {}],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the 802.1X supplicant interfaces", None),
    },
    (SA216, "affected-same-interface"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [AUTH_OUTPUT, MAC_OUTPUT, {"interfaces": {}}],
        "expected": expected(AntaTestStatus.FAILURE, "The device is affected because EOS version '4.35.6M' is affected", REMEDIATION),
    },
    (SA216, "not-affected-split-interface"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [{"systemAuthControl": True, "interfaces": {"Ethernet2": {"portControl": "controlled"}}}, MAC_OUTPUT, {"interfaces": {}}],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the 802.1X interface with an attached dot1x-keyed MACsec profile configuration is not configured.",
            None,
        ),
    },
    (SA216, "not-affected-no-profile"): {
        "version": None,
        "platform": None,
        "eos_data": [AUTH_OUTPUT, {"sources": {"cli": {"profiles": {}}}}, {"interfaces": {}}],
        "expected": expected(
            AntaTestStatus.SUCCESS, "The device is not affected because the 802.1X MACsec profile attachment using dot1x keys configuration is not configured.", None
        ),
    },
    (SA216, "not-affected-fixed-command-errors"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [{}, {}, {"interfaces": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.37.0F' is outside the affected releases.", None),
    },
    (SA216, "not-affected-excluded-virtual"): {
        "version": None,
        "platform": build_eos_platform("vEOS-lab"),
        "eos_data": [{}, {}, {"interfaces": {}}],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because platform 'vEOS-lab' is outside the affected platform scope.", None),
    },
    (SA216, "error-missing-profile-inventory"): {
        "version": build_eos_version("4.35.6M"),
        "platform": build_eos_platform("DCS-7050SX3-48YC8"),
        "eos_data": [AUTH_OUTPUT, {}, {"interfaces": {}}],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the MACsec profile key sources and interface bindings", None),
    },
}


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("positive", [False, True])
@pytest.mark.parametrize("role", ["authenticator", "supplicant"])
def test_partial_profile_bindings_preserve_positive_or_required_uncertainty(reverse: bool, positive: bool, role: str) -> None:
    """A valid same-interface witness survives a bad list entry; missing coverage is not absence."""
    entries = ["Ethernet3" if positive else "Ethernet2", None]
    macsec = mac_fact({"PROFILE": {"primaryKeySource": "dot1x", "interfaces": list(reversed(entries)) if reverse else entries}})
    authenticator = auth_fact() if role == "authenticator" else auth_fact({})
    supplicant = supplicant_fact({"Ethernet3": {}}) if role == "supplicant" else supplicant_fact()
    result = _assess_sa216(version_fact(), platform_fact(), authenticator, macsec, supplicant)
    assert isinstance(result, AffectedResult if positive else ErrorResult)
    if isinstance(result, ErrorResult):
        assert {problem.source.name for problem in result.problems} == {"show mac security profile"}


@pytest.mark.parametrize("key_source", ["cli", None])
def test_partial_non_dot1x_bindings_remain_outside_key_source_scope(key_source: str | None) -> None:
    """Malformed bindings cannot create an independently absent dot1x key source."""
    profile: dict[str, object] = {"interfaces": ["Ethernet3", None]}
    if key_source is not None:
        profile["primaryKeySource"] = key_source
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), mac_fact({"PROFILE": profile}), supplicant_fact())
    assert isinstance(result, NotAffectedResult)


@pytest.mark.parametrize("reverse", [False, True])
def test_partial_binding_with_unknown_key_source_cannot_override_known_scope_error(reverse: bool) -> None:
    """An invalid key source at a known witness remains an error despite unknown sibling scope."""
    entries = ["Ethernet3", None]
    profiles: dict[str, object] = {
        "VALID": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]},
        "BROKEN": {"primaryKeySource": None, "interfaces": list(reversed(entries)) if reverse else entries},
    }
    result = _assess_sa216(version_fact(), platform_fact(), auth_fact(), mac_fact(profiles), supplicant_fact())
    assert isinstance(result, ErrorResult)
    assert {problem.source.name for problem in result.problems} == {"show mac security profile"}
