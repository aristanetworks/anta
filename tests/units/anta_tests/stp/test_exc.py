"""
Tests for anta.tests.stp.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.stp import VerifySTPBlockedPorts, VerifySTPCounters, VerifySTPForwardingPorts, VerifySTPMode, VerifySTPRootPriority
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_STP_BLOCKED_PORTS, INPUT_STP_COUNTERS, INPUT_STP_FORWARDING_PORTS, INPUT_STP_MODE, INPUT_STP_ROOT_PRIORITY


@pytest.mark.parametrize("test_data", INPUT_STP_MODE, ids=generate_test_ids_list(INPUT_STP_MODE))
def test_VerifySTPMode(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySTPMode"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySTPMode(mocked_device, eos_data=test_data["eos_data"], template_params=test_data["side_effect"]["template_params"])
    asyncio.run(test.test(mode=test_data["side_effect"]["mode"]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_STP_BLOCKED_PORTS, ids=generate_test_ids_list(INPUT_STP_BLOCKED_PORTS))
def test_VerifySTPBlockedPorts(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySTPBlockedPorts"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySTPBlockedPorts(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_STP_COUNTERS, ids=generate_test_ids_list(INPUT_STP_COUNTERS))
def test_VerifySTPCounters(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySTPCounters"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySTPCounters(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_STP_FORWARDING_PORTS, ids=generate_test_ids_list(INPUT_STP_FORWARDING_PORTS))
def test_VerifySTPForwardingPorts(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySTPForwardingPorts"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySTPForwardingPorts(mocked_device, eos_data=test_data["eos_data"], template_params=test_data["side_effect"]["template_params"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_STP_ROOT_PRIORITY, ids=generate_test_ids_list(INPUT_STP_ROOT_PRIORITY))
def test_VerifySTPRootPriority(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySTPRootPriority"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySTPRootPriority(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(priority=test_data["side_effect"]["priority"], instances=test_data["side_effect"]["instances"]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
