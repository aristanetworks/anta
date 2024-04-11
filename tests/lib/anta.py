# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""generic test function used to generate unit tests for each AntaTest."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from anta.device import AntaDevice


def test(device: AntaDevice, data: dict[str, Any]) -> None:
    """Generic test function for AntaTest subclass.

    See `tests/units/anta_tests/README.md` for more information on how to use it.
    """
    # Instantiate the AntaTest subclass
    test_instance = data["test"](device, inputs=data["inputs"], eos_data=data["eos_data"])
    # Run the test() method
    asyncio.run(test_instance.test())
    # Assert expected result
    assert test_instance.result.result == data["expected"]["result"], test_instance.result.messages
    if "messages" in data["expected"]:
        # We expect messages in test result
        assert len(test_instance.result.messages) == len(data["expected"]["messages"])
        # Test will pass if the expected message is included in the test result message
        for message, expected in zip(test_instance.result.messages, data["expected"]["messages"]):  # NOTE: zip(strict=True) has been added in Python 3.10
            assert expected in message
    else:
        # Test result should not have messages
        assert test_instance.result.messages == []
