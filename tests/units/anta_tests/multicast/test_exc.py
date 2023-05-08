"""
Tests for anta.tests.multicast.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.multicast import VerifyIGMPSnoopingGlobal, VerifyIGMPSnoopingVlans
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_IGMP_SNOOPING_GLOBAL, INPUT_IGMP_SNOOPING_VLANS


@pytest.mark.parametrize("test_data", INPUT_IGMP_SNOOPING_VLANS, ids=generate_test_ids_list(INPUT_IGMP_SNOOPING_VLANS))
def test_VerifyIGMPSnoopingVlans(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyIGMPSnoopingVlans"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyIGMPSnoopingVlans(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(vlans=test_data["side_effect"]["vlans"], configuration=test_data["side_effect"]["configuration"]))
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_IGMP_SNOOPING_GLOBAL, ids=generate_test_ids_list(INPUT_IGMP_SNOOPING_GLOBAL))
def test_VerifyIGMPSnoopingGlobal(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyIGMPSnoopingGlobal"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyIGMPSnoopingGlobal(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(configuration=test_data["side_effect"]))
    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
