# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from anta.models import AntaTest

if TYPE_CHECKING:
    import sys

    from anta.device import AntaDevice
    from anta.result_manager.models import AntaTestStatus

    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired

    from typing import TypeAlias


class UnitTestResult(TypedDict):
    """Expected result of a unit test of an AntaTest subclass.

    For our AntaTest unit tests we expect only success, failure or skipped.
    Never unset nor error.
    """

    result: Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.SKIPPED]
    messages: NotRequired[list[str]]


class AntaUnitTest(TypedDict):
    """The parameters required for a unit test of an AntaTest subclass."""

    inputs: NotRequired[dict[str, Any]]
    eos_data: list[dict[str, Any] | str]
    expected: UnitTestResult


AntaUnitTestData: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]


def test(device: AntaDevice, anta_test: type[AntaTest], unit_test_data: AntaUnitTest) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    # Instantiate the AntaTest subclass
    test_instance = anta_test(device, inputs=unit_test_data.get("inputs"), eos_data=unit_test_data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())

    # Assert expected result
    assert test_instance.result.result == unit_test_data["expected"]["result"], (
        f"Expected '{unit_test_data['expected']['result']}' result, got '{test_instance.result.result}'. Messages: {test_instance.result.messages}"
    )
    # Assert test messages
    if "messages" in unit_test_data["expected"]:
        # Assert number of messages
        assert len(test_instance.result.messages) == len(unit_test_data["expected"]["messages"]), (
            f"Expected {len(unit_test_data['expected']['messages'])} messages, got {len(test_instance.result.messages)}"
        )
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(
            test_instance.result.messages, unit_test_data["expected"]["messages"], strict=False
        ):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message, f"Expected message '{expected}' not found in '{message}'"
    else:
        # Test result should not have messages
        assert test_instance.result.messages == [], "There are untested messages, see diffs with '-vv' option"
