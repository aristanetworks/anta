# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Tests for `anta.tools.get_item`."""
from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

from anta.tools.get_item import get_item

DUMMY_DATA = [
    {
        "id": 1,
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
    },
    {
        "id": 2,
        "name": "Bob",
        "age": 35,
        "email": "bob@example.com",
    },
    {
        "id": 3,
        "name": "Charlie",
        "age": 40,
        "email": "charlie@example.com",
    },
]


@pytest.mark.parametrize(
    "list_of_dicts, key, value, default, required, case_sensitive, var_name, custom_error_msg, expected_result, expected_raise",
    [
        pytest.param([], "name", "Bob", None, False, False, None, None, None, does_not_raise(), id="empty list"),
        pytest.param(DUMMY_DATA, "name", "Jack", None, False, False, None, None, None, does_not_raise(), id="missing item"),
        pytest.param(DUMMY_DATA, "name", "Alice", None, False, False, None, None, DUMMY_DATA[0], does_not_raise(), id="found item"),
        pytest.param(DUMMY_DATA, "name", "Jack", "default_value", False, False, None, None, "default_value", does_not_raise(), id="default value"),
        pytest.param(DUMMY_DATA, "name", "Jack", None, True, False, None, None, None, pytest.raises(ValueError, match="name"), id="required"),
        pytest.param(DUMMY_DATA, "name", "bob", None, False, True, None, None, None, does_not_raise(), id="case sensitive"),
        pytest.param(DUMMY_DATA, "name", "charlie", None, False, False, None, None, DUMMY_DATA[2], does_not_raise(), id="case insensitive"),
        pytest.param(
            DUMMY_DATA, "name", "Jack", None, True, False, "custom_var_name", None, None, pytest.raises(ValueError, match="custom_var_name"), id="custom var_name"
        ),
        pytest.param(
            DUMMY_DATA, "name", "Jack", None, True, False, None, "custom_error_msg", None, pytest.raises(ValueError, match="custom_error_msg"), id="custom error msg"
        ),
    ],
)
def test_get_item(
    list_of_dicts: list[dict[Any, Any]],
    key: Any,
    value: Any,
    default: Any | None,
    required: bool,
    case_sensitive: bool,
    var_name: str | None,
    custom_error_msg: str | None,
    expected_result: str,
    expected_raise: Any,
) -> None:
    """Test get_item."""
    # pylint: disable=too-many-arguments
    with expected_raise:
        assert get_item(list_of_dicts, key, value, default, required, case_sensitive, var_name, custom_error_msg) == expected_result
