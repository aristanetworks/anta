# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.configuration.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.configuration import VerifyRunningConfigLines

if TYPE_CHECKING:
    from anta.custom_types import RegexString
    from anta.input_models.configuration import RunningConfigSection


class TestVerifyRunningConfigLinesInput:
    """Test anta.tests.configuration.VerifyRunningConfigLines.Input."""

    @pytest.mark.parametrize(
        ("sections", "regex_patterns"),
        [
            pytest.param(
                [
                    {"regex": "interface Ethernet1", "regex_patterns": ["switchport mode trunk\n"]},
                    {"regex": "router bgp 65101", "regex_patterns": ["router-id 10.111.255.12", " network 10.110.254.1"]},
                ],
                [],
                id="valid-section",
            ),
            pytest.param([], ["router-id 10.111.254.1\n", "neighbor SPINE*"], id="valid-regex-patterns"),
        ],
    )
    def test_valid(self, sections: list[RunningConfigSection], regex_patterns: list[RegexString]) -> None:
        """Test VerifyRunningConfigLines.Input valid inputs."""
        VerifyRunningConfigLines.Input(sections=sections, regex_patterns=regex_patterns)

    @pytest.mark.parametrize(
        ("sections", "regex_patterns"),
        [
            pytest.param(
                [
                    {"regex": "interface Ethernet1", "regex_patterns": ["switchport mode trunk\n"]},
                    {"regex": "router bgp 65101", "regex_patterns": ["router-id 10.111.255.12", " network 10.110.254.1"]},
                ],
                ["router-id 10.111.254.1\n", "neighbor SPINE*"],
                id="invalid",
            ),
            pytest.param([], [], id="both-input-absent"),
        ],
    )
    def test_invalid(self, sections: list[RunningConfigSection], regex_patterns: list[RegexString]) -> None:
        """Test VerifyRunningConfigLines.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyRunningConfigLines.Input(sections=sections, regex_patterns=regex_patterns)
