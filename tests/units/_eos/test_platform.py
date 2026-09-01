# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for EOS platform identity parsing and family resolution."""

from __future__ import annotations

import pytest

from anta._eos.platform import (
    PLATFORM_FAMILY_RULES,
    PlatformComponentRole,
    PlatformFamily,
    _components_for_role,
    _role_is_complete,
    is_modular_platform,
    parse_eos_platform,
    parse_eos_platform_modules,
    platform_matches_families,
    resolve_platform_families,
)


def test_every_platform_family_has_resolution_rules() -> None:
    """Verify the central resolver covers every declared stable family."""
    assert set(PlatformFamily) == set(PLATFORM_FAMILY_RULES)


@pytest.mark.parametrize(
    ("family", "role", "positive", "negative"),
    [
        pytest.param(PlatformFamily.SERIES_720_D, PlatformComponentRole.CHASSIS, "ccs-720df-48y6", "CCS-720XP-48ZC2", id="720d"),
        pytest.param(PlatformFamily.SERIES_7050_X3, PlatformComponentRole.CHASSIS, "DCS-7050CX3-32S", "DCS-7050SX2-72Q", id="7050x3"),
        pytest.param(PlatformFamily.SERIES_7280_R3, PlatformComponentRole.CHASSIS, "DCS-7280CR3-32P4", "DCS-7280CR2-60", id="7280r3"),
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
    assert not resolve_platform_families("", PlatformComponentRole.CHASSIS)


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
    """Verify fixed systems are complete from show version alone."""
    platform = parse_eos_platform(" dcs-7050sx3-48yc12-f ")

    assert platform is not None
    assert platform.chassis.model == "DCS-7050SX3-48YC12-F"
    assert platform.chassis.role is PlatformComponentRole.CHASSIS
    assert platform.platform_families == {PlatformFamily.SERIES_7050_X3}
    assert platform.completeness.chassis
    assert platform.completeness.supervisors
    assert platform.completeness.switch_cards
    assert platform.completeness.line_cards


def test_platform_identity_implements_device_platform_protocol() -> None:
    """Verify EOS identities expose the generic platform representation contract."""
    platform = parse_eos_platform("DCS-7050SX3-48YC12-F")
    assert platform is not None

    assert str(platform) == "DCS-7050SX3-48YC12-F"
    assert platform.to_dict() == {
        "chassis": {
            "model": "DCS-7050SX3-48YC12-F",
            "role": "chassis",
            "slot": None,
            "platform_families": ["7050X3 Series"],
        },
        "supervisors": [],
        "switch_cards": [],
        "line_cards": [],
        "platform_families": ["7050X3 Series"],
        "completeness": {"chassis": True, "supervisors": True, "switch_cards": True, "line_cards": True},
    }


@pytest.mark.parametrize("model", [None, ""])
def test_parse_model_requires_chassis_identity(model: str | None) -> None:
    """Verify missing chassis evidence remains unavailable."""
    assert parse_eos_platform(model) is None


def test_parse_model_defensively_rejects_untyped_input() -> None:
    """Verify runtime validation rejects callers that bypass the typed contract."""
    assert parse_eos_platform(42) is None  # type: ignore[arg-type]


def test_parse_modular_components_and_aggregate_families() -> None:
    """Verify one module response retains role-specific normalized identities."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None

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

    assert [component.model for component in parsed.switch_cards] == ["7358X4-SC"]
    assert [component.slot for component in parsed.supervisors] == ["2"]
    assert [component.model for component in parsed.line_cards] == ["7368-16C"]
    assert PlatformFamily.SERIES_7358_X4 in parsed.platform_families
    assert parsed.completeness.supervisors
    assert parsed.completeness.switch_cards
    assert parsed.completeness.line_cards


@pytest.mark.parametrize(
    ("slot", "model", "role"),
    [
        pytest.param("Supervisor1", "UNRECOGNIZED", PlatformComponentRole.SUPERVISOR, id="supervisor"),
        pytest.param("SwitchCard1", "UNRECOGNIZED", PlatformComponentRole.SWITCH_CARD, id="switch-card"),
        pytest.param("LineCard1", "UNRECOGNIZED", PlatformComponentRole.LINE_CARD, id="line-card"),
    ],
)
def test_module_slot_names_resolve_component_roles(slot: str, model: str, role: PlatformComponentRole) -> None:
    """Verify structured slot names determine the component role."""
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {slot: {"modelName": model}}})

    assert getattr(parsed, f"{role.value}s")[0].role is role


@pytest.mark.parametrize(
    "modules",
    [
        pytest.param({42: {"modelName": "DCS-7500R3-36CQ-LC"}}, id="invalid-slot"),
        pytest.param({"Supervisor1": "invalid"}, id="invalid-module-data"),
    ],
)
def test_malformed_module_entries_make_relevant_evidence_incomplete(modules: object) -> None:
    """Verify malformed module entries cannot prove negative family matches."""
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": modules})

    assert not parsed.completeness.supervisors


def test_7368_chassis_family_is_resolved_from_switch_card() -> None:
    """Verify a shared 7368 chassis does not override the installed switch-card family."""
    platform = parse_eos_platform("DCS-7368-CH-F")
    assert platform is not None
    assert PlatformFamily.SERIES_7368_X4 not in platform.platform_families

    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert PlatformFamily.SERIES_7358_X4 in parsed.platform_families
    assert PlatformFamily.SERIES_7368_X4 not in parsed.platform_families


def test_partial_module_evidence_keeps_positive_matches_decidable() -> None:
    """Verify malformed siblings do not discard known positive family evidence."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None
    parsed = parse_eos_platform_modules(
        platform,
        {"modules": {"1": {"modelName": "7358X4-SC"}, "2": {"unexpected": "value"}}},
    )

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4]) is True
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is None
    assert not parsed.completeness.switch_cards


def test_complete_negative_and_role_qualified_family_matches() -> None:
    """Verify complete evidence proves negatives and role qualifiers limit evaluation."""
    platform = parse_eos_platform("DCS-7358-CH-F")
    assert platform is not None
    parsed = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "7358X4-SC"}}})

    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7388_X5]) is False
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4], role=PlatformComponentRole.SWITCH_CARD) is True
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7358_X4], role=PlatformComponentRole.CHASSIS) is False


def test_chassis_and_supervisor_role_helpers() -> None:
    """Verify chassis and supervisor evidence is selected from the corresponding fields."""
    platform = parse_eos_platform("DCS-7050SX3-48YC12-F")
    assert platform is not None

    assert _components_for_role(platform, PlatformComponentRole.CHASSIS) == (platform.chassis,)
    assert _role_is_complete(platform, PlatformComponentRole.CHASSIS)
    assert not _components_for_role(platform, PlatformComponentRole.SUPERVISOR)
    assert _role_is_complete(platform, PlatformComponentRole.SUPERVISOR)


def test_missing_platform_cannot_match_families() -> None:
    """Verify missing platform evidence produces an unknown family match."""
    assert platform_matches_families(None, [PlatformFamily.SERIES_7050_X3]) is None


def test_missing_module_output_preserves_incomplete_initial_identity() -> None:
    """Verify unsupported or malformed module collection retains unavailable evidence."""
    platform = parse_eos_platform("DCS-7508N")
    assert platform is not None

    assert parse_eos_platform_modules(platform, None) is platform
    assert parse_eos_platform_modules(platform, {}) is platform
    assert platform_matches_families(platform, [PlatformFamily.SERIES_7500_R3]) is None


def test_generic_module_models_leave_only_their_roles_incomplete() -> None:
    """Verify generic EOS component labels cannot prove generation-specific family negatives."""
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None
    parsed = parse_eos_platform_modules(
        platform,
        {"modules": {"1": {"modelName": "SUP"}, "2": {"modelName": "7800R3A-36D-LC"}}},
    )

    assert not parsed.completeness.supervisors
    assert parsed.completeness.switch_cards
    assert parsed.completeness.line_cards
    assert platform_matches_families(parsed, [PlatformFamily.SERIES_7800_R3]) is True

    generic_line_card = parse_eos_platform_modules(platform, {"modules": {"1": {"modelName": "LC"}}})
    assert not generic_line_card.completeness.line_cards
    assert platform_matches_families(generic_line_card, [PlatformFamily.SERIES_7800_R3]) is None


@pytest.mark.parametrize(
    ("slot", "model"),
    [
        pytest.param("Fabric1", "UNRECOGNIZED", id="fabric-slot"),
        pytest.param("1", "DCS-7800-FM", id="fabric-model"),
    ],
)
def test_fabric_modules_do_not_make_platform_identity_incomplete(slot: str, model: str) -> None:
    """Verify fabric modules identified by slot or model do not affect tracked roles."""
    platform = parse_eos_platform("DCS-7816-CH")
    assert platform is not None

    parsed = parse_eos_platform_modules(platform, {"modules": {slot: {"modelName": model}}})

    assert not parsed.supervisors
    assert not parsed.switch_cards
    assert not parsed.line_cards
    assert parsed.completeness.supervisors
    assert parsed.completeness.switch_cards
    assert parsed.completeness.line_cards
