# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.tools.get_dict_superset`."""
from __future__ import annotations

from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

from anta.tools.get_dict_superset import get_dict_superset

# pylint: disable=duplicate-code
DUMMY_DATA = [
    ("id", 0),
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
    (
        "list_of_dicts",
        "input_dict",
        "default",
        "required",
        "var_name",
        "custom_error_msg",
        "expected_result",
        "expected_raise",
    ),
    [
        pytest.param(
            [],
            {"id": 1, "name": "Alice"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="empty list",
        ),
        pytest.param(
            [],
            {"id": 1, "name": "Alice"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="empty list and required",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 10, "name": "Jack"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="missing item",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 1, "name": "Alice"},
            None,
            False,
            None,
            None,
            DUMMY_DATA[1],
            does_not_raise(),
            id="found item",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 10, "name": "Jack"},
            "default_value",
            False,
            None,
            None,
            "default_value",
            does_not_raise(),
            id="default value",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="required",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            "custom_var_name",
            None,
            None,
            pytest.raises(
                ValueError, match="custom_var_name not found in the provided list."
            ),
            id="custom var_name",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 1, "name": "Alice"},
            None,
            True,
            "custom_var_name",
            "Custom error message",
            DUMMY_DATA[1],
            does_not_raise(),
            id="custom error message",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            "custom_var_name",
            "Custom error message",
            None,
            pytest.raises(ValueError, match="Custom error message"),
            id="custom error message and required",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 1, "name": "Jack"},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="id ok but name not ok",
        ),
        pytest.param(
            "not a list",
            {"id": 1, "name": "Alice"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="non-list input for list_of_dicts",
        ),
        pytest.param(
            DUMMY_DATA,
            "not a dict",
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="non-dictionary input",
        ),
        pytest.param(
            DUMMY_DATA,
            {},
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="empty dictionary input",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 1, "name": "Alice", "extra_key": "extra_value"},
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="input dictionary with extra keys",
        ),
        pytest.param(
            DUMMY_DATA,
            {"id": 1},
            None,
            False,
            None,
            None,
            DUMMY_DATA[1],
            does_not_raise(),
            id="input dictionary is a subset of more than one dictionary in list_of_dicts",
        ),
        pytest.param(
            DUMMY_DATA,
            {
                "id": 1,
                "name": "Alice",
                "age": 30,
                "email": "alice@example.com",
                "extra_key": "extra_value",
            },
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="not found in the provided list."),
            id="input dictionary is a superset of a dictionary in list_of_dicts",
        ),
    ],
)
def test_get_dict_superset(
    list_of_dicts: list[dict[Any, Any]],
    input_dict: dict[Any, Any],
    default: str | None,
    required: bool,
    var_name: str | None,
    custom_error_msg: str | None,
    expected_result: str,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_dict_superset."""
    # pylint: disable=too-many-arguments
    with expected_raise:
        assert (
            get_dict_superset(
                list_of_dicts, input_dict, default, required, var_name, custom_error_msg
            )
            == expected_result
        )
