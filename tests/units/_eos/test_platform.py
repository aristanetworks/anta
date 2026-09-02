# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for EOS platform identity parsing and family resolution."""

from __future__ import annotations

import pytest

from anta._eos.platform import (
    PLATFORM_FAMILY_RULES,
    PlatformComponentIdentity,
    PlatformComponentRole,
    PlatformFamily,
    PlatformIdentity,
    _components_for_role,
    is_modular_platform,
    parse_eos_platform,
    parse_eos_platform_modules,
    platform_matches_families,
    resolve_platform_families,
)


def _modules_by_role(platform: PlatformIdentity, role: PlatformComponentRole) -> list[PlatformComponentIdentity]:
    """Return parsed modules matching one role."""
    return [module for module in platform.modules if module.role is role]


def test_every_platform_family_has_resolution_rules() -> None:
    """Verify the central resolver covers every declared stable family."""
    assert set(PlatformFamily) == set(PLATFORM_FAMILY_RULES)


@pytest.mark.parametrize(
    ("family", "role", "positive", "negative"),
    [
        pytest.param(PlatformFamily.SERIES_720_D, PlatformComponentRole.FIXED_SYSTEM, "ccs-720df-48y6", "CCS-720XP-48ZC2", id="720d"),
        pytest.param(PlatformFamily.SERIES_7050_X3, PlatformComponentRole.FIXED_SYSTEM, "DCS-7050CX3-32S", "DCS-7050SX2-72Q", id="7050x3"),
        pytest.param(PlatformFamily.SERIES_7280_R3, PlatformComponentRole.FIXED_SYSTEM, "DCS-7280CR3-32P4", "DCS-7280CR2-60", id="7280r3"),
        pytest.param(PlatformFamily.SERIES_7300_X3, PlatformComponentRole.LINE_CARD, "DCS-7300X3-32C-LC", "DCS-7300X-32Q-LC", id="7300x3"),
        pytest.param(PlatformFamily.SERIES_7358_X4, PlatformComponentRole.SWITCH_CARD, "7358X4-SC", "7368X4-SC", id="7358x4"),
        pytest.param(PlatformFamily.SERIES_7368_X4, PlatformComponentRole.SWITCH_CARD, "7368X4-SC", "7358X4-SC", id="7368x4"),
        pytest.param(PlatformFamily.SERIES_7500_R3, PlatformComponentRole.LINE_CARD, "DCS-7500R3-36CQ-LC", "DCS-7500R2-36CQ-LC", id="7500r3"),
    ],
)
def test_resolve_platform_families(
    family: PlatformFamily,
    role: PlatformComponentRole,
    positive: str,
    negative: str,
) -> None:
    """Verify normalized identities resolve by component role without advisory-local aliases."""
    assert family in resolve_platform_families(positive, role)
    assert family not in resolve_platform_families(negative, role)


def test_resolve_platform_families_rejects_empty_model() -> None:
    """Verify an empty component model resolves to no platform family."""
    assert not resolve_platform_families("", PlatformComponentRole.FIXED_SYSTEM)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        pytest.param("DCS-7050SX3-48YC12-F", False, id="fixed"),
        pytest.param("DCS-7508N", True, id="7500-modular"),
        pytest.param("dcs-7358-ch-f", True, id="normalized-7358-modular"),
        pytest.param("", False, id="empty"),
    ],
)
def test_is_modular_platform(model: str, expected: bool) -> None:
    """Verify module discovery is limited to known modular chassis."""
    assert is_modular_platform(model) is expected


def test_parse_fixed_platform_from_show_version() -> None:
    """Verify fixed systems are identified from show version alone."""
    platform = parse_eos_platform(" dcs-7050sx3-48yc12-f ")

    assert platform is not None
    assert platform.model == "DCS-7050SX3-48YC12-F"
    assert platform.chassis is None
    assert platform.platform_families == {PlatformFamily.SERIES_7050_X3}
    assert not platform.modules


def test_platform_identity_implements_device_platform_protocol() -> None:
    """Verify EOS identities expose the generic platform representation contract."""
    platform = parse_eos_platform("DCS-7050SX3-48YC12-F")
    assert platform is not None

    assert str(platform) == "DCS-7050SX3-48YC12-F"
    assert platform.to_dict() == {
        "model": "DCS-7050SX3-48YC12-F",
        "chassis": None,
        "modules": [],
        "platform_families": ["7050X3 Series"],
    }


def test_platform_identity_serializes_chassis_and_modules() -> None:
    """Verify the generic representation includes modular component details."""
    platform = parse_eos_platform("DCS-7808-CH")
    assert platform is not None
    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "DCS-7800-SUP1A"}}})

    assert parsed.to_dict()["chassis"] == {
        "model": "DCS-7808-CH",
        "role": "chassis",
        "slot": None,
        "platform_families": [],
    }
    assert parsed.to_dict()["modules"] == [
        {
            "model": "DCS-7800-SUP1A",
            "role": "supervisor",
            "slot": "1",
            "platform_families": [],
        }
    ]


@pytest.mark.parametrize("model", [None, ""])
def test_parse_model_requires_system_identity(model: str | None) -> None:
    """Verify missing system evidence remains unavailable."""
    assert parse_eos_platform(model) is None


def test_parse_model_defensively_rejects_untyped_input() -> None:
    """Verify runtime validation rejects callers that bypass the typed contract."""
    assert parse_eos_platform(42) is None  # type: ignore[arg-type]


def test_parse_modular_components_and_aggregate_families() -> None:
    """Verify one module response retains role-specific normalized identities."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None
    assert platform.chassis is not None
    assert platform.chassis.role is PlatformComponentRole.CHASSIS

    parsed = parse_eos_platform_modules(
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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {slot: {"modelName": model}}})

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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "UNRECOGNIZED", "typeDescription": description}}})

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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": model}}})

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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {slot: {"modelName": model, "typeDescription": description}}})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is expected_role


def test_realistic_7800_inventory_retains_all_module_roles() -> None:
    """Verify numeric supervisor slots and fabric entries retain their module roles."""
    platform = parse_eos_platform("DCS-7808-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(
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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": modules})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is expected_role


def test_7368_chassis_family_is_resolved_from_switch_card() -> None:
    """Verify a shared 7368 chassis does not override the installed switch-card family."""
    platform = parse_eos_platform("DCS-7368-CH-F")
    assert platform is not None
    assert PlatformFamily.SERIES_7368_X4 not in platform.platform_families

    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert PlatformFamily.SERIES_7358_X4 in parsed.platform_families
    assert PlatformFamily.SERIES_7368_X4 not in parsed.platform_families


def test_unknown_modules_do_not_discard_positive_family_evidence() -> None:
    """Verify unknown siblings do not discard known positive family evidence."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None
    parsed = parse_eos_platform_modules(
        platform,
        {"modules": {"1": {"modelName": "7358X4-SC"}, "2": {"unexpected": "value"}}},
    )

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4]) is True
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is None
    assert parsed.modules[1].role is PlatformComponentRole.UNKNOWN


def test_complete_negative_and_role_qualified_family_matches() -> None:
    """Verify complete evidence proves negatives and role qualifiers limit evaluation."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None
    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is False
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4], role=PlatformComponentRole.SWITCH_CARD) is True
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4], role=PlatformComponentRole.CHASSIS) is False


def test_system_and_supervisor_role_helpers() -> None:
    """Verify fixed-system and supervisor evidence is selected by role."""
    platform = parse_eos_platform("DCS-7050SX3-48YC12-F")
    assert platform is not None

    assert not _components_for_role(platform, PlatformComponentRole.FIXED_SYSTEM)
    assert not _components_for_role(platform, PlatformComponentRole.CHASSIS)
    assert not _components_for_role(platform, PlatformComponentRole.SUPERVISOR)


def test_missing_platform_cannot_match_families() -> None:
    """Verify missing platform evidence produces an unknown family match."""
    assert platform_matches_families(None, [PlatformFamily.SERIES_7050_X3]) is None


def test_fixed_platform_role_qualified_family_matches() -> None:
    """Verify fixed-system family matching can be explicitly role-qualified."""
    platform = parse_eos_platform("DCS-7050SX3-48YC12-F")
    assert platform is not None

    assert platform_matches_families(platform, [PlatformFamily.SERIES_7050_X3], role=PlatformComponentRole.FIXED_SYSTEM) is True
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7050_X4], role=PlatformComponentRole.FIXED_SYSTEM) is False


def test_missing_module_output_preserves_initial_identity() -> None:
    """Verify unsupported or malformed module collection retains the initial identity."""
    platform = parse_eos_platform("DCS-7508N")
    assert platform is not None

    assert parse_eos_platform_modules(platform, None) is platform
    assert parse_eos_platform_modules(platform, {}) is platform
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7500_R3]) is None


def test_generic_module_models_retain_their_roles() -> None:
    """Verify generic EOS component labels retain their recognized roles."""
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None
    parsed = parse_eos_platform_modules(
        platform,
        {"modules": {"1": {"modelName": "SUP"}, "2": {"modelName": "7800R3A-36D-LC"}}},
    )

    assert [component.role for component in parsed.modules] == [PlatformComponentRole.SUPERVISOR, PlatformComponentRole.LINE_CARD]
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7800_R3]) is True

    generic_line_card = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "LC"}}})
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
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {slot: {"modelName": model}}})

    assert len(parsed.modules) == 1
    assert parsed.modules[0].role is PlatformComponentRole.FABRIC_CARD
