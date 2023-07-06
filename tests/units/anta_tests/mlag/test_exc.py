"""
Tests for anta.tests.mlag.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.mlag import VerifyMlagConfigSanity, VerifyMlagDualPrimary, VerifyMlagInterfaces, VerifyMlagReloadDelay, VerifyMlagStatus
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_MLAG_CONFIG_SANITY, INPUT_MLAG_DUAL_PRIMARY, INPUT_MLAG_INTERFACES, INPUT_MLAG_RELOAD_DELAY, INPUT_MLAG_STATUS


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


@pytest.mark.parametrize("test_data", INPUT_MLAG_CONFIG_SANITY, ids=generate_test_ids_list(INPUT_MLAG_CONFIG_SANITY))
def test_VerifyMlagConfigSanity(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMlagConfigSanity"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMlagConfigSanity(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_MLAG_RELOAD_DELAY, ids=generate_test_ids_list(INPUT_MLAG_RELOAD_DELAY))
def test_VerifyMlagReloadDelay(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMlagReloadDelay"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMlagReloadDelay(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(reload_delay=test_data["side_effect"]["reload_delay"], reload_delay_non_mlag=test_data["side_effect"]["reload_delay_non_mlag"]))
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_MLAG_DUAL_PRIMARY, ids=generate_test_ids_list(INPUT_MLAG_DUAL_PRIMARY))
def test_VerifyMlagDualPrimary(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyMlagDualPrimary"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyMlagDualPrimary(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(
        test.test(
            detection_delay=test_data["side_effect"]["detection_delay"],
            errdisabled=test_data["side_effect"]["errdisabled"],
            recovery_delay=test_data["side_effect"]["recovery_delay"],
            recovery_delay_non_mlag=test_data["side_effect"]["recovery_delay_non_mlag"],
        )
    )
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
