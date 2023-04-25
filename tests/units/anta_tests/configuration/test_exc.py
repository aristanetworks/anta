"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyZeroTouch
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_RUNNING_CONFIG, INPUT_ZEROTOUCH


@pytest.mark.parametrize("test_data", INPUT_ZEROTOUCH, ids=generate_test_ids_list(INPUT_ZEROTOUCH))
def test_VerifyZeroTouch(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyZeroTouch."""

    logging.info(f"Mocked device is: {mocked_device.host}")

    test = VerifyZeroTouch(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_RUNNING_CONFIG, ids=generate_test_ids_list(INPUT_RUNNING_CONFIG))
def test_VerifyRunningConfigDiffs(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyRunningConfigDiffs."""

    logging.info(f"Mocked device is: {mocked_device.host}")

    test = VerifyRunningConfigDiffs(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
