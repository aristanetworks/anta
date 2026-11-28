# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for VXLAN test input models."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.tests.vxlan import VerifyVxlanFloodVtep


@pytest.mark.parametrize(
    ("vlans", "expected"),
    [
        pytest.param({10: []}, [10], id="single-integer"),
        pytest.param({"10": []}, [10], id="single-string"),
        pytest.param({"10,20,100,200,710-711": []}, [10, 20, 100, 200, 710, 711], id="mixed-selection"),
        pytest.param({" 10, 20 - 22 ": []}, [10, 20, 21, 22], id="whitespace"),
        pytest.param({"0,4093-4094": []}, [0, 4093, 4094], id="limits"),
        pytest.param({"10-10": []}, [10], id="single-vlan-range"),
    ],
)
def test_flood_vtep_valid_inputs(vlans: dict[str | int, Any], expected: list[int]) -> None:
    """Verify input selection is normalized to individual VLAN IDs."""
    inputs = VerifyVxlanFloodVtep.Input.model_validate({"vlans": vlans})
    assert list(inputs.vlans) == expected


@pytest.mark.parametrize(
    "vlans",
    [
        pytest.param({}, id="empty-mapping"),
        pytest.param({"": []}, id="empty-selection"),
        pytest.param({"10,": []}, id="trailing-comma"),
        pytest.param({"10,,20": []}, id="empty-token"),
        pytest.param({"abc": []}, id="non-numeric"),
        pytest.param({"10-": []}, id="incomplete-range"),
        pytest.param({"20-10": []}, id="descending-range"),
        pytest.param({"-1": []}, id="negative"),
        pytest.param({"4095": []}, id="above-maximum"),
        pytest.param({"4094-999999999": []}, id="range-above-maximum"),
        pytest.param({"10,10": []}, id="duplicate"),
        pytest.param({10: [], "9-11": []}, id="overlap"),
        pytest.param({"10-12": ["not-an-ip"]}, id="invalid-vtep"),
        pytest.param({"10-12": ["2001:db8::1"]}, id="ipv6-vtep"),
    ],
)
def test_flood_vtep_invalid_inputs(vlans: dict[str | int, Any]) -> None:
    """Reject invalid or ambiguous VLAN selections and non-IPv4 VTEPs."""
    with pytest.raises(ValidationError):
        VerifyVxlanFloodVtep.Input.model_validate({"vlans": vlans})
