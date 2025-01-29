# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for ISIS tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ISISInstances(BaseModel):
    """Model for a list of ISIS instance entries."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """The instance name to validated the instance specific isis details."""
    vrf: str = "default"
    """VRF context. Defaults to `default` VRF."""
    graceful_restart: bool = True
    """Specifies the Graceful Restart,
    Options:
    - True: Default mode, refer as graceful restart is enabled.
    - False: Refer as graceful restart is disabled."""
    graceful_helper: bool = True
    """Specifies the Graceful Restart Helper,
    Options:
    - True: Default mode, refer as graceful restart helper is enabled.
    - False: Refer as graceful restart helper is disabled."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInstances for reporting."""
        return f"Instance: {self.name} VRF: {self.vrf}"
