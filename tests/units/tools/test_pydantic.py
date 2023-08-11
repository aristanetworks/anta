# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tools.pydantic
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import pytest

from anta.tools.pydantic import pydantic_to_dict

if TYPE_CHECKING:
    from anta.result_manager.models import ListResult

EXPECTED_ONE_ENTRY = [
    {
        "name": "testdevice",
        "test": "VerifyTest0",
        "categories": ["test"],
        "description": "Verifies Test 0",
        "error": "None",
        "result": "unset",
        "messages": [],
        "custom_field": "None",
    }
]
EXPECTED_THREE_ENTRIES = [
    {
        "name": "testdevice",
        "test": "VerifyTest0",
        "categories": ["test"],
        "description": "Verifies Test 0",
        "error": "None",
        "result": "unset",
        "messages": [],
        "custom_field": "None",
    },
    {
        "name": "testdevice",
        "test": "VerifyTest1",
        "categories": ["test"],
        "description": "Verifies Test 1",
        "error": "None",
        "result": "unset",
        "messages": [],
        "custom_field": "None",
    },
    {
        "name": "testdevice",
        "test": "VerifyTest2",
        "categories": ["test"],
        "description": "Verifies Test 2",
        "error": "None",
        "result": "unset",
        "messages": [],
        "custom_field": "None",
    },
]


@pytest.mark.parametrize(
    "number_of_entries, expected",
    [
        pytest.param(0, [], id="empty"),
        pytest.param(1, EXPECTED_ONE_ENTRY, id="one"),
        pytest.param(3, EXPECTED_THREE_ENTRIES, id="three"),
    ],
)
def test_pydantic_to_dict(
    list_result_factory: Callable[[int], ListResult],
    number_of_entries: int,
    expected: dict[str, Any],
) -> None:
    """
    Test pydantic_to_dict
    """
    list_result = list_result_factory(number_of_entries)
    assert pydantic_to_dict(list_result) == expected
