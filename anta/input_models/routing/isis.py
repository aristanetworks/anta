# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for ISIS tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ISISInstances(BaseModel):
    """Model for a list of ISIS instance entries."""

    model_config = ConfigDict(extra="forbid")
    vrf: str = "default"
    """VRF context. Defaults to `default` VRF."""
    name: str
    """The instance name or ID to validated the instance specific isis details."""
    graceful_restart: bool = True
    """Flag to check if the  graceful restart is enabled for isis instance, Defaults to `True`"""
    graceful_helper: bool = True
    """Flag to check if the  graceful helper is enabled for isis instance, Defaults to `True`"""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInstances for reporting."""
        return f"VRF: {self.vrf} Instance: {self.name}"
