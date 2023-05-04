"""
Tests for anta.tests.system.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.system import (
    VerifyAgentLogs,
    VerifyCoredump,
    VerifyCPUUtilization,
    VerifyFileSystemUtilization,
    VerifyMemoryUtilization,
    VerifyNTP,
    VerifyReloadCause,
    VerifySyslog,
    VerifyUptime,
)
from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_AGENT_LOGS,
    INPUT_COREDUMP,
    INPUT_CPU_UTILIZATION,
    INPUT_FILE_SYSTEM_UTILIZATION,
    INPUT_MEMORY_UTILIZATION,
    INPUT_NTP,
    INPUT_RELOAD_CAUSE,
    INPUT_SYSLOG,
    INPUT_UPTIME,
)


@pytest.mark.parametrize("test_data", INPUT_UPTIME, ids=generate_test_ids_list(INPUT_UPTIME))
def test_VerifyUptime(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyUptime."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyUptime(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(minimum=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_RELOAD_CAUSE, ids=generate_test_ids_list(INPUT_RELOAD_CAUSE))
def test_VerifyReloadCause(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyReloadCause."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyReloadCause(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_COREDUMP, ids=generate_test_ids_list(INPUT_COREDUMP))
def test_VerifyCoredump(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyCoredump."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyCoredump(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_AGENT_LOGS, ids=generate_test_ids_list(INPUT_AGENT_LOGS))
def test_VerifyAgentLogs(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAgentLogs."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAgentLogs(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SYSLOG, ids=generate_test_ids_list(INPUT_SYSLOG))
def test_VerifySyslog(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySyslog."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySyslog(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_CPU_UTILIZATION, ids=generate_test_ids_list(INPUT_CPU_UTILIZATION))
def test_VerifyCPUUtilization(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyCPUUtilization."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyCPUUtilization(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_MEMORY_UTILIZATION, ids=generate_test_ids_list(INPUT_MEMORY_UTILIZATION))
def test_VerifyMemoryUtilization(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMemoryUtilization."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMemoryUtilization(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_FILE_SYSTEM_UTILIZATION, ids=generate_test_ids_list(INPUT_FILE_SYSTEM_UTILIZATION))
def test_VerifyFileSystemUtilization(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyFileSystemUtilization."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyFileSystemUtilization(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_NTP, ids=generate_test_ids_list(INPUT_NTP))
def test_VerifyNTP(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyNTP."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyNTP(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.debug(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
