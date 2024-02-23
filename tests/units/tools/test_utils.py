# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.

"""Tests for `anta.tools.utils`."""
from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

from anta.tools.utils import custom_division, extract_speed_and_lane, get_failed_logs

EXPECTED_OUTPUTS = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Jon", "age": 25, "email": "Jon@example.com"},
]

ACTUAL_OUTPUTS = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Rob", "age": 25, "email": "Jon@example.com"},
]


@pytest.mark.parametrize(
    "expected_output, actual_output, expected_result, expected_raise",
    [
        pytest.param(EXPECTED_OUTPUTS[0], ACTUAL_OUTPUTS[0], "", does_not_raise(), id="no difference"),
        pytest.param(
            EXPECTED_OUTPUTS[0],
            ACTUAL_OUTPUTS[1],
            "\nExpected `1` as the id, but found `2` instead.\nExpected `Alice` as the name, but found `Bob` instead.\n"
            "Expected `30` as the age, but found `35` instead.\nExpected `alice@example.com` as the email, but found `bob@example.com` instead.",
            does_not_raise(),
            id="different data",
        ),
        pytest.param(
            EXPECTED_OUTPUTS[0],
            {},
            "\nExpected `1` as the id, but it was not found in the actual output.\nExpected `Alice` as the name, but it was not found in the actual output.\n"
            "Expected `30` as the age, but it was not found in the actual output.\nExpected `alice@example.com` as the email, but it was not found in "
            "the actual output.",
            does_not_raise(),
            id="empty actual output",
        ),
        pytest.param(EXPECTED_OUTPUTS[3], ACTUAL_OUTPUTS[3], "\nExpected `Jon` as the name, but found `Rob` instead.", does_not_raise(), id="different name"),
    ],
)
def test_get_failed_logs(expected_output: dict[Any, Any], actual_output: dict[Any, Any], expected_result: str, expected_raise: Any) -> None:
    """Test get_failed_logs."""
    with expected_raise:
        assert get_failed_logs(expected_output, actual_output) == expected_result


@pytest.mark.parametrize(
    "numerator, denominator, expected_result, expected_raise",
    [
        pytest.param(4.0, 2.0, 2, does_not_raise(), id="int return for float input"),
        pytest.param(4, 2, 2, does_not_raise(), id="int return for int input"),
        pytest.param(5.0, 2.0, 2.5, does_not_raise(), id="float return for float input"),
        pytest.param(5, 2, 2.5, does_not_raise(), id="float return for int input"),
    ],
)
def test_custom_division(numerator: int | float, denominator: int | float, expected_result: str, expected_raise: Any) -> None:
    """Test custom_division."""
    with expected_raise:
        assert custom_division(numerator, denominator) == expected_result


@pytest.mark.parametrize(
    "speed, expected_result, expected_raise",
    [
        pytest.param("100g-4", ("100", 4), does_not_raise(), id="Speed with lane `100g-4`"),
        pytest.param("100g", ("100", None), does_not_raise(), id="Speed without lane `100g-4`"),
        pytest.param("auto 100g-8", ("100", 8), does_not_raise(), id="Auto speed with lane `auto 100g-8`"),
        pytest.param("auto 10", ("10", None), does_not_raise(), id="Auto speed without lane `auto 10`"),
        pytest.param("auto", (None, None), does_not_raise(), id="Only auto speed `auto`"),
        pytest.param("forced 2.5g", ("2.5", None), does_not_raise(), id="Forced speed without lane `forced 2.5g`"),
    ],
)
def test_extract_speed_and_lane(speed: str, expected_result: str, expected_raise: Any) -> None:
    """Test extract_speed_and_lane."""
    with expected_raise:
        assert extract_speed_and_lane(speed) == expected_result
