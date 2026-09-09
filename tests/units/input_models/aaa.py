# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.bfd.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.aaa import VerifyAuthorizationMethodLists

if TYPE_CHECKING:
    from anta.input_models.aaa import AAAAuthorization


class TestVerifyAuthorizationMethodListsInput:
    """Test the inputs for VerifyAuthorizationMethodLists."""

    @pytest.mark.parametrize(
        "authorization",
        [
            pytest.param([{"authz_type": "commands", "method_lists": [{"name": 0, "methods": ["local"]}]}], id="commands-integer"),
            pytest.param([{"authz_type": "commands", "method_lists": [{"name": "all", "methods": ["tacacs+", "local"]}]}], id="commands-all"),
            pytest.param([{"authz_type": "commands", "method_lists": [{"name": "privilege5-10", "methods": ["local"]}]}], id="commands-range"),
            pytest.param([{"authz_type": "exec", "method_lists": [{"name": "exec", "methods": ["local"]}]}], id="exec"),
        ],
    )
    def test_valid(self, authorization: list[AAAAuthorization]) -> None:
        """Verify valid authorization inputs."""
        VerifyAuthorizationMethodLists.Input(authorization=authorization)

    @pytest.mark.parametrize(
        "authorization",
        [
            pytest.param([], id="empty-authorization"),
            pytest.param([{"authz_type": "commands", "method_lists": []}], id="empty-method-lists"),
            pytest.param([{"authz_type": "invalid", "method_lists": [{"name": "all", "methods": ["local"]}]}], id="invalid-authorization-type"),
            pytest.param([{"authz_type": "exec", "method_lists": [{"name": "default", "methods": ["local"]}]}], id="invalid-exec-name"),
            pytest.param([{"authz_type": "commands", "method_lists": [{"name": 16, "methods": ["local"]}]}], id="privilege-out-of-range"),
            pytest.param([{"authz_type": "commands", "method_lists": [{"name": "privilege10-5", "methods": ["local"]}]}], id="reversed-range"),
            pytest.param(
                [
                    {
                        "authz_type": "commands",
                        "method_lists": [
                            {"name": "all", "methods": ["local"]},
                            {"name": "privilege0-15", "methods": ["local"]},
                        ],
                    }
                ],
                id="duplicate-normalized-name",
            ),
        ],
    )
    def test_invalid(self, authorization: list[AAAAuthorization]) -> None:
        """Verify invalid authorization inputs."""
        with pytest.raises(ValidationError):
            VerifyAuthorizationMethodLists.Input(authorization=authorization)
