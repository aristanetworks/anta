# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.aaa."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from anta.input_models.aaa import AAAAuthentication


@pytest.mark.parametrize(
    ("model", "data"),
    [
        pytest.param(
            AAAAuthentication,
            {
                "auth_type": "login",
                "method_lists": [
                    {"name": "default", "methods": ["tacacs+", "local"]},
                    {"name": "console", "methods": ["local"]},
                    {"name": "command-api", "methods": ["local"]},
                ],
            },
            id="authentication-login",
        ),
        pytest.param(
            AAAAuthentication,
            {"auth_type": "enable", "method_lists": [{"name": "default", "methods": ["local"]}, {"name": "console", "methods": ["local"]}]},
            id="authentication-enable",
        ),
        pytest.param(
            AAAAuthentication,
            {"auth_type": "dot1x", "method_lists": [{"name": "default", "methods": ["radius"]}]},
            id="authentication-dot1x",
        ),
    ],
)
def test_valid_models(model: type[AAAAuthentication], data: dict[str, object]) -> None:
    """Valid AAA method-list combinations are accepted."""
    model.model_validate(data)


@pytest.mark.parametrize(
    ("model", "data"),
    [
        pytest.param(
            AAAAuthentication,
            {"auth_type": "dot1x", "method_lists": [{"name": "console", "methods": ["radius"]}]},
            id="authentication-invalid-name",
        ),
        pytest.param(
            AAAAuthentication,
            {"auth_type": "login", "method_lists": [{"name": "default", "methods": ["local"]}, {"name": "default", "methods": ["local"]}]},
            id="authentication-duplicate-name",
        ),
    ],
)
def test_invalid_models(model: type[AAAAuthentication], data: dict[str, object]) -> None:
    """Invalid AAA method-list combinations are rejected."""
    with pytest.raises(ValidationError):
        model.model_validate(data)
