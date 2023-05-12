"""
Tests for anta.tests.routing.ospf.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.routing.ospf import VerifyOSPFNeighborCount, VerifyOSPFNeighborState
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_OSPF_NEIGHBOR_COUNT, INPUT_OSPF_NEIGHBOR_STATE


@pytest.mark.parametrize("test_data", INPUT_OSPF_NEIGHBOR_STATE, ids=generate_test_ids_list(INPUT_OSPF_NEIGHBOR_STATE))
def test_VerifyOSPFNeighborState(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyOSPFNeighborState."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyOSPFNeighborState(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_OSPF_NEIGHBOR_COUNT, ids=generate_test_ids_list(INPUT_OSPF_NEIGHBOR_COUNT))
def test_VerifyOSPFNeighborCount(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyOSPFNeighborCount."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyOSPFNeighborCount(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
