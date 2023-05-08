"""
Tests for anta.tests.profiles.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.profiles import VerifyTcamProfile, VerifyUnifiedForwardingTableMode
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_TCAM_PROFILE, INPUT_UFT_SETTING


@pytest.mark.parametrize("test_data", INPUT_UFT_SETTING, ids=generate_test_ids_list(INPUT_UFT_SETTING))
def test_VerifyUnifiedForwardingTableMode(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyUnifiedForwardingTableMode"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyUnifiedForwardingTableMode(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(mode=test_data["side_effect"]))
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_TCAM_PROFILE, ids=generate_test_ids_list(INPUT_TCAM_PROFILE))
def test_VerifyTcamProfile(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTcamProfile"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTcamProfile(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(profile=test_data["side_effect"]))
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
