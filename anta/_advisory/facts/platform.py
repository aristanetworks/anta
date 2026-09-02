# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from refreshed platform metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind
from anta._eos.platform import PlatformIdentity

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
        if device.platform is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(cast("PlatformIdentity", device.platform), source)
