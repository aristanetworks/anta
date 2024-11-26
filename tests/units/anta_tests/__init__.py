# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

import asyncio
from typing import Any

from anta.device import AntaDevice


def test(device: AntaDevice, data: dict[str, Any]) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    # Instantiate the AntaTest subclass
    test_instance = data["test"](device, inputs=data["inputs"], eos_data=data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())
    # Assert expected result
    assert test_instance.result.result == data["expected"]["result"], f"Expected '{data['expected']['result']}' result, got '{test_instance.result.result}'"
    if "messages" in data["expected"]:
        # We expect messages in test result
        assert len(test_instance.result.messages) == len(
            data["expected"]["messages"]
        ), f"Expected {len(data['expected']['messages'])} messages, got {len(test_instance.result.messages)}"
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test_instance.result.messages, data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test_instance.result.messages == [], "There are untested messages"

    if "atomic_results" in data["expected"]:
        assert len(test_instance.result.atomic_results) == len(
            data["expected"]["atomic_results"]
        ), f"Expected {len(data['expected']['atomic_results'])} atomic results, got {len(test_instance.result.atomic_results)}"
        for result, expected in zip(test_instance.result.atomic_results, data["expected"]["atomic_results"]):
            assert result.model_dump(serialize_as_any=True, mode="json") == expected
    else:
        # Test result should not have atomic results
        assert test_instance.result.atomic_results == [], "There are untested atomic results"
