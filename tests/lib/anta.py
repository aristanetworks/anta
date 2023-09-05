# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock


def test(mocked_device: MagicMock, data: dict[str, Any]) -> None:
    """
    Generic test case for AntaTest subclass.
    See tests/units/anta_tests/README.md for more information on how to use it.
    """
    # Instantiate the AntaTest subclass
    test = data["test"](mocked_device, inputs=data["inputs"], eos_data=data["eos_data"])
    # Run the test() method
    asyncio.run(test.test())
    # Assert expected result
    assert test.result.result == data["expected"]["result"], test.result.messages
    if "messages" in data["expected"]:
        # We expect messages in test result
        assert len(test.result.messages) == len(data["expected"]["messages"])
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test.result.messages, data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test.result.messages == []
