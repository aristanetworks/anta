"""
Tests for anta.tests.routing.generic.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.routing.generic import VerifyBFD, VerifyRoutingProtocolModel, VerifyRoutingTableSize
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_BFD, INPUT_ROUTING_PROTOCOL_MODEL, INPUT_ROUTING_TABLE_SIZE


@pytest.mark.parametrize("test_data", INPUT_ROUTING_PROTOCOL_MODEL, ids=generate_test_ids_list(INPUT_ROUTING_PROTOCOL_MODEL))
def test_VerifyRoutingProtocolModel(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyRoutingProtocolModel."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyRoutingProtocolModel(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(model=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_ROUTING_TABLE_SIZE, ids=generate_test_ids_list(INPUT_ROUTING_TABLE_SIZE))
def test_VerifyRoutingTableSize(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyRoutingTableSize."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyRoutingTableSize(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(minimum=test_data["side_effect"]["minimum"], maximum=test_data["side_effect"]["maximum"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BFD, ids=generate_test_ids_list(INPUT_BFD))
def test_VerifyBFD(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBFD."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyBFD(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
