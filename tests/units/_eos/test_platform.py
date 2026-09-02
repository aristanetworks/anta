# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for EOS platform identity parsing and family resolution."""

from __future__ import annotations

import pytest

from anta._eos.parsing import ParseFail, ParseFailureReason, ParseSuccessful
from anta._eos.platform import (
    MODULE_PLATFORM_FAMILY_RULES,
    SYSTEM_PLATFORM_RULES,
    PlatformComponentIdentity,
    PlatformComponentRole,
    PlatformFamily,
    PlatformIdentity,
    PlatformType,
    _components_for_role,
    _resolve_platform_type,
    _system_rule,
    parse_eos_platform,
    parse_eos_platform_modules,
    platform_matches_families,
    resolve_platform_families,
)


def _parse_platform(model: str | None) -> PlatformIdentity:
    """Parse a valid system model for tests."""
    result = parse_eos_platform(model)
    assert isinstance(result, ParseSuccessful)
    return result.value


def _parse_modules(platform: PlatformIdentity, output: dict[str, object]) -> PlatformIdentity:
    """Parse valid module inventory for tests."""
    result = parse_eos_platform_modules(platform, output)
    assert isinstance(result, ParseSuccessful)
    return result.value


def _modules_by_role(platform: PlatformIdentity, role: PlatformComponentRole) -> list[PlatformComponentIdentity]:
    """Return parsed modules matching one role."""
    return [module for module in platform.modules if module.role is role]


def test_every_platform_family_has_resolution_rules() -> None:
    """Verify the central resolver covers every declared stable family."""
    system_families = {family for rule in SYSTEM_PLATFORM_RULES for family in rule.families}
    assert set(PlatformFamily) == system_families | set(MODULE_PLATFORM_FAMILY_RULES)


@pytest.mark.parametrize(
    ("family", "role", "positive", "negative"),
    [
        pytest.param(PlatformFamily.SERIES_720_D, None, "ccs-720df-48y6", "CCS-720XP-48ZC2", id="720d"),
        pytest.param(PlatformFamily.SERIES_720_XPM, None, "CCS-720XPM-48TH-6SY-F", "CCS-722XPM-48TH-6SY-F", id="720xpm"),
        pytest.param(PlatformFamily.SERIES_720_XDM, None, "CCS-720XDM-48ZC2-F", "CCS-720XP-48ZC2-F", id="720xdm"),
        pytest.param(PlatformFamily.SERIES_710, None, "CCS-710P-16P", "DCS-7010T-48", id="710"),
        pytest.param(PlatformFamily.SERIES_7020_R4, None, "DCS-7020HR4M-48", "DCS-7020SR-32C2", id="7020r4"),
        pytest.param(PlatformFamily.SERIES_7130, None, "DCS-7132LB-48Y4C-R", "DCS-7150S-24", id="7130"),
        pytest.param(PlatformFamily.SERIES_7150, None, "DCS-7150S-24", "DCS-7160-48YC6", id="7150"),
        pytest.param(PlatformFamily.SERIES_7170, None, "DCS-7170B-64C", "DCS-7160-48YC6", id="7170"),
        pytest.param(PlatformFamily.SERIES_7050_X3, None, "DCS-7050CX3-32S", "DCS-7050SX2-72Q", id="7050x3"),
        pytest.param(PlatformFamily.SERIES_7280_R3, None, "DCS-7280CR3-32P4", "DCS-7280CR2-60", id="7280r3"),
        pytest.param(PlatformFamily.SERIES_7300_X3, PlatformComponentRole.LINE_CARD, "DCS-7300X3-32C-LC", "DCS-7300X-32Q-LC", id="7300x3"),
        pytest.param(PlatformFamily.SERIES_7358_X4, PlatformComponentRole.SWITCH_CARD, "7358X4-SC", "7368X4-SC", id="7358x4"),
        pytest.param(PlatformFamily.SERIES_7368_X4, PlatformComponentRole.SWITCH_CARD, "7368X4-SC", "7358X4-SC", id="7368x4"),
        pytest.param(PlatformFamily.SERIES_7289_R3A, PlatformComponentRole.SWITCH_CARD, "7289R3AK-SC", "7368X4-SC", id="7289r3a"),
        pytest.param(PlatformFamily.SERIES_7500_R3, PlatformComponentRole.LINE_CARD, "DCS-7500R3-36CQ-LC", "DCS-7500R2-36CQ-LC", id="7500r3"),
        pytest.param(PlatformFamily.SERIES_7700_R4, None, "DCS-DL-7700R4C-38PE-B", "DCS-DS-7720R4-128PE-F", id="7700r4"),
        pytest.param(PlatformFamily.SERIES_7720_R4, None, "DCS-DS-7720R4-128PE-F", "DCS-DL-7700R4C-38PE-B", id="7720r4"),
        pytest.param(PlatformFamily.AWE_5000, None, "AWE-5000-4S", "AWE-7220RP-5TH-2S", id="awe5000"),
        pytest.param(PlatformFamily.AWE_7200_R, None, "AWE-7220RP-5TH-2S", "AWE-5000-4S", id="awe7200r"),
        pytest.param(PlatformFamily.CLOUDEOS, None, "CloudEOS", "cEOSLab", id="cloudeos"),
        pytest.param(PlatformFamily.CEOS_LAB, None, "cEOSLab", "vEOS-lab", id="ceos-lab"),
        pytest.param(PlatformFamily.VEOS_LAB, None, "vEOS-lab", "cEOSLab", id="veos-lab"),
        pytest.param(PlatformFamily.CLOUDVISION_EXCHANGE, None, "CloudVision eXchange", "CloudEOS", id="cloudvision-exchange"),
    ],
)
def test_resolve_platform_families(
    family: PlatformFamily,
    role: PlatformComponentRole | None,
    positive: str,
    negative: str,
) -> None:
    """Verify normalized identities resolve by component role without advisory-local aliases."""
    assert family in resolve_platform_families(positive, role)
    assert family not in resolve_platform_families(negative, role)


def test_resolve_platform_families_rejects_empty_model() -> None:
    """Verify an empty component model resolves to no platform family."""
    assert not resolve_platform_families("")


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        pytest.param("DCS-7050SX3-48YC12-F", PlatformType.FIXED, id="fixed"),
        pytest.param("DCS-7132LB-48Y4C-R", PlatformType.FIXED, id="sa142-fixed"),
        pytest.param("DCS-7150S-24", PlatformType.FIXED, id="7150-fixed"),
        pytest.param("DCS-7170B-64C", PlatformType.FIXED, id="7170-fixed"),
        pytest.param("DCS-DL-7700R4-38PE", PlatformType.FIXED, id="dl-7700r4-fixed"),
        pytest.param("DCS-DS-7720R4-128PE-F", PlatformType.FIXED, id="7720r4-fixed"),
        pytest.param("DCS-7508N", PlatformType.CHASSIS, id="7500-chassis"),
        pytest.param("DCS-7358-CH-F", PlatformType.CHASSIS, id="7358-chassis"),
        pytest.param("DCS-7289-CH-F", PlatformType.CHASSIS, id="7289-chassis"),
        pytest.param("DCS-7304X3-F", PlatformType.CHASSIS, id="7304x3-chassis"),
        pytest.param("DCS-7308X3-F", PlatformType.CHASSIS, id="7308x3-chassis"),
        pytest.param("CEOSLAB", PlatformType.VIRTUAL, id="virtual"),
        pytest.param("AWE-7220RP-5TH-2S", PlatformType.APPLIANCE, id="appliance"),
        pytest.param("DCS-UNRECOGNIZED", PlatformType.UNKNOWN, id="unknown"),
    ],
)
def test_platform_type_is_resolved_from_exact_system_model(model: str, expected: PlatformType) -> None:
    """Verify exact system rules resolve physical type independently of family."""
    result = _resolve_platform_type(model)
    assert isinstance(result, ParseSuccessful)
    assert result.value is expected


def test_parse_fixed_platform_from_show_version() -> None:
    """Verify fixed systems retain the reported model while matching its normalized value."""
    platform = _parse_platform(" dcs-7050sx3-48yc12-f ")

    assert platform.model == "dcs-7050sx3-48yc12-f"
    assert platform.type is PlatformType.FIXED
    assert platform.platform_families == {PlatformFamily.SERIES_7050_X3}
    assert not platform.modules


@pytest.mark.parametrize(
    ("model", "platform_type", "family"),
    [
        pytest.param("CCS-720XPM-48TH-6SY-F", PlatformType.FIXED, PlatformFamily.SERIES_720_XPM, id="720xpm"),
        pytest.param("CCS-722XPM-48TH-6SY-F", PlatformType.FIXED, PlatformFamily.SERIES_722_XPM, id="722xpm"),
        pytest.param("CCS-720XDM-48ZC2-F", PlatformType.FIXED, PlatformFamily.SERIES_720_XDM, id="720xdm"),
        pytest.param("DCS-7020R4-10QC-4DF", PlatformType.FIXED, PlatformFamily.SERIES_7020_R4, id="7020r4"),
        pytest.param("DCS-7020R4M-24Y-6QDF", PlatformType.FIXED, PlatformFamily.SERIES_7020_R4, id="7020r4m"),
        pytest.param("DCS-7020HR4-48Y-8QC", PlatformType.FIXED, PlatformFamily.SERIES_7020_R4, id="7020hr4"),
        pytest.param("DCS-7020HR4M-48", PlatformType.FIXED, PlatformFamily.SERIES_7020_R4, id="7020hr4m"),
        pytest.param("DCS-7130L-48", PlatformType.FIXED, PlatformFamily.SERIES_7130, id="7130"),
        pytest.param("CloudEOS", PlatformType.VIRTUAL, PlatformFamily.CLOUDEOS, id="cloudeos"),
        pytest.param("cEOS-lab", PlatformType.VIRTUAL, PlatformFamily.CEOS_LAB, id="ceos-hyphenated"),
        pytest.param("cEOSLab", PlatformType.VIRTUAL, PlatformFamily.CEOS_LAB, id="ceos-compact"),
        pytest.param("vEOS-lab", PlatformType.VIRTUAL, PlatformFamily.VEOS_LAB, id="veos-hyphenated"),
        pytest.param("vEOSLab", PlatformType.VIRTUAL, PlatformFamily.VEOS_LAB, id="veos-compact"),
        pytest.param("CloudVision eXchange", PlatformType.APPLIANCE, PlatformFamily.CLOUDVISION_EXCHANGE, id="cvx"),
    ],
)
def test_released_system_model_variants_resolve(model: str, platform_type: PlatformType, family: PlatformFamily) -> None:
    """Verify released system-model variants resolve without losing their reported spelling."""
    platform = _parse_platform(model)

    assert platform.model == model
    assert platform.type is platform_type
    assert platform.platform_families == {family}


@pytest.mark.parametrize(
    "model",
    [
        pytest.param("DCS-DS-7720R4-128PE", id="base"),
        pytest.param("DCS-DS-7720R4-128PE-N", id="secure-boot"),
        pytest.param("DCS-DS-7720R4-128PE-F", id="live-inventory"),
    ],
)
def test_7720r4_variants_resolve_fixed_family(model: str) -> None:
    """Verify documented and observed 7720R4 variants share one fixed family."""
    platform = _parse_platform(model)
    assert platform.type is PlatformType.FIXED
    assert platform.platform_families == {PlatformFamily.SERIES_7720_R4}


@pytest.mark.parametrize("model", ["DCS-DL-7700R4-38PE", "DCS-DL-7700R4C-38PE-B", "DCS-DL-7700R4K-38PE-B"])
def test_dl_7700r4_variants_resolve_fixed_family(model: str) -> None:
    """Verify DL-7700R4 variants use their precise fixed-system family."""
    platform = _parse_platform(model)
    assert platform.type is PlatformType.FIXED
    assert platform.platform_families == {PlatformFamily.SERIES_7700_R4}


def test_platform_identity_implements_device_platform_protocol() -> None:
    """Verify EOS identities expose the generic platform representation contract."""
    platform = _parse_platform("DCS-7050SX3-48YC12-F")

    assert str(platform) == "DCS-7050SX3-48YC12-F"
    assert platform.to_dict() == {
        "model": "DCS-7050SX3-48YC12-F",
        "type": "fixed",
        "modules": [],
        "platform_families": ["7050X3 Series"],
    }


def test_platform_identity_serializes_chassis_and_modules() -> None:
    """Verify the generic representation includes modular component details."""
    platform = _parse_platform("DCS-7808-CH")
    parsed = _parse_modules(platform, {"modules": {"1": {"modelName": "DCS-7800-SUP1A"}}})

    assert parsed.to_dict()["type"] == "chassis"
    assert parsed.to_dict()["modules"] == [
        {
            "model": "DCS-7800-SUP1A",
            "role": "supervisor",
            "slot": "1",
            "platform_families": [],
        }
    ]


@pytest.mark.parametrize(
    ("model", "reason"),
    [
        pytest.param(None, ParseFailureReason.MISSING, id="missing"),
        pytest.param("", ParseFailureReason.INVALID, id="empty"),
        pytest.param("   ", ParseFailureReason.INVALID, id="whitespace"),
    ],
)
def test_parse_model_returns_typed_failure(model: str | None, reason: ParseFailureReason) -> None:
    """Verify missing and invalid system evidence retain their failure reason."""
    result = parse_eos_platform(model)
    assert isinstance(result, ParseFail)
    assert result.reason is reason


def test_parse_model_defensively_rejects_untyped_input() -> None:
    """Verify runtime validation rejects callers that bypass the typed contract."""
    result = parse_eos_platform(42)  # type: ignore[arg-type]
    assert isinstance(result, ParseFail)
    assert result.reason is ParseFailureReason.MALFORMED


def test_unknown_system_model_is_a_successful_identity() -> None:
    """Verify a valid unrecognized model remains usable with an unknown type."""
    platform = _parse_platform("DCS-UNRECOGNIZED")
    assert platform.type is PlatformType.UNKNOWN
    assert not platform.platform_families


def test_conflicting_type_rules_return_contradictory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify overlapping physical-type evidence is reported explicitly."""
    monkeypatch.setattr(
        "anta._eos.platform.SYSTEM_PLATFORM_RULES",
        (
            _system_rule(PlatformType.FIXED, r"^DCS-CONTRADICTORY$"),
            _system_rule(PlatformType.CHASSIS, r"^DCS-CONTRADICTORY$"),
        ),
    )

    result = parse_eos_platform("DCS-CONTRADICTORY")
    assert isinstance(result, ParseFail)
    assert result.reason is ParseFailureReason.CONTRADICTORY


def test_parse_modular_components_and_aggregate_families() -> None:
    """Verify one module response retains role-specific normalized identities."""
    platform = _parse_platform("DCS-7358-CH-F")
    assert platform.type is PlatformType.CHASSIS

    parsed = _parse_modules(
        platform,
        {
            "modules": {
                "1": {"modelName": "7358X4-SC"},
                "2": {"modelName": "7368-SUP-D"},
                "3": {"modelName": "7368-16C"},
                "4": {"modelName": "Not Inserted"},
            }
        },
    )

    assert [component.model for component in _modules_by_role(parsed, PlatformComponentRole.SWITCH_CARD)] == ["7358X4-SC"]
    assert [component.slot for component in _modules_by_role(parsed, PlatformComponentRole.SUPERVISOR)] == ["2"]
    assert [component.model for component in _modules_by_role(parsed, PlatformComponentRole.LINE_CARD)] == ["7368-16C"]
    assert PlatformFamily.SERIES_7358_X4 in parsed.platform_families


def test_7300x3_chassis_resolves_family_from_installed_line_card() -> None:
    """Verify a 7300X3 chassis collects module evidence that resolves its hardware generation."""
    platform = _parse_platform("DCS-7308X3-F")
    parsed = _parse_modules(platform, {"modules": {"3": {"modelName": "7300X3-32C-LC"}}})

    assert platform.type is PlatformType.CHASSIS
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7300_X3]) is True


@pytest.mark.parametrize(
    ("slot", "model", "role"),
    [
        pytest.param("Supervisor1", "UNRECOGNIZED", PlatformComponentRole.SUPERVISOR, id="supervisor"),
        pytest.param("SwitchCard1", "UNRECOGNIZED", PlatformComponentRole.SWITCH_CARD, id="switch-card"),
        pytest.param("LineCard1", "UNRECOGNIZED", PlatformComponentRole.LINE_CARD, id="line-card"),
        pytest.param("Fabric1", "UNRECOGNIZED", PlatformComponentRole.FABRIC_CARD, id="fabric-card"),
    ],
)
def test_module_slot_names_resolve_component_roles(slot: str, model: str, role: PlatformComponentRole) -> None:
    """Verify structured slot names determine the component role."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": {slot: {"modelName": model}}})

    assert parsed.modules[0].role is role


@pytest.mark.parametrize(
    ("description", "role"),
    [
        pytest.param("Supervisor module", PlatformComponentRole.SUPERVISOR, id="supervisor"),
        pytest.param("Switch Card", PlatformComponentRole.SWITCH_CARD, id="switch-card"),
        pytest.param("Linecard", PlatformComponentRole.LINE_CARD, id="line-card"),
        pytest.param("Fabric Module", PlatformComponentRole.FABRIC_CARD, id="fabric-module"),
        pytest.param("Fabric Card", PlatformComponentRole.FABRIC_CARD, id="fabric-card"),
    ],
)
def test_module_descriptions_resolve_component_roles(description: str, role: PlatformComponentRole) -> None:
    """Verify descriptions classify modules when slots and models do not."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": {"1": {"modelName": "UNRECOGNIZED", "typeDescription": description}}})

    assert parsed.modules[0].role is role


@pytest.mark.parametrize(
    "model",
    [
        pytest.param("SUP", id="generic"),
        pytest.param("DCS-7816-SUP", id="unsuffixed"),
        pytest.param("DCS-7816-SUP1", id="numbered"),
        pytest.param("DCS-7800-SUP1A", id="numbered-letter"),
        pytest.param("DCS-7800-SUP1S", id="sup1s"),
        pytest.param("DCS-7500-SUP2", id="sup2"),
        pytest.param("7368-SUP-D", id="hyphenated-suffix"),
    ],
)
def test_supervisor_sku_variants_resolve_from_numeric_slots(model: str) -> None:
    """Verify bounded supervisor SKU forms are recognized without slot-name hints."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": {"1": {"modelName": model}}})

    assert [component.model for component in _modules_by_role(parsed, PlatformComponentRole.SUPERVISOR)] == [model]


@pytest.mark.parametrize(
    ("model", "slot", "description", "expected_role"),
    [
        pytest.param("DCS-7816-SUP1S", "1", "DCS-7816-SUP1S Supervisor", PlatformComponentRole.SUPERVISOR, id="7816-sup1s"),
        pytest.param("DCS-7816-SUP", "1", "DCS-7816-SUP Supervisor", PlatformComponentRole.SUPERVISOR, id="7816-sup"),
        pytest.param("DCS-7800-SUP1A", "1", "DCS-7800-SUP Supervisor", PlatformComponentRole.SUPERVISOR, id="7800-sup1a"),
        pytest.param("DCS-7500-SUP2", "1", "DCS-7500-SUP2 Supervisor", PlatformComponentRole.SUPERVISOR, id="7500-sup2"),
        pytest.param("7001-SUP-A", "1", "Supervisor 7001", PlatformComponentRole.SUPERVISOR, id="7001-sup-a"),
        pytest.param("7003-SUP-ELB", "1", "Supervisor 7003", PlatformComponentRole.SUPERVISOR, id="7003-sup-elb"),
        pytest.param("Unknown", "2", "Standby supervisor", PlatformComponentRole.SUPERVISOR, id="unknown-standby-supervisor"),
        pytest.param("7800R3A-36D-LC", "3", "36-port QSFPDD Linecard", PlatformComponentRole.LINE_CARD, id="7800r3-line-card"),
        pytest.param("7800R4K-36PE-C-LC", "3", "36 port OSFP Linecard", PlatformComponentRole.LINE_CARD, id="7800r4-line-card"),
        pytest.param("7500R-36CQ-LC", "3", "36-port QSFP100 Linecard", PlatformComponentRole.LINE_CARD, id="7500r-line-card"),
        pytest.param("7500R-48S2CQ-LC", "4", "48-port SFP+ Linecard", PlatformComponentRole.LINE_CARD, id="7500r-sfp-line-card"),
        pytest.param("7500R-36Q-LC", "5", "36-port QSFP+ Linecard", PlatformComponentRole.LINE_CARD, id="7500r-qsfp-line-card"),
        pytest.param("7812R3-FM", "Fabric1", "DCS-7812R3 Fabric Module", PlatformComponentRole.FABRIC_CARD, id="7812r3-fabric"),
        pytest.param("7812R4-FM", "Fabric1", "DCS-7812R4 Fabric Module", PlatformComponentRole.FABRIC_CARD, id="7812r4-fabric"),
        pytest.param("7808R3-FM", "Fabric1", "DCS-7808R3 Fabric Module", PlatformComponentRole.FABRIC_CARD, id="7808r3-fabric"),
        pytest.param("7812-FCM", "Fabric6", "DCS-7812H Fan Spinner Fabric Module", PlatformComponentRole.FABRIC_CARD, id="7812-fcm"),
        pytest.param("7504R-FM", "Fabric1", "DCS-7504R Fabric Module", PlatformComponentRole.FABRIC_CARD, id="7504r-fabric"),
        pytest.param("", "6", "Unknown", PlatformComponentRole.UNKNOWN, id="empty-unknown"),
    ],
)
def test_carl_inventory_module_forms(
    model: str,
    slot: str,
    description: str,
    expected_role: PlatformComponentRole,
) -> None:
    """Verify every unique module form collected from the Carl inventory is retained and classified."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": {slot: {"modelName": model, "typeDescription": description}}})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is expected_role


def test_realistic_7800_inventory_retains_all_module_roles() -> None:
    """Verify numeric supervisor slots and fabric entries retain their module roles."""
    platform = _parse_platform("DCS-7808-CH")

    parsed = _parse_modules(
        platform,
        {
            "modules": {
                "1": {"modelName": "DCS-7800-SUP1A"},
                "2": {"modelName": "DCS-7800-SUP1A"},
                "3": {"modelName": "7800R3A-36D-LC"},
                "Fabric1": {"modelName": "7808R3-FM"},
            }
        },
    )

    assert [component.slot for component in _modules_by_role(parsed, PlatformComponentRole.SUPERVISOR)] == ["1", "2"]
    assert [component.slot for component in _modules_by_role(parsed, PlatformComponentRole.LINE_CARD)] == ["3"]
    assert [component.slot for component in _modules_by_role(parsed, PlatformComponentRole.FABRIC_CARD)] == ["Fabric1"]


@pytest.mark.parametrize(
    ("modules", "expected_role"),
    [
        pytest.param({42: {"modelName": "DCS-7500R3-36CQ-LC"}}, PlatformComponentRole.LINE_CARD, id="numeric-slot"),
        pytest.param({"Supervisor1": "invalid"}, PlatformComponentRole.SUPERVISOR, id="slot-only"),
        pytest.param({"1": {"modelName": "Unrecognized"}}, PlatformComponentRole.UNKNOWN, id="unknown"),
    ],
)
def test_module_entries_retain_all_available_role_evidence(modules: object, expected_role: PlatformComponentRole) -> None:
    """Verify module entries use available evidence and remain retained."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": modules})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is expected_role


def test_7368_chassis_family_is_resolved_from_switch_card() -> None:
    """Verify a shared 7368 chassis does not override the installed switch-card family."""
    platform = _parse_platform("DCS-7368-CH-F")
    assert PlatformFamily.SERIES_7368_X4 not in platform.platform_families

    parsed = _parse_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert PlatformFamily.SERIES_7358_X4 in parsed.platform_families
    assert PlatformFamily.SERIES_7368_X4 not in parsed.platform_families


@pytest.mark.parametrize("switch_card", ["7289R3A-SC", "7289R3AK-SC", "7289R3AM-SC"])
def test_7289_family_is_resolved_from_switch_card(switch_card: str) -> None:
    """Verify a generic 7289 chassis receives its generation from the installed switch card."""
    platform = _parse_platform("DCS-7289-CH-F")
    assert platform.type is PlatformType.CHASSIS
    assert not platform.platform_families

    parsed = _parse_modules(platform, {"modules": {"SwitchCard1": {"modelName": switch_card}, "Supervisor1": {"modelName": "7289-SUP-D"}}})

    assert parsed.platform_families == {PlatformFamily.SERIES_7289_R3A}
    assert _modules_by_role(parsed, PlatformComponentRole.SUPERVISOR)[0].platform_families == frozenset()


def test_mixed_7358_7368_switch_cards_retain_both_families() -> None:
    """Verify a shared chassis retains every installed switch-card family."""
    platform = _parse_platform("DCS-7368-CH-F")
    parsed = _parse_modules(
        platform,
        {
            "modules": {
                "SwitchCard1": {"modelName": "7358X4-SC"},
                "SwitchCard2": {"modelName": "7368X4-SC"},
            }
        },
    )

    assert parsed.platform_families == {PlatformFamily.SERIES_7358_X4, PlatformFamily.SERIES_7368_X4}


def test_unknown_modules_do_not_discard_positive_family_evidence() -> None:
    """Verify unknown siblings do not discard known positive family evidence."""
    platform = _parse_platform("DCS-7358-CH-F")
    parsed = _parse_modules(
        platform,
        {"modules": {"1": {"modelName": "7358X4-SC"}, "2": {"unexpected": "value"}}},
    )

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4]) is True
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is None
    assert parsed.modules[1].role is PlatformComponentRole.UNKNOWN


def test_complete_negative_and_role_qualified_family_matches() -> None:
    """Verify complete evidence proves negatives and role qualifiers limit evaluation."""
    platform = _parse_platform("DCS-7358-CH-F")
    parsed = _parse_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is False
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4], role=PlatformComponentRole.SWITCH_CARD) is True


def test_unknown_platform_type_cannot_prove_negative_family_membership() -> None:
    """Verify an unrecognized system model produces unknown family applicability."""
    platform = _parse_platform("DCS-UNRECOGNIZED")
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7050_X3]) is None


def test_supervisor_role_helper() -> None:
    """Verify absent installed module evidence returns no components."""
    platform = _parse_platform("DCS-7050SX3-48YC12-F")

    assert not _components_for_role(platform, PlatformComponentRole.SUPERVISOR)


def test_missing_platform_cannot_match_families() -> None:
    """Verify missing platform evidence produces an unknown family match."""
    assert platform_matches_families(None, [PlatformFamily.SERIES_7050_X3]) is None


def test_system_family_and_platform_type_are_independent() -> None:
    """Verify system-family matching does not require a component role."""
    platform = _parse_platform("DCS-7050SX3-48YC12-F")

    assert platform.type is PlatformType.FIXED
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7050_X3]) is True
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7050_X4]) is False


@pytest.mark.parametrize(
    ("output", "reason"),
    [
        pytest.param(None, ParseFailureReason.MISSING, id="missing-output"),
        pytest.param({}, ParseFailureReason.MISSING, id="missing-modules"),
        pytest.param({"modules": []}, ParseFailureReason.MALFORMED, id="malformed-modules"),
        pytest.param({"modules": {}}, ParseFailureReason.INVALID, id="empty-modules"),
    ],
)
def test_invalid_module_output_returns_typed_failure(output: dict[str, object] | None, reason: ParseFailureReason) -> None:
    """Verify invalid module inventory retains its failure reason."""
    platform = _parse_platform("DCS-7508N")

    result = parse_eos_platform_modules(platform, output)
    assert isinstance(result, ParseFail)
    assert result.reason is reason
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7500_R3]) is None


def test_module_parser_defensively_rejects_untyped_output() -> None:
    """Verify runtime validation reports a non-mapping module payload as malformed."""
    platform = _parse_platform("DCS-7508N")
    result = parse_eos_platform_modules(platform, [])  # type: ignore[arg-type]
    assert isinstance(result, ParseFail)
    assert result.reason is ParseFailureReason.MALFORMED


def test_module_parser_rejects_fixed_platform() -> None:
    """Verify module inventory cannot enrich a fixed system."""
    platform = _parse_platform("DCS-7050SX3-48YC12-F")
    result = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "LC"}}})
    assert isinstance(result, ParseFail)
    assert result.reason is ParseFailureReason.INVALID


def test_generic_module_models_retain_their_roles() -> None:
    """Verify generic EOS component labels retain their recognized roles."""
    platform = _parse_platform("DCS-7816-CH")
    parsed = _parse_modules(
        platform,
        {"modules": {"1": {"modelName": "SUP"}, "2": {"modelName": "7800R3A-36D-LC"}}},
    )

    assert [component.role for component in parsed.modules] == [PlatformComponentRole.SUPERVISOR, PlatformComponentRole.LINE_CARD]
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7800_R3]) is True

    generic_line_card = _parse_modules(platform, {"modules": {"1": {"modelName": "LC"}}})
    assert generic_line_card.modules[0].role is PlatformComponentRole.LINE_CARD
    assert platform_matches_families(generic_line_card, [PlatformFamily.SERIES_7800_R3]) is False


@pytest.mark.parametrize(
    ("slot", "model"),
    [
        pytest.param("Fabric1", "UNRECOGNIZED", id="fabric-slot"),
        pytest.param("1", "DCS-7800-FM", id="fabric-model"),
    ],
)
def test_fabric_modules_are_retained(slot: str, model: str) -> None:
    """Verify fabric modules are identified by slot or model."""
    platform = _parse_platform("DCS-7816-CH")

    parsed = _parse_modules(platform, {"modules": {slot: {"modelName": model}}})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is PlatformComponentRole.FABRIC_CARD
