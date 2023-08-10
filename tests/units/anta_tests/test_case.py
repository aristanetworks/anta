from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock


def test(mocked_device: MagicMock, data: dict[str, Any]) -> None:
    # Instantiate the AntaTest subclass
    test = data["test"](mocked_device, inputs=data["inputs"], eos_data=data["eos_data"])
    # Run the test() method
    asyncio.run(test.test())
    # Assert expected result
    assert test.result.result == data["expected"]["result"], test.result.messages
    if "messages" in data["expected"]:
        assert test.result.messages == data["expected"]["messages"]
    else:
        assert test.result.messages == []
