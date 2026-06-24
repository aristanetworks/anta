# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.configuration."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from anta.input_models.configuration import ConfigRule, RuleEntry


class TestRuleEntry:
    """Tests for anta.input_models.configuration.RuleEntry."""

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
        """Test RuleEntry valid inputs."""
        RuleEntry.model_validate(model_params)

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
        """Test RuleEntry invalid inputs."""
        with pytest.raises(ValidationError):
            RuleEntry.model_validate(model_params)


class TestConfigRule:
    """Tests for anta.input_models.configuration.ConfigRule."""

    @pytest.mark.parametrize(
        "model_params",
        [
            # stanza=None means top-level commands — valid default
            pytest.param(
                {"stanza": None, "entries": [{"match": "ip routing"}]},
                id="no-stanza",
            ),
            # single exact stanza path — valid
            pytest.param(
                {"stanza": ["router bgp 65101"], "entries": [{"match": "router-id"}]},
                id="exact-stanza",
            ),
            # single regex stanza pattern — valid; regex fallback is applied at runtime
            pytest.param(
                {"stanza": ["interface Ethernet\\d+"], "entries": [{"match": "description"}]},
                id="regex-stanza",
            ),
            # entries=[] is valid — stanza existence check: passes if stanza resolves, fails if not found
            pytest.param(
                {"stanza": ["router bgp 65101"], "entries": []},
                id="stanza-existence-only",
            ),
        ],
    )
    def test_valid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigRule valid inputs."""
        ConfigRule.model_validate(model_params)

    @pytest.mark.parametrize(
        "model_params",
        [
            # stanza must have at least one pattern — empty list is rejected
            pytest.param(
                {"stanza": [], "entries": [{"match": "ip routing"}]},
                id="empty-stanza-list",
            ),
            # each stanza pattern must be non-empty — empty string is rejected
            pytest.param(
                {"stanza": [""], "entries": [{"match": "ip routing"}]},
                id="empty-string-in-stanza",
            ),
            # stanza patterns used as regex fallback — invalid syntax is rejected at model validation time
            pytest.param(
                {"stanza": ["interface Ethernet[invalid"], "entries": [{"match": "ip routing"}]},
                id="invalid-stanza-regex-syntax",
            ),
        ],
    )
    def test_invalid(self, model_params: dict[str, Any]) -> None:
        """Test ConfigRule invalid inputs."""
        with pytest.raises(ValidationError):
            ConfigRule.model_validate(model_params)
