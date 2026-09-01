# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista EOS platform identity parsing and family resolution helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class PlatformComponentRole(str, Enum):
    """Roles that can contribute to an EOS platform identity."""

    CHASSIS = "chassis"
    SUPERVISOR = "supervisor"
    SWITCH_CARD = "switch_card"
    LINE_CARD = "line_card"


class PlatformFamily(str, Enum):
    """Stable EOS platform families resolved from chassis and component models."""

    SERIES_720_D = "720D Series"
    SERIES_720_XP = "720XP Series"
    SERIES_722_XPM = "722XPM Series"
    SERIES_755_758 = "755/758 Series"
    SERIES_7010 = "7010 Series"
    SERIES_7010_X = "7010X Series"
    SERIES_7020_R = "7020R Series"
    SERIES_7160 = "7160 Series"
    SERIES_7050_X = "7050X Series"
    SERIES_7050_X2 = "7050X2 Series"
    SERIES_7050_X3 = "7050X3 Series"
    SERIES_7050_X4 = "7050X4 Series"
    SERIES_7060_X = "7060X Series"
    SERIES_7060_X2 = "7060X2 Series"
    SERIES_7060_X4 = "7060X4 Series"
    SERIES_7060_X5 = "7060X5 Series"
    SERIES_7060_X6 = "7060X6 Series"
    SERIES_7250_X = "7250X Series"
    SERIES_7260_X = "7260X Series"
    SERIES_7260_X3 = "7260X3 Series"
    SERIES_7280_E = "7280E Series"
    SERIES_7280_R = "7280R Series"
    SERIES_7280_R2 = "7280R2 Series"
    SERIES_7280_R3 = "7280R3 Series"
    SERIES_7280_R4 = "7280R4 Series"
    SERIES_7300_X = "7300X Series"
    SERIES_7300_X3 = "7300X3 Series"
    SERIES_7320_X = "7320X Series"
    SERIES_7358_X4 = "7358X4 Series"
    SERIES_7368_X4 = "7368X4 Series"
    SERIES_7388_X5 = "7388X5 Series"
    SERIES_7500_E = "7500E Series"
    SERIES_7500_R = "7500R Series"
    SERIES_7500_R2 = "7500R2 Series"
    SERIES_7500_R3 = "7500R3 Series"
    SERIES_7800_R3 = "7800R3 Series"
    SERIES_7800_R4 = "7800R4 Series"


@dataclass(frozen=True, slots=True)
class PlatformComponentIdentity:
    """Normalized identity for one chassis or installed modular component."""

    model: str
    role: PlatformComponentRole
    slot: str | None = None
    platform_families: frozenset[PlatformFamily] = frozenset()


@dataclass(frozen=True, slots=True)
class PlatformIdentityCompleteness:
    """Whether each component role has sufficient evidence for negative family matches."""

    chassis: bool
    supervisors: bool
    switch_cards: bool
    line_cards: bool


@dataclass(frozen=True, slots=True)
class PlatformIdentity:
    """Structured EOS chassis and component identities discovered during device refresh."""

    chassis: PlatformComponentIdentity
    supervisors: tuple[PlatformComponentIdentity, ...]
    switch_cards: tuple[PlatformComponentIdentity, ...]
    line_cards: tuple[PlatformComponentIdentity, ...]
    platform_families: frozenset[PlatformFamily]
    completeness: PlatformIdentityCompleteness

    def __str__(self) -> str:
        """Return the normalized chassis model."""
        return self.chassis.model

    def to_dict(self) -> dict[str, object]:
        """Return the structured identity as a JSON-compatible dictionary."""

        def component_to_dict(component: PlatformComponentIdentity) -> dict[str, object]:
            return {
                "model": component.model,
                "role": component.role.value,
                "slot": component.slot,
                "platform_families": sorted(family.value for family in component.platform_families),
            }

        return {
            "chassis": component_to_dict(self.chassis),
            "supervisors": [component_to_dict(component) for component in self.supervisors],
            "switch_cards": [component_to_dict(component) for component in self.switch_cards],
            "line_cards": [component_to_dict(component) for component in self.line_cards],
            "platform_families": sorted(family.value for family in self.platform_families),
            "completeness": {
                "chassis": self.completeness.chassis,
                "supervisors": self.completeness.supervisors,
                "switch_cards": self.completeness.switch_cards,
                "line_cards": self.completeness.line_cards,
            },
        }


@dataclass(frozen=True, slots=True)
class _PlatformFamilyRule:
    """Associate model-name patterns for one component role with a platform family."""

    role: PlatformComponentRole
    patterns: tuple[re.Pattern[str], ...]


def _rule(role: PlatformComponentRole, *patterns: str) -> _PlatformFamilyRule:
    """Build one platform family rule from regular-expression strings."""
    return _PlatformFamilyRule(role=role, patterns=tuple(re.compile(pattern) for pattern in patterns))


PLATFORM_FAMILY_RULES: dict[PlatformFamily, tuple[_PlatformFamilyRule, ...]] = {
    PlatformFamily.SERIES_720_D: (_rule(PlatformComponentRole.CHASSIS, r"^CCS-720D[FTP]-.*$"),),
    PlatformFamily.SERIES_720_XP: (_rule(PlatformComponentRole.CHASSIS, r"^CCS-720XP-.*$"),),
    PlatformFamily.SERIES_722_XPM: (_rule(PlatformComponentRole.CHASSIS, r"^CCS-722XPM-.*$"),),
    PlatformFamily.SERIES_755_758: (_rule(PlatformComponentRole.CHASSIS, r"^CCS-75[58]-CH.*$"),),
    PlatformFamily.SERIES_7010: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7010T-.*$"),),
    PlatformFamily.SERIES_7010_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7010TX-.*$"),),
    PlatformFamily.SERIES_7020_R: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7020[ST]R[A-Z]*-.*$"),),
    PlatformFamily.SERIES_7160: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7160-.*$"),),
    PlatformFamily.SERIES_7050_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7050[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7050_X2: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7050[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7050_X3: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7050[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7050_X4: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7050[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7060[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7060_X2: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7060[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7060_X4: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7060[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X5: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7060[A-Z]*X5.*$"),),
    PlatformFamily.SERIES_7060_X6: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7060[A-Z]*X6.*$"),),
    PlatformFamily.SERIES_7250_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7250[A-WY-Z]*X.*$"),),
    PlatformFamily.SERIES_7260_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7260[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7260_X3: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7260[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7280_E: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7280SE-.*$"),),
    PlatformFamily.SERIES_7280_R: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7280[CQST]R(?!\d).*$"),),
    PlatformFamily.SERIES_7280_R2: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7280[CS]R2.*$"),),
    PlatformFamily.SERIES_7280_R3: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7280[CDPST]R3.*$"),),
    PlatformFamily.SERIES_7280_R4: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-7280R4.*$"),),
    PlatformFamily.SERIES_7300_X: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7300X(?!\d)-.*-LC$"),),
    PlatformFamily.SERIES_7300_X3: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7300X3-.*-LC$"),),
    PlatformFamily.SERIES_7320_X: (_rule(PlatformComponentRole.CHASSIS, r"^DCS-732[48](?:-[FR])?$"),),
    PlatformFamily.SERIES_7358_X4: (_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7358X4-SC$"),),
    PlatformFamily.SERIES_7368_X4: (_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7368X4-SC$"),),
    PlatformFamily.SERIES_7388_X5: (_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7388X5-SC$"),),
    PlatformFamily.SERIES_7500_E: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500E-.*-LC$"),),
    PlatformFamily.SERIES_7500_R: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R(?!\d)-.*-LC$"),),
    PlatformFamily.SERIES_7500_R2: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R2[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7500_R3: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R3[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7800_R3: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7800R3[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7800_R4: (_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7800R4[A-Z]*-.*-LC$"),),
}


_MODULAR_CHASSIS_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"^CCS-75[58]-CH.*$",
        r"^DCS-73(?:04|08|16)(?:-[FR])?$",
        r"^DCS-732[48](?:-[FR])?$",
        r"^(?:DCS-)?(?:7358|7368)(?:-CH)?(?:-[FR])?$",
        r"^(?:DCS-)?7388(?:-CH)?(?:-[FR])?$",
        r"^DCS-75(?:04|08|12|16)(?:N|-CH)?(?:-[FR])?$",
        r"^DCS-78(?:04|08|12|16[BL]?)-CH(?:-[FR])?$",
    )
)

_NOT_INSERTED_MODELS = {"NOT INSERTED", "NOTINSERTED"}
_GENERIC_COMPONENT_MODELS = {"SUP", "SC", "LC"}
_MODULE_COMPONENT_ROLES = frozenset(
    {
        PlatformComponentRole.SUPERVISOR,
        PlatformComponentRole.SWITCH_CARD,
        PlatformComponentRole.LINE_CARD,
    }
)


def normalize_platform_model(model: object) -> str | None:
    """Return a normalized EOS model name, or ``None`` for unavailable evidence."""
    if not isinstance(model, str) or not (normalized := model.strip().upper()):
        return None
    return normalized


def resolve_platform_families(model: str, role: PlatformComponentRole) -> frozenset[PlatformFamily]:
    """Resolve all stable platform families associated with a normalized component model."""
    normalized_model = normalize_platform_model(model)
    if normalized_model is None:
        return frozenset()
    return frozenset(
        family
        for family, rules in PLATFORM_FAMILY_RULES.items()
        for rule in rules
        if rule.role is role and any(pattern.fullmatch(normalized_model) for pattern in rule.patterns)
    )


def is_modular_platform(model: str) -> bool:
    """Return whether a chassis model requires structured module discovery."""
    normalized_model = normalize_platform_model(model)
    return normalized_model is not None and any(pattern.fullmatch(normalized_model) for pattern in _MODULAR_CHASSIS_PATTERNS)


def _component(model: str, role: PlatformComponentRole, slot: str | None = None) -> PlatformComponentIdentity:
    """Build a normalized component identity and resolve its platform families."""
    return PlatformComponentIdentity(model=model, role=role, slot=slot, platform_families=resolve_platform_families(model, role))


def _platform_identity(
    chassis: PlatformComponentIdentity,
    *,
    supervisors: tuple[PlatformComponentIdentity, ...] = (),
    switch_cards: tuple[PlatformComponentIdentity, ...] = (),
    line_cards: tuple[PlatformComponentIdentity, ...] = (),
    completeness: PlatformIdentityCompleteness,
) -> PlatformIdentity:
    """Build a platform identity and aggregate all resolved families."""
    components = (chassis, *supervisors, *switch_cards, *line_cards)
    return PlatformIdentity(
        chassis=chassis,
        supervisors=supervisors,
        switch_cards=switch_cards,
        line_cards=line_cards,
        platform_families=frozenset(family for component in components for family in component.platform_families),
        completeness=completeness,
    )


def parse_eos_platform(model_name: object) -> PlatformIdentity | None:
    """Parse an EOS model name into an initial chassis identity."""
    model = normalize_platform_model(model_name)
    if model is None:
        return None

    chassis = _component(model, PlatformComponentRole.CHASSIS)
    modules_complete = not is_modular_platform(model)
    return _platform_identity(
        chassis,
        completeness=PlatformIdentityCompleteness(
            chassis=True,
            supervisors=modules_complete,
            switch_cards=modules_complete,
            line_cards=modules_complete,
        ),
    )


def _role_from_slot(slot: str) -> PlatformComponentRole | None:
    """Resolve a component role from a structured module slot name."""
    normalized_slot = re.sub(r"[^A-Z]", "", slot.upper())
    if normalized_slot.startswith("SUPERVISOR"):
        return PlatformComponentRole.SUPERVISOR
    if normalized_slot.startswith("SWITCHCARD"):
        return PlatformComponentRole.SWITCH_CARD
    if normalized_slot.startswith("LINECARD"):
        return PlatformComponentRole.LINE_CARD
    return None


def _role_from_model(model: str) -> PlatformComponentRole | None:
    """Resolve a component role from normalized EOS model naming conventions."""
    if model == "SUP" or re.search(r"(?:^|-)SUP(?:-|$)", model) is not None:
        return PlatformComponentRole.SUPERVISOR
    if model == "SC" or re.search(r"(?:^|-)SC(?:-|$)", model) is not None:
        return PlatformComponentRole.SWITCH_CARD
    if model == "LC" or re.search(r"(?:^|-)LC(?:-|$)", model) is not None or re.fullmatch(r"(?:DCS-)?(?:7358|7368)-\d+[A-Z]*", model):
        return PlatformComponentRole.LINE_CARD
    return None


def _is_ignored_module(slot: str, model: str) -> bool:
    """Return whether a module is known not to contribute to the requested identity roles."""
    normalized_slot = re.sub(r"[^A-Z]", "", slot.upper())
    return normalized_slot.startswith("FABRIC") or model.endswith("-FM")


def _parse_eos_module(slot: object, module_data: object) -> tuple[PlatformComponentIdentity | None, frozenset[PlatformComponentRole]]:
    """Parse one module and return any component plus roles with unavailable evidence."""
    if not isinstance(slot, str):
        return None, _MODULE_COMPONENT_ROLES
    role_from_slot = _role_from_slot(slot)
    unavailable_role = _MODULE_COMPONENT_ROLES if role_from_slot is None else frozenset({role_from_slot})
    if not isinstance(module_data, Mapping):
        return None, unavailable_role

    model = normalize_platform_model(module_data.get("modelName"))
    if model in _NOT_INSERTED_MODELS:
        return None, frozenset()
    if model is None:
        return None, unavailable_role

    role = role_from_slot or _role_from_model(model)
    if role is None:
        return (None, frozenset()) if _is_ignored_module(slot, model) else (None, _MODULE_COMPONENT_ROLES)
    incomplete_roles = frozenset({role}) if model in _GENERIC_COMPONENT_MODELS else frozenset()
    return _component(model, role, slot), incomplete_roles


def parse_eos_platform_modules(platform: PlatformIdentity, show_module_output: Mapping[str, object] | None) -> PlatformIdentity:
    """Augment a modular chassis identity from structured ``show module`` output.

    Valid component identities are retained from partially malformed evidence. Module
    completeness remains false in that case so negative family predicates stay unknown.
    """
    if not is_modular_platform(platform.chassis.model) or show_module_output is None:
        return platform

    modules = show_module_output.get("modules")
    if not isinstance(modules, Mapping) or not modules:
        return platform

    components: dict[PlatformComponentRole, list[PlatformComponentIdentity]] = {
        PlatformComponentRole.SUPERVISOR: [],
        PlatformComponentRole.SWITCH_CARD: [],
        PlatformComponentRole.LINE_CARD: [],
    }
    completeness = {
        PlatformComponentRole.SUPERVISOR: True,
        PlatformComponentRole.SWITCH_CARD: True,
        PlatformComponentRole.LINE_CARD: True,
    }
    for slot, module_data in sorted(modules.items(), key=lambda item: str(item[0])):
        component, unavailable_roles = _parse_eos_module(slot, module_data)
        if component is not None:
            components[component.role].append(component)
        for unavailable_role in unavailable_roles:
            completeness[unavailable_role] = False

    return _platform_identity(
        platform.chassis,
        supervisors=tuple(components[PlatformComponentRole.SUPERVISOR]),
        switch_cards=tuple(components[PlatformComponentRole.SWITCH_CARD]),
        line_cards=tuple(components[PlatformComponentRole.LINE_CARD]),
        completeness=PlatformIdentityCompleteness(
            chassis=True,
            supervisors=completeness[PlatformComponentRole.SUPERVISOR],
            switch_cards=completeness[PlatformComponentRole.SWITCH_CARD],
            line_cards=completeness[PlatformComponentRole.LINE_CARD],
        ),
    )


def _components_for_role(platform: PlatformIdentity, role: PlatformComponentRole) -> tuple[PlatformComponentIdentity, ...]:
    """Return platform components for one role."""
    if role is PlatformComponentRole.CHASSIS:
        return (platform.chassis,)
    if role is PlatformComponentRole.SUPERVISOR:
        return platform.supervisors
    if role is PlatformComponentRole.SWITCH_CARD:
        return platform.switch_cards
    return platform.line_cards


def _role_is_complete(platform: PlatformIdentity, role: PlatformComponentRole) -> bool:
    """Return whether one role has complete discovery evidence."""
    if role is PlatformComponentRole.CHASSIS:
        return platform.completeness.chassis
    if role is PlatformComponentRole.SUPERVISOR:
        return platform.completeness.supervisors
    if role is PlatformComponentRole.SWITCH_CARD:
        return platform.completeness.switch_cards
    return platform.completeness.line_cards


def platform_matches_families(
    platform: PlatformIdentity | None,
    families: Iterable[PlatformFamily],
    *,
    role: PlatformComponentRole | None = None,
) -> bool | None:
    """Evaluate a family predicate using role-specific evidence.

    Returns ``True`` on a positive match, ``False`` when all relevant evidence is
    complete without a match, and ``None`` when evidence needed for a negative answer
    is unavailable.
    """
    if platform is None:
        return None

    requested_families = frozenset(families)
    relevant_roles = {rule.role for family in requested_families for rule in PLATFORM_FAMILY_RULES[family] if role is None or rule.role is role}
    if not relevant_roles:
        return False
    if any(component.platform_families & requested_families for relevant_role in relevant_roles for component in _components_for_role(platform, relevant_role)):
        return True
    return False if all(_role_is_complete(platform, relevant_role) for relevant_role in relevant_roles) else None
