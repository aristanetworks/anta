# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired  # NOTE: required to support Python < 3.11 https://peps.python.org/pep-0655/#usage-in-python-3-11

    from anta.device import AntaDevice
    from anta.models import AntaTest


class AtomicResult(TypedDict):
    """Expected atomic result of a unit test of an AntaTest subclass."""

    result: Literal["success", "failure", "skipped"]  # TODO: Refactor tests and use AntaTestStatus
    description: str
    messages: NotRequired[list[str]]
    inputs: NotRequired[dict[str, Any]]


class Expected(TypedDict):
    """Expected result of a unit test of an AntaTest subclass."""

    result: Literal["success", "failure", "skipped"]  # TODO: Refactor tests and use AntaTestStatus
    messages: NotRequired[list[str]]
    atomic_results: NotRequired[list[AtomicResult]]


class AntaUnitTest(TypedDict):
    """The parameters required for a unit test of an AntaTest subclass."""

    name: str  # TODO: Refactor tests and change the DATA constant type as dictionary instead of list[AntaUnitTest] to avoid test duplicates.
    test: type[AntaTest]
    inputs: NotRequired[dict[str, Any]]
    eos_data: list[dict[str, Any] | str]
    expected: Expected


def test(device: AntaDevice, data: dict[str, Any]) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    # Instantiate the AntaTest subclass
    test_instance = data["test"](device, inputs=data.get("inputs"), eos_data=data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())
    # Assert expected result
    assert test_instance.result.result == data["expected"]["result"], f"Expected '{data['expected']['result']}' result, got '{test_instance.result.result}'"
    if "messages" in data["expected"]:
        # We expect messages in test result
        assert len(test_instance.result.messages) == len(data["expected"]["messages"]), (
            f"Expected {len(data['expected']['messages'])} messages, got {len(test_instance.result.messages)}"
        )
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test_instance.result.messages, data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test_instance.result.messages == [], "There are untested messages"

    if "atomic_results" in data["expected"]:
        assert len(test_instance.result.atomic_results) == len(data["expected"]["atomic_results"]), (
            f"Expected {len(data['expected']['atomic_results'])} atomic results, got {len(test_instance.result.atomic_results)}"
        )
        for atomic_result_model, expected_atomic_result in zip(test_instance.result.atomic_results, data["expected"]["atomic_results"]):
            atomic_result = atomic_result_model.model_dump(mode="json", exclude_none=True)
            if len(atomic_result["messages"]):
                for message, expected in zip(atomic_result["messages"], expected_atomic_result["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
                    assert expected in message
            else:
                del atomic_result["messages"]
            assert atomic_result == expected_atomic_result
    else:
        # Test result should not have atomic results
        assert test_instance.result.atomic_results == [], "There are untested atomic results"
