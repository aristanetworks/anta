# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.connectivity.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.connectivity import VerifyReachability

if TYPE_CHECKING:
    from anta.input_models.connectivity import Host


class TestVerifyReachabilityInput:
    """Test anta.tests.connectivity.VerifyReachability.Input."""

    @pytest.mark.parametrize(
        ("hosts"),
        [
            pytest.param([{"destination": "fd12:3456:789a:1::2", "source": "fd12:3456:789a:1::1"}], id="valid"),
        ],
    )
    def test_valid(self, hosts: list[Host]) -> None:
        """Test VerifyReachability.Input valid inputs."""
        VerifyReachability.Input(hosts=hosts)

    @pytest.mark.parametrize(
        ("hosts"),
        [
            pytest.param([{"destination": "fd12:3456:789a:1::2", "source": "192.168.0.10"}], id="invalid-source"),
            pytest.param([{"destination": "192.168.0.10", "source": "fd12:3456:789a:1::2"}], id="invalid-destination"),
        ],
    )
    def test_invalid(self, hosts: list[Host]) -> None:
        """Test VerifyReachability.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyReachability.Input(hosts=hosts)
