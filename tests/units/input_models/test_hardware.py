# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the hardware test input models."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.tests.hardware import VerifyEnvironmentPower


class TestVerifyEnvironmentPowerInput:
    """Test anta.tests.hardware.VerifyEnvironmentPower.Input."""

    @pytest.mark.parametrize(
        "inputs",
        [
            pytest.param({"states": ["ok"]}, id="omitted-selector"),
            pytest.param({"states": ["ok"], "min_input_voltage": None}, id="omitted-selector-none-threshold"),
            pytest.param({"states": ["ok"], "min_input_voltage": 240}, id="default-a-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "A", "min_input_voltage": 240}, id="A-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "B", "min_input_voltage": 240}, id="B-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "any", "min_input_voltage": 240}, id="any-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "both", "min_input_voltage": 240}, id="both-threshold"),
        ],
    )
    def test_valid(self, inputs: dict[str, Any]) -> None:
        """Accept omitted selectors and explicit selectors with a threshold."""
        VerifyEnvironmentPower.Input.model_validate(inputs)

    @pytest.mark.parametrize(
        "inputs",
        [
            pytest.param({"states": ["ok"], "input_voltage_feeds": "A"}, id="A-omitted-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "A", "min_input_voltage": None}, id="A-none-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "B"}, id="B-omitted-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "B", "min_input_voltage": None}, id="B-none-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "any"}, id="any-omitted-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "any", "min_input_voltage": None}, id="any-none-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "both"}, id="both-omitted-threshold"),
            pytest.param({"states": ["ok"], "input_voltage_feeds": "both", "min_input_voltage": None}, id="both-none-threshold"),
        ],
    )
    def test_invalid(self, inputs: dict[str, Any]) -> None:
        """Reject an explicit selector without a non-None threshold."""
        with pytest.raises(ValidationError, match="'min_input_voltage' must be provided when 'input_voltage_feeds' is provided"):
            VerifyEnvironmentPower.Input.model_validate(inputs)
