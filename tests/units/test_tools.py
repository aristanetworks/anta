# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for `anta.tools`."""

from __future__ import annotations

import asyncio
from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest

# Import as Result to avoid PytestCollectionWarning
from anta.result_manager.models import TestResult as Result
from anta.tools import convert_categories, custom_division, format_data, get_dict_superset, get_failed_logs, get_item, get_value, limit_concurrency

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Sequence

TEST_GET_FAILED_LOGS_DATA = [
    {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "age": 35, "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "age": 40, "email": "charlie@example.com"},
    {"id": 4, "name": "Jon", "age": 25, "email": "Jon@example.com"},
    {"id": 4, "name": "Rob", "age": 25, "email": "Jon@example.com"},
]
TEST_GET_DICT_SUPERSET_DATA = [
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
TEST_GET_VALUE_DATA = {"test_value": 42, "nested_test": {"nested_value": 43}}
TEST_GET_ITEM_DATA = [
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
    ("expected_output", "actual_output", "expected_result"),
    [
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            TEST_GET_FAILED_LOGS_DATA[0],
            "",
            id="no difference",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            TEST_GET_FAILED_LOGS_DATA[1],
            "\nExpected `1` as the id, but found `2` instead.\nExpected `Alice` as the name, but found `Bob` instead.\n"
            "Expected `30` as the age, but found `35` instead.\nExpected `alice@example.com` as the email, but found `bob@example.com` instead.",
            id="different data",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[0],
            {},
            "\nExpected `1` as the id, but it was not found in the actual output.\nExpected `Alice` as the name, but it was not found in the actual output.\n"
            "Expected `30` as the age, but it was not found in the actual output.\nExpected `alice@example.com` as the email, but it was not found in "
            "the actual output.",
            id="empty actual output",
        ),
        pytest.param(
            TEST_GET_FAILED_LOGS_DATA[3],
            TEST_GET_FAILED_LOGS_DATA[4],
            "\nExpected `Jon` as the name, but found `Rob` instead.",
            id="different name",
        ),
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Alice"},
            None,
            False,
            None,
            None,
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="found item",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 10, "name": "Jack"},
            None,
            True,
            "custom_var_name",
            None,
            None,
            pytest.raises(ValueError, match="custom_var_name not found in the provided list."),
            id="custom var_name",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1, "name": "Alice"},
            None,
            True,
            "custom_var_name",
            "Custom error message",
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="custom error message",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
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
            TEST_GET_DICT_SUPERSET_DATA,
            {"id": 1},
            None,
            False,
            None,
            None,
            TEST_GET_DICT_SUPERSET_DATA[1],
            does_not_raise(),
            id="input dictionary is a subset of more than one dictionary in list_of_dicts",
        ),
        pytest.param(
            TEST_GET_DICT_SUPERSET_DATA,
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
    with expected_raise:
        assert get_dict_superset(list_of_dicts, input_dict, default, var_name, custom_error_msg, required=required) == expected_result


@pytest.mark.parametrize(
    (
        "input_dict",
        "key",
        "default",
        "required",
        "org_key",
        "separator",
        "expected_result",
        "expected_raise",
    ),
    [
        pytest.param({}, "test", None, False, None, None, None, does_not_raise(), id="empty dict"),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "test_value",
            None,
            False,
            None,
            None,
            42,
            does_not_raise(),
            id="simple key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "nested_test.nested_value",
            None,
            False,
            None,
            None,
            43,
            does_not_raise(),
            id="nested_key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_value",
            None,
            False,
            None,
            None,
            None,
            does_not_raise(),
            id="missing_value",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_value_with_default",
            "default_value",
            False,
            None,
            None,
            "default_value",
            does_not_raise(),
            id="default",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_required",
            None,
            True,
            None,
            None,
            None,
            pytest.raises(ValueError, match="missing_required"),
            id="required",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "missing_required",
            None,
            True,
            "custom_org_key",
            None,
            None,
            pytest.raises(ValueError, match="custom_org_key"),
            id="custom org_key",
        ),
        pytest.param(
            TEST_GET_VALUE_DATA,
            "nested_test||nested_value",
            None,
            None,
            None,
            "||",
            43,
            does_not_raise(),
            id="custom separator",
        ),
    ],
)
def test_get_value(
    input_dict: dict[Any, Any],
    key: str,
    default: str | None,
    required: bool,
    org_key: str | None,
    separator: str | None,
    expected_result: int | str | None,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_value."""
    kwargs = {
        "default": default,
        "required": required,
        "org_key": org_key,
        "separator": separator,
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    with expected_raise:
        assert get_value(input_dict, key, **kwargs) == expected_result  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("list_of_dicts", "key", "value", "default", "required", "case_sensitive", "var_name", "custom_error_msg", "expected_result", "expected_raise"),
    [
        pytest.param([], "name", "Bob", None, False, False, None, None, None, does_not_raise(), id="empty list"),
        pytest.param([], "name", "Bob", None, True, False, None, None, None, pytest.raises(ValueError, match="name"), id="empty list and required"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", None, False, False, None, None, None, does_not_raise(), id="missing item"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Alice", None, False, False, None, None, TEST_GET_ITEM_DATA[1], does_not_raise(), id="found item"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", "default_value", False, False, None, None, "default_value", does_not_raise(), id="default value"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Jack", None, True, False, None, None, None, pytest.raises(ValueError, match="name"), id="required"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "Bob", None, False, True, None, None, TEST_GET_ITEM_DATA[2], does_not_raise(), id="case sensitive"),
        pytest.param(TEST_GET_ITEM_DATA, "name", "charlie", None, False, False, None, None, TEST_GET_ITEM_DATA[3], does_not_raise(), id="case insensitive"),
        pytest.param(
            TEST_GET_ITEM_DATA,
            "name",
            "Jack",
            None,
            True,
            False,
            "custom_var_name",
            None,
            None,
            pytest.raises(ValueError, match="custom_var_name"),
            id="custom var_name",
        ),
        pytest.param(
            TEST_GET_ITEM_DATA,
            "name",
            "Jack",
            None,
            True,
            False,
            None,
            "custom_error_msg",
            None,
            pytest.raises(ValueError, match="custom_error_msg"),
            id="custom error msg",
        ),
    ],
)
def test_get_item(
    list_of_dicts: list[dict[Any, Any]],
    key: str,
    value: str | None,
    default: str | None,
    required: bool,
    case_sensitive: bool,
    var_name: str | None,
    custom_error_msg: str | None,
    expected_result: str,
    expected_raise: AbstractContextManager[Exception],
) -> None:
    """Test get_item."""
    with expected_raise:
        assert get_item(list_of_dicts, key, value, default, var_name, custom_error_msg, required=required, case_sensitive=case_sensitive) == expected_result


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


@pytest.mark.parametrize(
    ("test_input", "expected_raise", "expected_result"),
    [
        pytest.param([], does_not_raise(), [], id="empty list"),
        pytest.param(["bgp", "system", "vlan", "configuration"], does_not_raise(), ["BGP", "System", "VLAN", "Configuration"], id="list with acronyms and titles"),
        pytest.param(42, pytest.raises(TypeError, match="Wrong input type"), None, id="wrong input type"),
    ],
)
def test_convert_categories(test_input: list[str], expected_raise: AbstractContextManager[Exception], expected_result: list[str]) -> None:
    """Test convert_categories."""
    with expected_raise:
        assert convert_categories(test_input) == expected_result


@pytest.mark.parametrize(
    ("input_data", "expected_output"),
    [
        pytest.param({"advertised": True, "received": True, "enabled": True}, "Advertised: True, Received: True, Enabled: True", id="multiple entry, all True"),
        pytest.param({"advertised": False, "received": False}, "Advertised: False, Received: False", id="multiple entry, all False"),
        pytest.param({}, "", id="empty dict"),
        pytest.param({"test": True}, "Test: True", id="single entry"),
    ],
)
def test_format_data(input_data: dict[str, bool], expected_output: str) -> None:
    """Test format_data."""
    assert format_data(input_data) == expected_output


class TestLimitConcurrency:
    """Test limit_concurrency function."""

    # Helper classes and functions for testing limit_concurrency function
    class _EmptyGenerator:
        """Helper class to create an empty async generator."""

        def __aiter__(self) -> AsyncIterator[Coroutine[Any, Any, Any]]:
            """Make this class an async iterator."""
            return self

        async def __anext__(self) -> Coroutine[Any, Any, Any]:
            """Raise StopAsyncIteration."""
            raise StopAsyncIteration

    async def _mock_test_coro(self, result: Result) -> Result:
        """Mock coroutine simulating a test."""
        # Simulate some work
        await asyncio.sleep(0.1)
        return result

    async def _create_test_generator(self, results: Sequence[Result]) -> AsyncGenerator[Coroutine[Any, Any, Result], None]:
        """Create a test generator yielding mock test coroutines."""
        for result in results:
            yield self._mock_test_coro(result)

    # Unit tests
    async def test_limit_concurrency_with_zero_limit(self) -> None:
        """Test that limit_concurrency raises RuntimeError when limit is 0."""
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await limit_concurrency(generator, limit=0).__anext__()  # pylint: disable=unnecessary-dunder-call

    async def test_limit_concurrency_with_negative_limit(self) -> None:
        """Test that limit_concurrency raises RuntimeError when limit is negative."""
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await limit_concurrency(generator, limit=-1).__anext__()  # pylint: disable=unnecessary-dunder-call

    async def test_limit_concurrency_with_empty_generator(self) -> None:
        """Test limit_concurrency behavior with an empty generator."""
        results = [await result async for result in limit_concurrency(self._EmptyGenerator(), limit=10)]
        assert len(results) == 0

    async def test_limit_concurrency_with_concurrent_limit(self) -> None:
        """Test limit_concurrency enforces the maximum number of concurrently running tasks."""
        max_concurrent = 0
        current_concurrent = 0

        async def instrumented_coro(result: int) -> int:
            nonlocal current_concurrent, max_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            # Simulate work
            await asyncio.sleep(0.1)
            current_concurrent -= 1
            return result

        async def test_generator() -> AsyncGenerator[Coroutine[Any, Any, int], None]:
            for i in range(10):
                yield instrumented_coro(i)

        # Run with limit of 3 to test concurrency limit
        completed_results = [await task async for task in limit_concurrency(test_generator(), limit=3)]

        # Verify all results were returned
        assert len(completed_results) == 10
        # Verify that the maximum number of concurrently running tasks never exceeded the limit
        assert max_concurrent <= 3
