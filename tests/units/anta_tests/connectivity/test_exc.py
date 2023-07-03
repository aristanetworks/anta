"""
Tests for anta.tests.connectivity.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.connectivity import VerifyReachability
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_REACHABILITY


@pytest.mark.parametrize("test_data", INPUT_REACHABILITY, ids=generate_test_ids_list(INPUT_REACHABILITY))
def test_VerifyReachability(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyReachability"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyReachability(mocked_device, eos_data=test_data["eos_data"], template_params=test_data["side_effect"]["template_params"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
