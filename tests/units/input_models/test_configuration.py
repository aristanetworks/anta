# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.configuration."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.input_models.configuration import RuleEntry


class TestRuleEntry:
    """Tests for anta.input_models.configuration.RuleEntry."""

    @pytest.mark.parametrize(
        "model_params",
        [
            pytest.param(
                {"match": "mtu (\\d+)", "mode": "regex", "threshold": {"value": 1500, "operator": "ge"}},
                id="threshold-with-regex-mode",
            ),
            pytest.param(
                {"match": "no shutdown", "mode": "exact"},
                id="no-threshold-exact",
            ),
            pytest.param(
                {"match": "router-id", "mode": "contains"},
                id="no-threshold-contains",
            ),
            pytest.param(
                {"match": "logging host \\S+", "mode": "regex"},
                id="no-threshold-regex",
            ),
        ],
    )
    def test_valid(self, model_params: dict[str, Any]) -> None:
        """Test RuleEntry valid inputs."""
        RuleEntry.model_validate(model_params)

    @pytest.mark.parametrize(
        "model_params",
        [
            pytest.param(
                {"match": "mtu", "mode": "exact", "threshold": {"value": 1500, "operator": "ge"}},
                id="threshold-with-exact-mode",
            ),
            pytest.param(
                {"match": "mtu", "mode": "contains", "threshold": {"value": 1500, "operator": "ge"}},
                id="threshold-with-contains-mode",
            ),
        ],
    )
    def test_invalid(self, model_params: dict[str, Any]) -> None:
        """Test RuleEntry invalid inputs."""
        with pytest.raises(ValidationError):
            RuleEntry.model_validate(model_params)
