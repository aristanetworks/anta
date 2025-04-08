# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.system.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.system import VerifyNTPAssociations, VerifyReloadCause

if TYPE_CHECKING:
    from anta.input_models.system import NTPPool, NTPServer


class TestVerifyNTPAssociationsInput:
    """Test anta.tests.system.VerifyNTPAssociations.Input."""

    @pytest.mark.parametrize(
        ("ntp_servers", "ntp_pool"),
        [
            pytest.param([{"server_address": "1.1.1.1", "preferred": True, "stratum": 1}], None, id="valid-ntp-server"),
            pytest.param(None, {"server_addresses": ["1.1.1.1"], "preferred_stratum_range": [1, 3]}, id="valid-ntp-pool"),
        ],
    )
    def test_valid(self, ntp_servers: list[NTPServer], ntp_pool: NTPPool) -> None:
        """Test VerifyNTPAssociations.Input valid inputs."""
        VerifyNTPAssociations.Input(ntp_servers=ntp_servers, ntp_pool=ntp_pool)

    @pytest.mark.parametrize(
        ("ntp_servers", "ntp_pool"),
        [
            pytest.param(
                [{"server_address": "1.1.1.1", "preferred": True, "stratum": 1}],
                {"server_addresses": ["1.1.1.1"], "preferred_stratum_range": [1, 3]},
                id="invalid-both-server-pool",
            ),
            pytest.param(None, {"server_addresses": ["1.1.1.1"], "preferred_stratum_range": [1, 3, 6]}, id="invalid-ntp-pool-stratum"),
            pytest.param(None, None, id="invalid-both-none"),
        ],
    )
    def test_invalid(self, ntp_servers: list[NTPServer], ntp_pool: NTPPool) -> None:
        """Test VerifyNTPAssociations.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyNTPAssociations.Input(ntp_servers=ntp_servers, ntp_pool=ntp_pool)


class TestVerifyReloadCause:
    """Test anta.tests.system.VerifyReloadCause.Input."""

    @pytest.mark.parametrize(
        ("allowed_causes"),
        [pytest.param(["ZTP"], id="valid-allowed-cause"), pytest.param(["FPGA"], id="valid-allowed-cause"), pytest.param(["USER"], id="valid-allowed-cause")],
    )
    def test_valid(self, allowed_causes: list[str]) -> None:
        """Test VerifyReloadCause.Input valid inputs."""
        VerifyReloadCause.Input(allowed_causes=allowed_causes)

    @pytest.mark.parametrize(
        ("allowed_causes"),
        [pytest.param(["ZTP2"], id="invalid-allowed-cause")],
    )
    def test_invalid(self, allowed_causes: list[str]) -> None:
        """Test VerifyReloadCause.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyReloadCause.Input(allowed_causes=allowed_causes)
