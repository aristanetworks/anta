# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tools.get_value
"""

from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

from anta.tools.get_value import get_value

INPUT_DICT = {"test_value": 42, "nested_test": {"nested_value": 43}}


@pytest.mark.parametrize(
    "input_dict, key, default, required, org_key, separator, expected_result, expected_raise",
    [
        pytest.param({}, "test", None, False, None, None, None, does_not_raise(), id="empty dict"),
        pytest.param(INPUT_DICT, "test_value", None, False, None, None, 42, does_not_raise(), id="simple key"),
        pytest.param(INPUT_DICT, "nested_test.nested_value", None, False, None, None, 43, does_not_raise(), id="nested_key"),
        pytest.param(INPUT_DICT, "missing_value", None, False, None, None, None, does_not_raise(), id="missing_value"),
        pytest.param(INPUT_DICT, "missing_value_with_default", "default_value", False, None, None, "default_value", does_not_raise(), id="default"),
        pytest.param(INPUT_DICT, "missing_required", None, True, None, None, None, pytest.raises(ValueError), id="required"),
        pytest.param(INPUT_DICT, "missing_required", None, True, "custom_org_key", None, None, pytest.raises(ValueError), id="custom org_key"),
        pytest.param(INPUT_DICT, "nested_test||nested_value", None, None, None, "||", 43, does_not_raise(), id="custom separator"),
    ],
)
def test_get_value(
    input_dict: dict[Any, Any],
    key: str,
    default: str | None,
    required: bool,
    org_key: str | None,
    separator: str | None,
    expected_result: str,
    expected_raise: Any,
) -> None:
    """
    Test get_value
    """
    # pylint: disable=too-many-arguments
    kwargs = {"default": default, "required": required, "org_key": org_key, "separator": separator}
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    with expected_raise:
        assert get_value(input_dict, key, **kwargs) == expected_result  # type: ignore
