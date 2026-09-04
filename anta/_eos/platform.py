# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Parse EOS hardware inventory into a structured platform identity.

The identity records the normalized system type and modular-component models by role. A
`PlatformFamily` is a stable semantic classification of related EOS products or hardware that
lets consumers such as security-advisory tests declare their scope without parsing
raw EOS model strings.

System-model rules independently resolve the physical platform type and any
system-level families. Module-family rules map role-specific models to families.
`parse_eos_platform` builds the initial identity from the `show version` system
model. Chassis platforms are then enriched by `parse_eos_platform_modules` using
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

from anta._eos.parsing import ParseFail, ParseFailureReason, ParseResult, ParseSuccessful

if TYPE_CHECKING:
    from collections.abc import Iterable


class PlatformComponentRole(str, Enum):
    """Installed module roles that can contribute to an EOS platform identity."""

    SUPERVISOR = "supervisor"
    SWITCH_CARD = "switch_card"
    LINE_CARD = "line_card"
    FABRIC_CARD = "fabric_card"
    UNKNOWN = "unknown"


class PlatformType(str, Enum):
    """Deployment form of an EOS system model."""

    FIXED = "fixed"
    CHASSIS = "chassis"
    VIRTUAL = "virtual"
    APPLIANCE = "appliance"
    UNKNOWN = "unknown"


class PlatformFamily(str, Enum):
    """Stable product classifications used when evaluating platform scope.

    A family groups model names that share the product characteristic relevant to
    an ANTA consumer. Consumers compare these values instead of parsing raw EOS
    model strings. System and module rules map identities to these families
    independently of the physical platform type.
    """

    SERIES_720_D = "720D Series"
    SERIES_720_XP = "720XP Series"
    SERIES_720_XDM = "720XDM Series"
    SERIES_722_XPM = "722XPM Series"
    SERIES_755_758 = "755/758 Series"
    SERIES_710 = "710 Series"
    SERIES_7010 = "7010 Series"
    SERIES_7010_X = "7010X Series"
    SERIES_7020_R = "7020R Series"
    SERIES_7020_R4 = "7020R4 Series"
    SERIES_7130 = "7130 Series"
    SERIES_7150 = "7150 Series"
    SERIES_7160 = "7160 Series"
    SERIES_7170 = "7170 Series"
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
    SERIES_7289_R3A = "7289R3A Series"
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
    SERIES_7700_R4 = "7700R4 Series"
    SERIES_7720_R4 = "7720R4 Series"
    SERIES_7800_R3 = "7800R3 Series"
    SERIES_7800_R4 = "7800R4 Series"
    AWE_5000 = "AWE 5000 Series"
    AWE_7200_R = "AWE 7200R Series"
    CLOUDEOS = "CloudEOS"
    CEOS_LAB = "cEOS-lab"
    VEOS_LAB = "vEOS-lab"
    CLOUDVISION_EXCHANGE = "CloudVision eXchange"


@dataclass(frozen=True, slots=True)
class PlatformComponentIdentity:
    """Normalized identity for one installed module."""

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
    type: PlatformType
    modules: tuple[PlatformComponentIdentity, ...]
    platform_families: frozenset[PlatformFamily]

    def __str__(self) -> str:
        """Return the system model reported by EOS.

        Returns
        -------
        str
            System model reported by EOS, with surrounding whitespace removed.
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
            "type": self.type.value,
            "modules": [component_to_dict(component) for component in self.modules],
            "platform_families": sorted(family.value for family in self.platform_families),
        }


@dataclass(frozen=True, slots=True)
class _SystemPlatformRule:
    """Resolve deployment type and optional families from one system model rule."""

    type: PlatformType
    families: frozenset[PlatformFamily]
    patterns: tuple[re.Pattern[str], ...]


@dataclass(frozen=True, slots=True)
class _ModuleFamilyRule:
    """Resolve platform families from models for one installed module role."""

    role: PlatformComponentRole
    patterns: tuple[re.Pattern[str], ...]


def _system_rule(
    platform_type: PlatformType,
    *patterns: str,
    families: tuple[PlatformFamily, ...] = (),
) -> _SystemPlatformRule:
    """Build a system-model rule with independent type and family results."""
    return _SystemPlatformRule(
        type=platform_type,
        families=frozenset(families),
        patterns=tuple(re.compile(pattern) for pattern in patterns),
    )


def _module_rule(role: PlatformComponentRole, *patterns: str) -> _ModuleFamilyRule:
    """Build a role-specific module-family resolution rule."""
    return _ModuleFamilyRule(role=role, patterns=tuple(re.compile(pattern) for pattern in patterns))


SYSTEM_PLATFORM_RULES: tuple[_SystemPlatformRule, ...] = (
    _system_rule(PlatformType.FIXED, r"^CCS-720D[FTP]-.*$", families=(PlatformFamily.SERIES_720_D,)),
    _system_rule(PlatformType.FIXED, r"^CCS-720XP-.*$", families=(PlatformFamily.SERIES_720_XP,)),
    _system_rule(PlatformType.FIXED, r"^CCS-720XDM-.*$", families=(PlatformFamily.SERIES_720_XDM,)),
    _system_rule(PlatformType.FIXED, r"^CCS-72[02]XPM-.*$", families=(PlatformFamily.SERIES_722_XPM,)),
    _system_rule(PlatformType.CHASSIS, r"^CCS-75[58]-CH.*$", families=(PlatformFamily.SERIES_755_758,)),
    _system_rule(PlatformType.FIXED, r"^CCS-710[A-Z0-9]*-.*$", families=(PlatformFamily.SERIES_710,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7010T-.*$", families=(PlatformFamily.SERIES_7010,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7010TX-.*$", families=(PlatformFamily.SERIES_7010_X,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7020[ST]R[A-Z]*-.*$", families=(PlatformFamily.SERIES_7020_R,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7020H?R4M?-.*$", families=(PlatformFamily.SERIES_7020_R4,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7050[A-Z]*X(?!\d).*$", families=(PlatformFamily.SERIES_7050_X,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7050[A-Z]*X2.*$", families=(PlatformFamily.SERIES_7050_X2,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7050[A-Z]*X3.*$", families=(PlatformFamily.SERIES_7050_X3,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7050[A-Z]*X4.*$", families=(PlatformFamily.SERIES_7050_X4,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7060[A-Z]*X(?!\d).*$", families=(PlatformFamily.SERIES_7060_X,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7060[A-Z]*X2.*$", families=(PlatformFamily.SERIES_7060_X2,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7060[A-Z]*X4.*$", families=(PlatformFamily.SERIES_7060_X4,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7060[A-Z]*X5.*$", families=(PlatformFamily.SERIES_7060_X5,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7060[A-Z]*X6.*$", families=(PlatformFamily.SERIES_7060_X6,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7130[A-Z0-9]*-.*$", r"^DCS-7132LB-.*$", families=(PlatformFamily.SERIES_7130,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7150[A-Z0-9]*-.*$", families=(PlatformFamily.SERIES_7150,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7160-.*$", families=(PlatformFamily.SERIES_7160,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7170[A-Z0-9]*-.*$", families=(PlatformFamily.SERIES_7170,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7250[A-WY-Z]*X.*$", families=(PlatformFamily.SERIES_7250_X,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7260[A-Z]*X(?!\d).*$", families=(PlatformFamily.SERIES_7260_X,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7260[A-Z]*X3.*$", families=(PlatformFamily.SERIES_7260_X3,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7280SE-.*$", families=(PlatformFamily.SERIES_7280_E,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7280[CQST]R(?!\d).*$", families=(PlatformFamily.SERIES_7280_R,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7280[CS]R2.*$", families=(PlatformFamily.SERIES_7280_R2,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7280[CDPST]R3.*$", families=(PlatformFamily.SERIES_7280_R3,)),
    _system_rule(PlatformType.FIXED, r"^DCS-7280R4.*$", families=(PlatformFamily.SERIES_7280_R4,)),
    _system_rule(PlatformType.CHASSIS, r"^DCS-73(?:04|08|16)(?:-[FR])?$", r"^DCS-73(?:04|08)X3(?:-[FR])?$"),
    _system_rule(PlatformType.CHASSIS, r"^DCS-732[48](?:-[FR])?$", families=(PlatformFamily.SERIES_7320_X,)),
    _system_rule(PlatformType.CHASSIS, r"^(?:DCS-)?(?:7358|7368)(?:-CH)?(?:-[FR])?$"),
    _system_rule(PlatformType.CHASSIS, r"^(?:DCS-)?7388(?:-CH)?(?:-[FR])?$"),
    _system_rule(PlatformType.CHASSIS, r"^(?:DCS-)?7289(?:-CH)?(?:-[FR])?$"),
    _system_rule(PlatformType.CHASSIS, r"^DCS-75(?:04|08|12|16)(?:N|-CH)?(?:-[FR])?$"),
    _system_rule(PlatformType.CHASSIS, r"^DCS-78(?:04|08|12|16[BL]?)-CH(?:-[FR])?$"),
    _system_rule(PlatformType.FIXED, r"^DCS-DL-7700R4[A-Z0-9]*(?:-.*)?$", families=(PlatformFamily.SERIES_7700_R4,)),
    _system_rule(PlatformType.FIXED, r"^DCS-DS-7720R4-128PE(?:-[NF])?$", families=(PlatformFamily.SERIES_7720_R4,)),
    _system_rule(PlatformType.APPLIANCE, r"^AWE-5[0-9]{3}(?:-.*)?$", families=(PlatformFamily.AWE_5000,)),
    _system_rule(PlatformType.APPLIANCE, r"^AWE-72[0-9]{2}R[A-Z0-9]*(?:-.*)?$", families=(PlatformFamily.AWE_7200_R,)),
    _system_rule(PlatformType.VIRTUAL, r"^CLOUDEOS$", families=(PlatformFamily.CLOUDEOS,)),
    _system_rule(PlatformType.VIRTUAL, r"^(?:CEOS-LAB|CEOSLAB)(?:-.+)?$", families=(PlatformFamily.CEOS_LAB,)),
    _system_rule(PlatformType.VIRTUAL, r"^(?:VEOS-LAB|VEOSLAB)(?:-.+)?$", families=(PlatformFamily.VEOS_LAB,)),
    _system_rule(PlatformType.APPLIANCE, r"^CLOUDVISION EXCHANGE$", families=(PlatformFamily.CLOUDVISION_EXCHANGE,)),
)


MODULE_PLATFORM_FAMILY_RULES: dict[PlatformFamily, tuple[_ModuleFamilyRule, ...]] = {
    PlatformFamily.SERIES_7289_R3A: (_module_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7289R3A[A-Z]*-SC$"),),
    PlatformFamily.SERIES_7300_X: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7300X(?!\d)-.*-LC$"),),
    PlatformFamily.SERIES_7300_X3: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7300X3-.*-LC$"),),
    PlatformFamily.SERIES_7358_X4: (_module_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7358X4-SC$"),),
    PlatformFamily.SERIES_7368_X4: (_module_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7368X4-SC$"),),
    PlatformFamily.SERIES_7388_X5: (_module_rule(PlatformComponentRole.SWITCH_CARD, r"^(?:DCS-)?7388X5-SC$"),),
    PlatformFamily.SERIES_7500_E: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500E-.*-LC$"),),
    PlatformFamily.SERIES_7500_R: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R(?!\d)-.*-LC$"),),
    PlatformFamily.SERIES_7500_R2: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R2[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7500_R3: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7500R3[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7800_R3: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7800R3[A-Z]*-.*-LC$"),),
    PlatformFamily.SERIES_7800_R4: (_module_rule(PlatformComponentRole.LINE_CARD, r"^(?:DCS-)?7800R4[A-Z]*-.*-LC$"),),
}

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


def resolve_platform_families(model: str, role: PlatformComponentRole | None = None) -> frozenset[PlatformFamily]:
    """Resolve semantic platform families from a system or module model.

    Resolution may return more than one family when classifications overlap. The
    results are attached to the component and later aggregated by
    `PlatformIdentity`.

    Parameters
    ----------
    model : str
        Component model to resolve.
    role : PlatformComponentRole | None
        Installed module role, or `None` when `model` identifies the system.

    Returns
    -------
    frozenset[PlatformFamily]
        All platform families matched by the model and role.
    """
    normalized_model = normalize_platform_model(model)
    if normalized_model is None:
        return frozenset()
    if role is None:
        return frozenset(
            family for rule in SYSTEM_PLATFORM_RULES if any(pattern.fullmatch(normalized_model) for pattern in rule.patterns) for family in rule.families
        )
    return frozenset(
        family
        for family, rules in MODULE_PLATFORM_FAMILY_RULES.items()
        for rule in rules
        if rule.role is role and any(pattern.fullmatch(normalized_model) for pattern in rule.patterns)
    )


def _resolve_platform_type(model: str) -> ParseResult[PlatformType]:
    """Resolve platform deployment type from an exact normalized system model.

    Parameters
    ----------
    model : str
        Normalized system model to evaluate.

    Returns
    -------
    ParseResult[PlatformType]
        Resolved physical type, including `UNKNOWN` when no rule matches, or a
        contradictory result if rules resolve more than one type.
    """
    matched_types = {rule.type for rule in SYSTEM_PLATFORM_RULES if any(pattern.fullmatch(model) for pattern in rule.patterns)}
    if len(matched_types) > 1:
        return ParseFail(ParseFailureReason.CONTRADICTORY, f"system model '{model}' matches conflicting platform types")
    return ParseSuccessful(next(iter(matched_types), PlatformType.UNKNOWN))


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
    platform_type: PlatformType,
    *,
    modules: tuple[PlatformComponentIdentity, ...] = (),
) -> PlatformIdentity:
    """Build a platform identity and aggregate component families.

    Parameters
    ----------
    model : str
        Model reported by `show version`, with surrounding whitespace removed.
    platform_type : PlatformType
        Deployment type resolved from the exact system model.
    modules : tuple[PlatformComponentIdentity, ...]
        Discovered module identities in deterministic slot order.

    Returns
    -------
    PlatformIdentity
        The structured platform identity.
    """
    base_families = resolve_platform_families(model)
    return PlatformIdentity(
        model=model,
        type=platform_type,
        modules=modules,
        platform_families=frozenset((*base_families, *(family for component in modules for family in component.platform_families))),
    )


def parse_eos_platform(model_name: str | None) -> ParseResult[PlatformIdentity]:
    """Parse an EOS model name into an initial system identity.

    Parameters
    ----------
    model_name : str | None
        System model reported by EOS.

    Returns
    -------
    ParseResult[PlatformIdentity]
        The initial platform identity or a typed parsing failure.
    """
    if model_name is None:
        return ParseFail(ParseFailureReason.MISSING, "show version does not contain modelName")
    if not isinstance(model_name, str):
        return ParseFail(ParseFailureReason.MALFORMED, "show version modelName is not a string")
    normalized_model = normalize_platform_model(model_name)
    if normalized_model is None:
        return ParseFail(ParseFailureReason.INVALID, "show version modelName is empty")

    platform_type_result = _resolve_platform_type(normalized_model)
    if isinstance(platform_type_result, ParseFail):
        return platform_type_result
    return ParseSuccessful(_platform_identity(model_name.strip(), platform_type_result.value))


def parse_eos_platform_or_none(model_name: str | None) -> PlatformIdentity | None:
    """Return a platform identity without exposing parsing failures to metadata consumers.

    Parameters
    ----------
    model_name : str | None
        System model reported by EOS.

    Returns
    -------
    PlatformIdentity | None
        Parsed identity, or `None` when the system model cannot be parsed.
    """
    result = parse_eos_platform(model_name)
    return result.value if isinstance(result, ParseSuccessful) else None


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


def _parse_modules_mapping(show_module_output: Mapping[str, object] | None) -> ParseResult[Mapping[object, object]]:
    """Validate and return the modules mapping from structured EOS output.

    Parameters
    ----------
    show_module_output : Mapping[str, object] | None
        Structured `show module` output, if available.

    Returns
    -------
    ParseResult[Mapping[object, object]]
        Valid non-empty module inventory or a typed parsing failure.
    """
    if show_module_output is None:
        return ParseFail(ParseFailureReason.MISSING, "show module output is missing")
    if not isinstance(show_module_output, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "show module output is not a mapping")
    if "modules" not in show_module_output:
        return ParseFail(ParseFailureReason.MISSING, "show module output does not contain modules")

    modules = show_module_output.get("modules")
    if not isinstance(modules, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "show module modules value is not a mapping")
    if not modules:
        return ParseFail(ParseFailureReason.INVALID, "show module modules mapping is empty")
    return ParseSuccessful(modules)


def parse_eos_platform_modules(
    platform: PlatformIdentity,
    show_module_output: Mapping[str, object] | None,
) -> ParseResult[PlatformIdentity]:
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
    ParseResult[PlatformIdentity]
        The enriched identity or a typed parsing failure.
    """
    if platform.type is not PlatformType.CHASSIS:
        return ParseFail(ParseFailureReason.INVALID, "module inventory can only enrich a chassis platform")
    modules_result = _parse_modules_mapping(show_module_output)
    if isinstance(modules_result, ParseFail):
        return modules_result

    components: list[PlatformComponentIdentity] = []
    for raw_slot, module_data in sorted(modules_result.value.items(), key=lambda item: str(item[0])):
        slot = raw_slot if isinstance(raw_slot, str) else str(raw_slot)
        normalized_data = module_data if isinstance(module_data, Mapping) else {}
        component = _parse_eos_module(slot, normalized_data)
        if component is not None:
            components.append(component)

    return ParseSuccessful(_platform_identity(platform.model, platform.type, modules=tuple(components)))


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
    family_match = (
        bool(platform.platform_families & requested_families)
        if role is None
        else any(component.platform_families & requested_families for component in _components_for_role(platform, role))
    )
    if family_match:
        return True
    if platform.type is PlatformType.UNKNOWN:
        return None
    if platform.type is PlatformType.CHASSIS and (not platform.modules or any(component.role is PlatformComponentRole.UNKNOWN for component in platform.modules)):
        return None
    return False
