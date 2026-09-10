# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.aaa."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.aaa import AAAAccounting

if TYPE_CHECKING:
    from anta.custom_types import AAAAccountingType
    from anta.input_models.aaa import AAAAccountingMethods


class TestAAAAccounting:
    """Tests for the AAAAccounting model."""

    @pytest.mark.parametrize(
        ("acct_type", "method_configs"),
        [
            # commands type: privilege method-list names and console plane
            pytest.param("commands", [{"name": "all", "default_methods": ["tacacs+"]}], id="commands-name-all"),
            pytest.param("commands", [{"name": 5, "default_methods": ["tacacs+"]}], id="commands-name-int"),
            pytest.param("commands", [{"name": "privilege0-15", "default_methods": ["tacacs+"]}], id="commands-name-privilege-string"),
            pytest.param(
                "commands",
                [{"name": "privilege0-5", "default_methods": ["tacacs+"]}, {"name": "privilege6-15", "default_methods": ["logging"]}],
                id="commands-multiple-unique-privilege-ranges",
            ),
            pytest.param(
                "commands",
                [{"name": "all", "default_methods": ["tacacs+"], "console_methods": ["tacacs+"]}],
                id="commands-console-methods-allowed",
            ),
            # exec type: name must equal "exec", both planes allowed
            pytest.param("exec", [{"name": "exec", "default_methods": ["tacacs+"]}], id="exec-default-methods"),
            pytest.param("exec", [{"name": "exec", "console_methods": ["tacacs+"]}], id="exec-console-methods"),
            pytest.param("exec", [{"name": "exec", "default_methods": ["tacacs+"], "console_methods": ["logging"]}], id="exec-both-planes"),
            # system type: name must equal "system", console plane not supported
            pytest.param("system", [{"name": "system", "default_methods": ["tacacs+"]}], id="system-default-only"),
            # dot1x type: name must equal "dot1x", console plane not supported
            pytest.param("dot1x", [{"name": "dot1x", "default_methods": ["radius"]}], id="dot1x-default-only"),
        ],
    )
    def test_valid(self, acct_type: AAAAccountingType, method_configs: list[AAAAccountingMethods]) -> None:
        """Test AAAAccounting valid inputs."""
        AAAAccounting(acct_type=acct_type, method_configs=method_configs)

    @pytest.mark.parametrize(
        ("acct_type", "method_configs", "expected_normalized_name"),
        [
            pytest.param("commands", [{"name": "all", "default_methods": ["tacacs+"]}], "privilege0-15", id="all-expands-to-full-range"),
            pytest.param("commands", [{"name": 0, "default_methods": ["tacacs+"]}], "privilege0", id="int-zero-to-privilege0"),
            pytest.param("commands", [{"name": 15, "default_methods": ["tacacs+"]}], "privilege15", id="int-max-level"),
            pytest.param("commands", [{"name": "privilege5-10", "default_methods": ["tacacs+"]}], "privilege5-10", id="partial-range-unchanged"),
        ],
    )
    def test_valid_name_normalization(self, acct_type: AAAAccountingType, method_configs: list[AAAAccountingMethods], expected_normalized_name: str) -> None:
        """Test that commands method-list names are normalized to their canonical EOS form."""
        acct = AAAAccounting(acct_type=acct_type, method_configs=method_configs)
        assert acct.method_configs[0].name == expected_normalized_name

    @pytest.mark.parametrize(
        ("acct_type", "method_configs"),
        [
            # commands type: invalid names and duplicate detection
            pytest.param("commands", [{"name": 16, "default_methods": ["tacacs+"]}], id="commands-int-out-of-range"),
            pytest.param("commands", [{"name": -1, "default_methods": ["tacacs+"]}], id="commands-int-negative"),
            pytest.param("commands", [{"name": "privilege5-3", "default_methods": ["tacacs+"]}], id="commands-range-start-exceeds-end"),
            pytest.param("commands", [{"name": "privilege16", "default_methods": ["tacacs+"]}], id="commands-privilege-level-out-of-range"),
            pytest.param("commands", [{"name": "not-a-privilege", "default_methods": ["tacacs+"]}], id="commands-invalid-name-format"),
            pytest.param(
                "commands",
                [{"name": "all", "default_methods": ["tacacs+"]}, {"name": "privilege0-15", "default_methods": ["logging"]}],
                id="commands-duplicate-names-after-normalization",
            ),
            pytest.param(
                "commands",
                [{"name": 0, "default_methods": ["tacacs+"]}, {"name": "privilege0", "default_methods": ["logging"]}],
                id="commands-int-and-string-collide-after-normalization",
            ),
            pytest.param("commands", [], id="commands-empty-method-lists"),
            # exec type: wrong name and duplicates
            pytest.param("exec", [{"name": "system", "default_methods": ["tacacs+"]}], id="exec-wrong-name"),
            pytest.param(
                "exec",
                [{"name": "exec", "default_methods": ["tacacs+"]}, {"name": "exec", "console_methods": ["logging"]}],
                id="exec-duplicate-names",
            ),
            # system type: console not supported and wrong name
            pytest.param("system", [{"name": "system", "console_methods": ["tacacs+"]}], id="system-console-methods-not-supported"),
            pytest.param("system", [{"name": "exec", "default_methods": ["tacacs+"]}], id="system-wrong-name"),
            # dot1x type: console not supported and wrong name
            pytest.param("dot1x", [{"name": "dot1x", "console_methods": ["radius"]}], id="dot1x-console-methods-not-supported"),
            pytest.param("dot1x", [{"name": "system", "default_methods": ["radius"]}], id="dot1x-wrong-name"),
            # AAAAccountingMethods: neither default nor console methods provided
            pytest.param("exec", [{"name": "exec"}], id="method-config-no-methods-provided"),
        ],
    )
    def test_invalid(self, acct_type: AAAAccountingType, method_configs: list[AAAAccountingMethods]) -> None:
        """Test AAAAccounting invalid inputs raise ValidationError."""
        with pytest.raises(ValidationError):
            AAAAccounting(acct_type=acct_type, method_configs=method_configs)
