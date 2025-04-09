# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests module."""

import asyncio

from anta.device import AntaDevice
from anta.models import AntaTest, AntaUnitTest


def test(device: AntaDevice, data: tuple[tuple[type[AntaTest], str], AntaUnitTest]) -> None:
    """Generic test function for AntaTest subclass.

    Generate unit tests for each AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    anta_test = data[0][0]
    test_data = data[1]
    # Instantiate the AntaTest subclass
    test_instance = anta_test(device, inputs=test_data["inputs"], eos_data=test_data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())
    # Assert expected result
    assert test_instance.result.result == test_data["expected"]["result"], (
        f"Expected '{test_data['expected']['result']}' result, got '{test_instance.result.result}'"
    )
    if "messages" in test_data["expected"]:
        # We expect messages in test result
        assert len(test_instance.result.messages) == len(test_data["expected"]["messages"])
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test_instance.result.messages, test_data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test_instance.result.messages == []
