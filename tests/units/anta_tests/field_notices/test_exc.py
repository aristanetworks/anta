"""
Tests for anta.tests.field_notices.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.field_notices import VerifyFieldNotice44Resolution, VerifyFieldNotice72Resolution
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_FIELD_NOTICE_44_RESOLUTION, INPUT_FIELD_NOTICE_72_RESOLUTION


@pytest.mark.parametrize("test_data", INPUT_FIELD_NOTICE_44_RESOLUTION, ids=generate_test_ids_list(INPUT_FIELD_NOTICE_44_RESOLUTION))
def test_VerifyFieldNotice44Resolution(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyFieldNotice44Resolution."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyFieldNotice44Resolution(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_FIELD_NOTICE_72_RESOLUTION, ids=generate_test_ids_list(INPUT_FIELD_NOTICE_72_RESOLUTION))
def test_VerifyFieldNotice72Resolution(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyFieldNotice72Resolution."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyFieldNotice72Resolution(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
