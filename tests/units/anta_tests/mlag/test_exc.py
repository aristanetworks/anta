# -*- coding: utf-8 -*-

"""
Tests for anta.tests.mlag.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.mlag import (
    VerifyMlagStatus,
    VerifyMlagInterfaces
)

from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_MLAG_STATUS,
    INPUT_MLAG_INTERFACES
)

@pytest.mark.parametrize("test_data", INPUT_MLAG_STATUS, ids=generate_test_ids_list(INPUT_MLAG_STATUS))
def test_VerifyMlagStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMlagStatus"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMlagStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_MLAG_INTERFACES, ids=generate_test_ids_list(INPUT_MLAG_INTERFACES))
def test_VerifyMlagInterfaces(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMlagInterfaces"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMlagInterfaces(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]