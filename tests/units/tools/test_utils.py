# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.tools.utils`."""

from __future__ import annotations

from typing import Any

import pytest

from anta.tools.utils import custom_division, get_failed_logs

EXPECTED_OUTPUTS = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Jon", "age": 25, "email": "Jon@example.com"},
    {"id": 5, "name": "Jon", "age": 45, "email": "Jon@example.com"},
]

ACTUAL_OUTPUTS = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Rob", "age": 25, "email": "Jon@example.com"},
    {"id": 5, "name": "Jon", "email": "Jon@example.com"},
]


@pytest.mark.parametrize(
    ("expected_output", "actual_output", "expected_result"),
    [
        pytest.param(
            EXPECTED_OUTPUTS[0],
            ACTUAL_OUTPUTS[0],
            "",
            id="no difference",
        ),
        pytest.param(
            EXPECTED_OUTPUTS[0],
            ACTUAL_OUTPUTS[1],
            "\nExpected `1` as the id, but found `2` instead.\nExpected `Alice` as the name, but found `Bob` instead.\n"
            "Expected `30` as the age, but found `35` instead.\nExpected `alice@example.com` as the email, but found `bob@example.com` instead.",
            id="different data",
        ),
        pytest.param(
            EXPECTED_OUTPUTS[0],
            {},
            "\nExpected `1` as the id, but it was not found in the actual output.\nExpected `Alice` as the name, but it was not found in the actual output.\n"
            "Expected `30` as the age, but it was not found in the actual output.\nExpected `alice@example.com` as the email, but it was not found in "
            "the actual output.",
            id="empty actual output",
        ),
        pytest.param(
            EXPECTED_OUTPUTS[3],
            ACTUAL_OUTPUTS[3],
            "\nExpected `Jon` as the name, but found `Rob` instead.",
            id="different name",
        ),
        pytest.param(EXPECTED_OUTPUTS[4], ACTUAL_OUTPUTS[4], "\nExpected `45` as the age, but it was not found in the actual output.", id="missing age"),
    ],
)
def test_get_failed_logs(
    expected_output: dict[Any, Any],
    actual_output: dict[Any, Any],
    expected_result: str,
) -> None:
    """Test get_failed_logs."""
    assert get_failed_logs(expected_output, actual_output) == expected_result


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected_result"),
    [
        pytest.param(4.0, 2.0, 2, id="int return for float input"),
        pytest.param(4, 2, 2, id="int return for int input"),
        pytest.param(5.0, 2.0, 2.5, id="float return for float input"),
        pytest.param(5, 2, 2.5, id="float return for int input"),
    ],
)
def test_custom_division(numerator: float, denominator: float, expected_result: str) -> None:
    """Test custom_division."""
    assert custom_division(numerator, denominator) == expected_result
