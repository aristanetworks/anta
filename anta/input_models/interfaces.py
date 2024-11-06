# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for interface tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from anta.custom_types import Interface


class InterfaceState(BaseModel):
    """Model for an interface state."""

    name: Interface
    """Interface to validate."""
    status: Literal["up", "down", "adminDown"]
    """Expected status of the interface."""
    line_protocol_status: Literal["up", "down", "testing", "unknown", "dormant", "notPresent", "lowerLayerDown"] | None = None
    """Expected line protocol status of the interface."""
