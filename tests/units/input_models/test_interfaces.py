# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.interfaces.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta.input_models.interfaces import InterfaceState

if TYPE_CHECKING:
    from anta.custom_types import Interface, PortChannelInterface


class TestInterfaceState:
    """Test anta.input_models.interfaces.InterfaceState."""

    # pylint: disable=too-few-public-methods

    @pytest.mark.parametrize(
        ("name", "portchannel", "expected"),
        [
            pytest.param("Ethernet1", "Port-Channel42", "Interface: Ethernet1 Port-Channel: Port-Channel42", id="with port-channel"),
            pytest.param("Ethernet1", None, "Interface: Ethernet1", id="no port-channel"),
        ],
    )
    def test_valid__str__(self, name: Interface, portchannel: PortChannelInterface | None, expected: str) -> None:
        """Test InterfaceState __str__."""
        assert str(InterfaceState(name=name, portchannel=portchannel)) == expected
