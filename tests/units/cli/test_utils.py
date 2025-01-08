# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.utils."""

import pytest
from click import BadParameter

from anta.cli.utils import FloatOrNoneParamType


def test_float_or_none_param_type() -> None:
    """Test FloatOrNoneParamType click parameter type."""
    param_type = FloatOrNoneParamType()

    # Test valid float strings
    assert param_type.convert("1.23", None, None) == 1.23
    assert param_type.convert("-4.56", None, None) == -4.56

    # Test None values
    assert param_type.convert(None, None, None) is None
    assert param_type.convert("none", None, None) is None
    assert param_type.convert("NONE", None, None) is None

    # Test float inputs
    assert param_type.convert(1.23, None, None) == 1.23

    # Test invalid inputs
    with pytest.raises(BadParameter):
        param_type.convert("invalid", None, None)

    with pytest.raises(BadParameter):
        param_type.convert("1.2.3", None, None)
