# -*- coding: utf-8 -*-

# pylint: disable = unused-import
# pylint: disable = redefined-outer-name
# flake8: noqa

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
from tests.data.anta_tests.hardware import INPUT_MANUFACTURER
from tests.lib.fixture import mocked_device
from tests.lib.utils import generate_test_ids_list


@pytest.mark.parametrize("test_data", INPUT_MANUFACTURER, ids=generate_test_ids_list(INPUT_MANUFACTURER))
def test_VerifyTransceiversManufacturers(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTransceiversManufacturers."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTransceiversManufacturers(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(manufacturers=test_data["side_effect"]))

    logging.info(f"test input is: {test_data['side_effect']}")
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_message"]


@pytest.mark.parametrize("test_data", INPUT_MANUFACTURER, ids=generate_test_ids_list(INPUT_MANUFACTURER))
def test_VerifyTransceiversManufacturers_skipped(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTransceiversManufacturers."""

    mocked_device.hw_model = "cEOSLab"
    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTransceiversManufacturers(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(manufacturers=test_data["side_effect"]))

    logging.info(f"test input is: {test_data['side_effect']}")
    logging.info(f"test result is: {test.result}")

    if mocked_device.hw_model == "cEOSLab":
        assert test.result.result == "skipped"
