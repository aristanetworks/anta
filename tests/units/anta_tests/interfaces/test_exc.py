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

from anta.tests.interfaces import VerifyInterfaceErrors, VerifyInterfaceUtilization
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_INTERFACE_ERRORS, INPUT_INTERFACE_UTILIZATION


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_UTILIZATION, ids=generate_test_ids_list(INPUT_INTERFACE_UTILIZATION))
def test_VerifyInterfaceUtilization(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceUtilization"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceUtilization(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_ERRORS, ids=generate_test_ids_list(INPUT_INTERFACE_ERRORS))
def test_VerifyInterfaceErrors(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceErrors"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceErrors(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
