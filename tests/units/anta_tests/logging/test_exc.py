"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.logging import (
    VerifyLoggingAccounting,
    VerifyLoggingHostname,
    VerifyLoggingHosts,
    VerifyLoggingLogsGeneration,
    VerifyLoggingPersistent,
    VerifyLoggingSourceIntf,
    VerifyLoggingTimestamp,
)
from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_LOGGING_ACCOUNTING,
    INPUT_LOGGING_HOSTNAME,
    INPUT_LOGGING_HOSTS,
    INPUT_LOGGING_LOGS_GEN,
    INPUT_LOGGING_PERSISTENT,
    INPUT_LOGGING_SOURCE_INTF,
    INPUT_LOGGING_TIMESTAMP,
)


@pytest.mark.parametrize("test_data", INPUT_LOGGING_PERSISTENT, ids=generate_test_ids_list(INPUT_LOGGING_PERSISTENT))
def test_VerifyLoggingPersistent(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingPersistent."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingPersistent(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_SOURCE_INTF, ids=generate_test_ids_list(INPUT_LOGGING_SOURCE_INTF))
def test_VerifyLoggingSourceIntf(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingSourceIntf."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingSourceIntf(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(intf=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_HOSTS, ids=generate_test_ids_list(INPUT_LOGGING_HOSTS))
def test_VerifyLoggingHosts(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingHosts."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingHosts(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(hosts=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_LOGS_GEN, ids=generate_test_ids_list(INPUT_LOGGING_LOGS_GEN))
def test_VerifyLoggingLogsGeneration(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingLogsGeneration."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingLogsGeneration(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_HOSTNAME, ids=generate_test_ids_list(INPUT_LOGGING_HOSTNAME))
def test_VerifyLoggingHostname(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingHostname."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingHostname(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_TIMESTAMP, ids=generate_test_ids_list(INPUT_LOGGING_TIMESTAMP))
def test_VerifyLoggingTimestamp(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingTimestamp."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingTimestamp(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOGGING_ACCOUNTING, ids=generate_test_ids_list(INPUT_LOGGING_ACCOUNTING))
def test_VerifyLoggingAccounting(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoggingAccounting."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoggingAccounting(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
