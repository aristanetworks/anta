# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from anta.models import AntaTest

if TYPE_CHECKING:
    from typing_extensions import NotRequired  # NOTE: required to support Python < 3.11 https://peps.python.org/pep-0655/#usage-in-python-3-11

    from anta.device import AntaDevice
    from anta.result_manager.models import AntaTestStatus

    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = type

class AtomicResult(TypedDict):
    """Expected atomic result of a unit test of an AntaTest subclass."""

    description: str
    result: Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.SKIPPED]
    messages: NotRequired[list[str]]
    inputs: NotRequired[dict[str, Any]]

class UnitTestResult(TypedDict):
    """Expected result of a unit test of an AntaTest subclass.

    For our AntaTest unit tests we expect only success, failure or skipped.
    Never unset nor error.
    """

    result: Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.SKIPPED]
    messages: NotRequired[list[str]]
    atomic_results: NotRequired[list[AtomicResult]]

class AntaUnitTest(TypedDict):
    """The parameters required for a unit test of an AntaTest subclass."""

    inputs: NotRequired[dict[str, Any]]
    eos_data: list[dict[str, Any] | str]
    expected: UnitTestResult

AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

def test(device: AntaDevice, data: tuple[tuple[type[AntaTest], str], AntaUnitTest]) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    # Extract the test class, name and test data from a nested tuple structure:
    # `val: Tuple[Tuple[Type[AntaTest], str], AntaUnitTest]`
    (anta_test, _name), test_data = data

    # Instantiate the AntaTest subclass
    test_instance = anta_test(device, inputs=test_data.get("inputs"), eos_data=test_data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())

    # Assert expected result
    assert test_instance.result.result == test_data["expected"]["result"], (
        f"Expected '{test_data['expected']['result']}' result, got '{test_instance.result.result}'. Messages: {test_instance.result.messages}"
    )
    if "messages" in test_data["expected"]:
        # We expect messages in test result
        assert len(test_instance.result.messages) == len(
            data["expected"]["messages"]
        ), f"Expected {len(data['expected']['messages'])} messages, got {len(test_instance.result.messages)}"
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test_instance.result.messages, test_data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test_instance.result.messages == [], "There are untested messages"

    if "atomic_results" in data["expected"]:
        assert len(test_instance.result.atomic_results) == len(
            data["expected"]["atomic_results"]
        ), f"Expected {len(data['expected']['atomic_results'])} atomic results, got {len(test_instance.result.atomic_results)}"
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
