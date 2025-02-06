# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.isis.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.routing.isis import VerifyISISSegmentRoutingAdjacencySegments, VerifyISISSegmentRoutingDataplane

if TYPE_CHECKING:
    from anta.input_models.routing.isis import ISISInstance


class TestVerifyISISSegmentRoutingAdjacencySegmentsInput:
    """Test anta.tests.routing.isis.VerifyISISSegmentRoutingAdjacencySegments.Input."""

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "default", "segments": [{"interface": "Ethernet2", "address": "10.0.1.3", "sid_origin": "dynamic"}]}], id="valid_vrf"
            ),
        ],
    )
    def test_valid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingAdjacencySegments.Input valid inputs."""
        VerifyISISSegmentRoutingAdjacencySegments.Input(instances=instances)

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "PROD", "segments": [{"interface": "Ethernet2", "address": "10.0.1.3", "sid_origin": "dynamic"}]}], id="invalid_vrf"
            ),
        ],
    )
    def test_invalid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingAdjacencySegments.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyISISSegmentRoutingAdjacencySegments.Input(instances=instances)


class TestVerifyISISSegmentRoutingDataplaneInput:
    """Test anta.tests.routing.isis.VerifyISISSegmentRoutingDataplane.Input."""

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param([{"name": "CORE-ISIS", "vrf": "default", "dataplane": "MPLS"}], id="valid_vrf"),
        ],
    )
    def test_valid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingDataplane.Input valid inputs."""
        VerifyISISSegmentRoutingDataplane.Input(instances=instances)

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param([{"name": "CORE-ISIS", "vrf": "PROD", "dataplane": "MPLS"}], id="invalid_vrf"),
        ],
    )
    def test_invalid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingDataplane.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyISISSegmentRoutingDataplane.Input(instances=instances)
