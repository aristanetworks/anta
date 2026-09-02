# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Parse EOS hardware inventory into a structured platform identity.

The identity records the normalized system and modular-component models by role. A
`PlatformFamily` is a stable semantic classification of related hardware that
lets consumers such as security-advisory tests declare their scope without parsing
raw EOS model strings.

`PLATFORM_FAMILY_RULES` maps role-specific model patterns to those families.
`parse_eos_platform` builds the initial identity from the `show version` system
model. Fixed systems and modular chassis have distinct component roles. Modular
platforms are then enriched by `parse_eos_platform_modules` using
`show module` inventory, since an installed switch or line card can identify the
family more precisely than its chassis.

Resolved component families are aggregated on `PlatformIdentity`. Module entries
that cannot yet be classified are retained with the `UNKNOWN` role so consumers
can decide whether they are relevant.
"""

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

    FIXED_SYSTEM = "fixed_system"
    CHASSIS = "chassis"
    SUPERVISOR = "supervisor"
    SWITCH_CARD = "switch_card"
    LINE_CARD = "line_card"
    FABRIC_CARD = "fabric_card"
    UNKNOWN = "unknown"


class PlatformFamily(str, Enum):
    """Stable hardware classifications used when evaluating platform scope.

    A family groups model names that share the hardware characteristic relevant to
    an ANTA consumer. Consumers compare these values instead of parsing raw EOS
    model strings. `PLATFORM_FAMILY_RULES` is the single mapping from component
    identities to these families.
    """

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
    """Normalized identity for one modular chassis or installed module."""

    model: str | None
    role: PlatformComponentRole
    slot: str | None = None
    platform_families: frozenset[PlatformFamily] = frozenset()


@dataclass(frozen=True, slots=True)
class PlatformIdentity:
    """Structured EOS system and component identities discovered during device refresh.

    `platform_families` aggregates the families resolved from the system and every
    discovered module. Unknown module roles are retained without preventing known
    components from being used.
    """

    model: str
    chassis: PlatformComponentIdentity | None
    modules: tuple[PlatformComponentIdentity, ...]
    platform_families: frozenset[PlatformFamily]

    def __str__(self) -> str:
        """Return the normalized system model.

        Returns
        -------
        str
            Normalized system model.
        """
        return self.model

    def to_dict(self) -> dict[str, object]:
        """Return the structured platform identity.

        Returns
        -------
        dict[str, object]
            A JSON-compatible dictionary containing the system, modules, and
            resolved families.
        """

        def component_to_dict(component: PlatformComponentIdentity) -> dict[str, object]:
            return {
                "model": component.model,
                "role": component.role.value,
                "slot": component.slot,
                "platform_families": sorted(family.value for family in component.platform_families),
            }

        return {
            "model": self.model,
            "chassis": component_to_dict(self.chassis) if self.chassis is not None else None,
            "modules": [component_to_dict(component) for component in self.modules],
            "platform_families": sorted(family.value for family in self.platform_families),
        }


@dataclass(frozen=True, slots=True)
class _PlatformFamilyRule:
    """Associate model-name patterns for one component role with a platform family.

    The role is part of the rule because an enclosure, switch card, and line card
    can carry different identity information even when their model names are
    related.
    """

    role: PlatformComponentRole
    patterns: tuple[re.Pattern[str], ...]


def _rule(role: PlatformComponentRole, *patterns: str) -> _PlatformFamilyRule:
    """Build a platform-family resolution rule.

    Parameters
    ----------
    role : PlatformComponentRole
        Component role to which the patterns apply.
    *patterns : str
        Regular expressions matching component models.

    Returns
    -------
    _PlatformFamilyRule
        The compiled platform-family rule.
    """
    return _PlatformFamilyRule(role=role, patterns=tuple(re.compile(pattern) for pattern in patterns))


PLATFORM_FAMILY_RULES: dict[PlatformFamily, tuple[_PlatformFamilyRule, ...]] = {
    PlatformFamily.SERIES_720_D: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^CCS-720D[FTP]-.*$"),),
    PlatformFamily.SERIES_720_XP: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^CCS-720XP-.*$"),),
    PlatformFamily.SERIES_722_XPM: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^CCS-722XPM-.*$"),),
    PlatformFamily.SERIES_755_758: (_rule(PlatformComponentRole.CHASSIS, r"^CCS-75[58]-CH.*$"),),
    PlatformFamily.SERIES_7010: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7010T-.*$"),),
    PlatformFamily.SERIES_7010_X: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7010TX-.*$"),),
    PlatformFamily.SERIES_7020_R: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7020[ST]R[A-Z]*-.*$"),),
    PlatformFamily.SERIES_7160: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7160-.*$"),),
    PlatformFamily.SERIES_7050_X: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7050[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7050_X2: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7050[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7050_X3: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7050[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7050_X4: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7050[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7060[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7060_X2: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7060[A-Z]*X2.*$"),),
    PlatformFamily.SERIES_7060_X4: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7060[A-Z]*X4.*$"),),
    PlatformFamily.SERIES_7060_X5: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7060[A-Z]*X5.*$"),),
    PlatformFamily.SERIES_7060_X6: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7060[A-Z]*X6.*$"),),
    PlatformFamily.SERIES_7250_X: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7250[A-WY-Z]*X.*$"),),
    PlatformFamily.SERIES_7260_X: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7260[A-Z]*X(?!\d).*$"),),
    PlatformFamily.SERIES_7260_X3: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7260[A-Z]*X3.*$"),),
    PlatformFamily.SERIES_7280_E: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7280SE-.*$"),),
    PlatformFamily.SERIES_7280_R: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7280[CQST]R(?!\d).*$"),),
    PlatformFamily.SERIES_7280_R2: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7280[CS]R2.*$"),),
    PlatformFamily.SERIES_7280_R3: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7280[CDPST]R3.*$"),),
    PlatformFamily.SERIES_7280_R4: (_rule(PlatformComponentRole.FIXED_SYSTEM, r"^DCS-7280R4.*$"),),
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


def normalize_platform_model(model: str | None) -> str | None:
    """Normalize an EOS model name.

    Parameters
    ----------
    model : str | None
        Model value to validate and normalize.

    Returns
    -------
    str | None
        The stripped, uppercase model name, or `None` when the value is not a
        non-empty string.
    """
    if not isinstance(model, str) or not (normalized := model.strip().upper()):
        return None
    return normalized


def resolve_platform_families(model: str, role: PlatformComponentRole) -> frozenset[PlatformFamily]:
    """Resolve semantic platform families from one component model and its role.

    Resolution may return more than one family when classifications overlap. The
    results are attached to the component and later aggregated by
    `PlatformIdentity`.

    Parameters
    ----------
    model : str
        Component model to resolve.
    role : PlatformComponentRole
        Role of the component identified by `model`.

    Returns
    -------
    frozenset[PlatformFamily]
        All platform families matched by the model and role.
    """
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
    """Return whether a chassis requires module discovery.

    Parameters
    ----------
    model : str
        Chassis model to evaluate.

    Returns
    -------
    bool
        `True` when the chassis requires structured module discovery, otherwise
        `False`.
    """
    normalized_model = normalize_platform_model(model)
    return normalized_model is not None and any(pattern.fullmatch(normalized_model) for pattern in _MODULAR_CHASSIS_PATTERNS)


def _component(model: str | None, role: PlatformComponentRole, slot: str | None = None) -> PlatformComponentIdentity:
    """Build a normalized component identity.

    Parameters
    ----------
    model : str | None
        Normalized component model, if EOS reports one.
    role : PlatformComponentRole
        Role of the component.
    slot : str | None
        Inventory slot containing the component, if available.

    Returns
    -------
    PlatformComponentIdentity
        The component identity with its resolved platform families.
    """
    families = resolve_platform_families(model, role) if model is not None else frozenset()
    return PlatformComponentIdentity(model=model, role=role, slot=slot, platform_families=families)


def _platform_identity(
    model: str,
    chassis: PlatformComponentIdentity | None,
    *,
    modules: tuple[PlatformComponentIdentity, ...] = (),
) -> PlatformIdentity:
    """Build a platform identity and aggregate component families.

    Parameters
    ----------
    model : str
        Normalized model reported by `show version`.
    chassis : PlatformComponentIdentity | None
        Modular chassis identity, if the model is a known modular enclosure.
    modules : tuple[PlatformComponentIdentity, ...]
        Discovered module identities in deterministic slot order.

    Returns
    -------
    PlatformIdentity
        The structured platform identity.
    """
    base_families = chassis.platform_families if chassis is not None else resolve_platform_families(model, PlatformComponentRole.FIXED_SYSTEM)
    return PlatformIdentity(
        model=model,
        chassis=chassis,
        modules=modules,
        platform_families=frozenset((*base_families, *(family for component in modules for family in component.platform_families))),
    )


def parse_eos_platform(model_name: str | None) -> PlatformIdentity | None:
    """Parse an EOS model name into an initial system identity.

    Parameters
    ----------
    model_name : str | None
        System model reported by EOS.

    Returns
    -------
    PlatformIdentity | None
        The initial platform identity, or `None` when the system model is invalid.
    """
    model = normalize_platform_model(model_name)
    if model is None:
        return None

    chassis = _component(model, PlatformComponentRole.CHASSIS) if is_modular_platform(model) else None
    return _platform_identity(model, chassis)


def _role_from_slot(slot: str) -> PlatformComponentRole | None:
    """Resolve a component role from a module slot name.

    Parameters
    ----------
    slot : str
        Module slot name reported by EOS.

    Returns
    -------
    PlatformComponentRole | None
        The resolved component role, or `None` for an unrecognized slot.
    """
    normalized_slot = re.sub(r"[^A-Z]", "", slot.upper())
    if normalized_slot.startswith("SUPERVISOR"):
        return PlatformComponentRole.SUPERVISOR
    if normalized_slot.startswith("SWITCHCARD"):
        return PlatformComponentRole.SWITCH_CARD
    if normalized_slot.startswith("LINECARD"):
        return PlatformComponentRole.LINE_CARD
    if normalized_slot.startswith("FABRIC"):
        return PlatformComponentRole.FABRIC_CARD
    return None


def _role_from_model(model: str) -> PlatformComponentRole | None:
    """Resolve a component role from its model name.

    Parameters
    ----------
    model : str
        Normalized component model.

    Returns
    -------
    PlatformComponentRole | None
        The resolved component role, or `None` for an unrecognized model.
    """
    if re.search(r"(?:^|-)SUP(?:\d+[A-Z]*)?(?:-|$)", model) is not None:
        return PlatformComponentRole.SUPERVISOR
    if model == "SC" or re.search(r"(?:^|-)SC(?:-|$)", model) is not None:
        return PlatformComponentRole.SWITCH_CARD
    if model == "LC" or re.search(r"(?:^|-)LC(?:-|$)", model) is not None or re.fullmatch(r"(?:DCS-)?(?:7358|7368)-\d+[A-Z]*", model):
        return PlatformComponentRole.LINE_CARD
    if re.search(r"(?:^|-)(?:FM|FCM)(?:-|$)", model) is not None:
        return PlatformComponentRole.FABRIC_CARD
    return None


def _role_from_description(description: str) -> PlatformComponentRole | None:
    """Resolve a component role from its EOS type description.

    Parameters
    ----------
    description : str
        Module type description reported by EOS.

    Returns
    -------
    PlatformComponentRole | None
        The resolved component role, or `None` for an unrecognized description.
    """
    normalized_description = re.sub(r"[^A-Z]", "", description.upper())
    if "SUPERVISOR" in normalized_description:
        return PlatformComponentRole.SUPERVISOR
    if "SWITCHCARD" in normalized_description:
        return PlatformComponentRole.SWITCH_CARD
    if "LINECARD" in normalized_description:
        return PlatformComponentRole.LINE_CARD
    if "FABRICMODULE" in normalized_description or "FABRICCARD" in normalized_description:
        return PlatformComponentRole.FABRIC_CARD
    return None


def _parse_eos_module(slot: str, module_data: Mapping[str, object]) -> PlatformComponentIdentity | None:
    """Parse one module inventory entry.

    Parameters
    ----------
    slot : str
        Module slot name.
    module_data : Mapping[str, object]
        Inventory data for the slot.

    Returns
    -------
    PlatformComponentIdentity | None
        The parsed module, or `None` for an explicitly empty slot.
    """
    model_name = module_data.get("modelName")
    model = normalize_platform_model(model_name if isinstance(model_name, str) else None)
    if model in _NOT_INSERTED_MODELS:
        return None
    description = module_data.get("typeDescription")
    role = _role_from_slot(slot) or (_role_from_model(model) if model is not None else None)
    if role is None and isinstance(description, str):
        role = _role_from_description(description)
    return _component(model, role or PlatformComponentRole.UNKNOWN, slot)


def parse_eos_platform_modules(platform: PlatformIdentity, show_module_output: Mapping[str, object] | None) -> PlatformIdentity:
    """Augment a platform identity from structured `show module` output.

    Every reported module is retained. Entries that cannot be classified from their
    slot, model, or type description use the `UNKNOWN` role for later evaluation.

    Parameters
    ----------
    platform : PlatformIdentity
        Initial system identity to enrich.
    show_module_output : Mapping[str, object] | None
        Structured `show module` output, if available.

    Returns
    -------
    PlatformIdentity
        The enriched identity, or the original identity when module inventory is
        unavailable.
    """
    if show_module_output is None:
        return platform

    modules = show_module_output.get("modules")
    if not isinstance(modules, Mapping) or not modules:
        return platform

    components: list[PlatformComponentIdentity] = []
    for raw_slot, module_data in sorted(modules.items(), key=lambda item: str(item[0])):
        slot = raw_slot if isinstance(raw_slot, str) else str(raw_slot)
        normalized_data = module_data if isinstance(module_data, Mapping) else {}
        component = _parse_eos_module(slot, normalized_data)
        if component is not None:
            components.append(component)

    return _platform_identity(platform.model, platform.chassis, modules=tuple(components))


def _components_for_role(platform: PlatformIdentity, role: PlatformComponentRole) -> tuple[PlatformComponentIdentity, ...]:
    """Return platform components for one role.

    Parameters
    ----------
    platform : PlatformIdentity
        Platform identity containing the components.
    role : PlatformComponentRole
        Component role to select.

    Returns
    -------
    tuple[PlatformComponentIdentity, ...]
        Components associated with the requested role.
    """
    if role is PlatformComponentRole.CHASSIS:
        return (platform.chassis,) if platform.chassis is not None else ()
    if role is PlatformComponentRole.FIXED_SYSTEM:
        return ()
    return tuple(component for component in platform.modules if component.role is role)


def platform_matches_families(
    platform: PlatformIdentity | None,
    families: Iterable[PlatformFamily],
    *,
    role: PlatformComponentRole | None = None,
) -> bool | None:
    """Evaluate whether a platform belongs to any requested semantic family.

    Security advisories and other platform-scoped consumers use this helper rather
    than matching EOS model strings directly. When `role` is provided, only
    evidence from that component role participates in the decision.

    Parameters
    ----------
    platform : PlatformIdentity | None
        Platform identity to evaluate, if available.
    families : Iterable[PlatformFamily]
        Platform families accepted by the consumer.
    role : PlatformComponentRole | None
        Optional component role to which matching is restricted.

    Returns
    -------
    bool | None
        `True` on a positive match, `False` when no discovered component matches,
        or `None` when no platform identity is available.
    """
    if platform is None:
        return None

    requested_families = frozenset(families)
    relevant_roles = {rule.role for family in requested_families for rule in PLATFORM_FAMILY_RULES[family] if role is None or rule.role is role}
    if not relevant_roles:
        return False
    family_match = bool(platform.platform_families & requested_families) if role is None else False
    if role is PlatformComponentRole.FIXED_SYSTEM:
        family_match = bool(resolve_platform_families(platform.model, role) & requested_families)
    elif role is not None:
        family_match = any(
            component.platform_families & requested_families for relevant_role in relevant_roles for component in _components_for_role(platform, relevant_role)
        )
    if family_match:
        return True
    if platform.chassis is not None and (not platform.modules or any(component.role is PlatformComponentRole.UNKNOWN for component in platform.modules)):
        return None
    return False
