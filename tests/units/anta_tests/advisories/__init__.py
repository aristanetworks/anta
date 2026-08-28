# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit-test helpers for anta.tests.advisories modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anta.device import AntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


class OfflineAntaDevice(AntaDevice):
    """Minimal ANTA device for tests that simulate collection outcomes."""

    @property
    def _keys(self) -> tuple[Any, ...]:
        """Return the immutable key tuple used by ANTA."""
        return (self.name,)

    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Reject unexpected command collection."""
        msg = f"Unit-test device cannot collect '{command.command}'."
        raise RuntimeError(msg)

    async def refresh(self) -> None:
        """Mark the unit-test device as available."""
        self.is_online = True
        self.established = True
