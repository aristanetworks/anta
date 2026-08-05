# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.configuration."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.input_models.configuration import ConfigEntry, ConfigRule


class TestConfigEntry:
    """Tests for anta.input_models.configuration.ConfigEntry."""

    @pytest.mark.parametrize(
        "model_params",
        [
            # threshold is valid when mode=regex and match contains a capture group
            pytest.param(
                {
                    "match": "mtu (\\d+)",
                    "mode": "regex",
                    "threshold": {"value": 1500, "operator": "ge"},
                },
                id="threshold-with-regex-mode",
            ),
            # mode defaults to exact; no threshold — always valid
            pytest.param(
                {"match": "no shutdown", "mode": "exact"},
                id="no-threshold-exact",
            ),
            # contains mode without threshold — always valid
            pytest.param(
                {"match": "router-id", "mode": "contains"},
                id="no-threshold-contains",
            ),
            # regex mode without threshold — valid even without a capture group
            pytest.param(
                {"match": "logging host \\S+", "mode": "regex"},
                id="no-threshold-regex",
            ),
        ],
    )
    def test_valid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigEntry valid inputs."""
        ConfigEntry.model_validate(model_params)

    @pytest.mark.parametrize(
        "model_params",
        [
            # threshold requires mode=regex; exact is rejected
            pytest.param(
                {"match": "mtu", "mode": "exact", "threshold": {"value": 1500, "operator": "ge"}},
                id="threshold-with-exact-mode",
            ),
            # threshold requires mode=regex; contains is rejected
            pytest.param(
                {
                    "match": "mtu",
                    "mode": "contains",
                    "threshold": {"value": 1500, "operator": "ge"},
                },
                id="threshold-with-contains-mode",
            ),
            # threshold requires a capture group in the pattern; bare \\d+ has none
            pytest.param(
                {
                    "match": "mtu \\d+",
                    "mode": "regex",
                    "threshold": {"value": 1500, "operator": "ge"},
                },
                id="threshold-regex-no-capture-group",
            ),
            # threshold requires absent=False; combining threshold with absent=True is rejected
            pytest.param(
                {
                    "match": "mtu (\\d+)",
                    "mode": "regex",
                    "absent": True,
                    "threshold": {"value": 1500, "operator": "ge"},
                },
                id="threshold-with-absent-true",
            ),
            # mode=regex with invalid regex syntax is rejected at model validation time, not at runtime
            pytest.param(
                {"match": "mtu [invalid", "mode": "regex"},
                id="invalid-regex-syntax",
            ),
        ],
    )
    def test_invalid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigEntry invalid inputs."""
        with pytest.raises(ValidationError):
            ConfigEntry.model_validate(model_params)


class TestConfigRule:
    """Tests for anta.input_models.configuration.ConfigRule."""

    @pytest.mark.parametrize(
        "model_params",
        [
            # section=None means top-level commands — valid default
            pytest.param(
                {"section": None, "entries": [{"match": "ip routing"}]},
                id="no-section",
            ),
            # single exact section path — valid
            pytest.param(
                {"section": ["router bgp 65101"], "entries": [{"match": "router-id"}]},
                id="exact-section",
            ),
            # single regex section pattern — valid; regex fallback is applied at runtime
            pytest.param(
                {"section": ["interface Ethernet\\d+"], "entries": [{"match": "description"}]},
                id="regex-section",
            ),
            # entries=[] is valid — section existence check: passes if section resolves, fails if not found
            pytest.param(
                {"section": ["router bgp 65101"], "entries": []},
                id="section-existence-only",
            ),
        ],
    )
    def test_valid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigRule valid inputs."""
        ConfigRule.model_validate(model_params)

    @pytest.mark.parametrize(
        "model_params",
        [
            # section must have at least one pattern — empty list is rejected
            pytest.param(
                {"section": [], "entries": [{"match": "ip routing"}]},
                id="empty-section-list",
            ),
            # each section pattern must be non-empty — empty string is rejected
            pytest.param(
                {"section": [""], "entries": [{"match": "ip routing"}]},
                id="empty-string-in-section",
            ),
            # section patterns used as regex fallback — invalid syntax is rejected at model validation time
            pytest.param(
                {"section": ["interface Ethernet[invalid"], "entries": [{"match": "ip routing"}]},
                id="invalid-section-regex-syntax",
            ),
        ],
    )
    def test_invalid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigRule invalid inputs."""
        with pytest.raises(ValidationError):
            ConfigRule.model_validate(model_params)
