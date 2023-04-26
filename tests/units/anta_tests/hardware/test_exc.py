# -*- coding: utf-8 -*-

"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.hardware import VerifyTransceiversManufacturers
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_MANUFACTURER


@pytest.mark.parametrize("test_data", INPUT_MANUFACTURER, ids=generate_test_ids_list(INPUT_MANUFACTURER))
def test_VerifyTransceiversManufacturers(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTransceiversManufacturers."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTransceiversManufacturers(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(manufacturers=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
