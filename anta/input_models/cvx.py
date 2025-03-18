# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for CVX tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from anta.custom_types import Hostname


class CVXPeers(BaseModel):
    """Model for a CVX Cluster Peer."""

    peer_name: Hostname
    """The CVX Peer used communicate with a CVX server."""
    registration_state: Literal["Connecting", "Connected", "Registration error", "Registration complete", "Unexpected peer state"] = "Registration complete"
    """The CVX registration state."""
