# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from refreshed platform metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind
from anta._eos.platform import PlatformComponentIdentity, PlatformComponentRole, PlatformIdentity

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand


class PlatformIdentityFact(FactDefinition[PlatformIdentity]):
    """Normalized platform identity from refreshed device metadata."""

    key = "platform.identity"
    label = "platform identity"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[PlatformIdentity]:
        """Return the refreshed platform identity or a missing fact when unavailable."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        platform = device.platform
        if platform is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(platform, PlatformIdentity):
            return cls.unavailable(FactProblemKind.INVALID, source)
        return cls.available(platform, source)


class SwitchCardIdentityFact(FactDefinition[PlatformComponentIdentity]):
    """Switch-card identity from refreshed platform metadata."""

    key = "platform.component.switch_card"
    label = "switch-card platform identity"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[PlatformComponentIdentity]:
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
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=distinct)
        return cls.available(next(iter(distinct)), source)
