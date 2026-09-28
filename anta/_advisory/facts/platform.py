# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from refreshed platform metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind
from anta._eos.platform import PlatformComponentIdentity, PlatformComponentRole, PlatformIdentity

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand


@dataclass(frozen=True, slots=True)
class PlatformIdentityFact(PlatformIdentity, FactDefinition["PlatformIdentityFact"]):
    """Normalized platform identity from refreshed device metadata."""

    key: ClassVar[str] = "platform.identity"
    label: ClassVar[str] = "platform identity"

    @classmethod
    def from_identity(cls, platform: PlatformIdentity) -> PlatformIdentityFact:
        """Create the nominal fact value from normalized platform identity."""
        return cls(
            model=platform.model,
            type=platform.type,
            modules=platform.modules,
            platform_families=platform.platform_families,
        )

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[PlatformIdentityFact]:
        """Return the refreshed platform identity or a missing fact when unavailable."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        platform = device.platform
        if platform is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(platform, PlatformIdentity):
            return cls.unavailable(FactProblemKind.INVALID, source)
        return cls.from_identity(platform).available(source)


@dataclass(frozen=True, slots=True)
class SwitchCardIdentityFact(PlatformComponentIdentity, FactDefinition["SwitchCardIdentityFact"]):
    """Switch-card identity from refreshed platform metadata."""

    key: ClassVar[str] = "platform.component.switch_card"
    label: ClassVar[str] = "switch-card platform identity"

    @classmethod
    def from_identity(cls, card: PlatformComponentIdentity) -> SwitchCardIdentityFact:
        """Create the nominal fact value from normalized switch-card identity."""
        return cls(
            model=card.model,
            role=card.role,
            slot=card.slot,
            platform_families=card.platform_families,
        )

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[SwitchCardIdentityFact]:
        """Return the single switch card discovered during device refresh."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        if not isinstance(device.platform, PlatformIdentity):
            problem = FactProblemKind.MISSING if device.platform is None else FactProblemKind.INVALID
            return cls.unavailable(problem, source)
        switch_cards = tuple(module for module in device.platform.modules if module.role is PlatformComponentRole.SWITCH_CARD)
        if not switch_cards:
            return cls.unavailable(FactProblemKind.MISSING, source)
        distinct = tuple({(card.model, card.platform_families): card for card in switch_cards}.values())
        if len(distinct) > 1:
            observations = tuple(cls.from_identity(card) for card in distinct)
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=observations)
        card = next(iter(distinct))
        return cls.from_identity(card).available(source)
