# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.interfaces.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.services import VerifyErrdisableRecovery

if TYPE_CHECKING:
    from anta.input_models.services import ErrdisableRecovery


class TestVerifyBgpRouteMapsInput:
    """Test anta.tests.services.VerifyErrdisableRecovery.Input."""

    @pytest.mark.parametrize(
        ("reasons"),
        [
            pytest.param([{"reason": "acl", "timer_interval": 30}], id="valid"),
        ],
    )
    def test_valid(self, reasons: list[ErrdisableRecovery]) -> None:
        """Test VerifyErrdisableRecovery.Input valid inputs."""
        VerifyErrdisableRecovery.Input(reasons=reasons)

    @pytest.mark.parametrize(
        ("reasons"),
        [
            pytest.param([{"reason": "acl", "timer_interval": None}], id="invalid"),
        ],
    )
    def test_invalid(self, reasons: list[ErrdisableRecovery]) -> None:
        """Test VerifyErrdisableRecovery.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyErrdisableRecovery.Input(reasons=reasons)
