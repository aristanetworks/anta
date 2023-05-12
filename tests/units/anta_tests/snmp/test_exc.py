"""
Tests for anta.tests.snmp.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.snmp import VerifySnmpIPv4Acl, VerifySnmpIPv6Acl, VerifySnmpStatus
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_SNMP_IPV4_ACL, INPUT_SNMP_IPV6_ACL, INPUT_SNMP_STATUS


@pytest.mark.parametrize("test_data", INPUT_SNMP_STATUS, ids=generate_test_ids_list(INPUT_SNMP_STATUS))
def test_VerifySnmpStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySnmpStatus."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySnmpStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(vrf=test_data["side_effect"]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SNMP_IPV4_ACL, ids=generate_test_ids_list(INPUT_SNMP_IPV4_ACL))
def test_VerifySnmpIPv4Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySnmpIPv4Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySnmpIPv4Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SNMP_IPV6_ACL, ids=generate_test_ids_list(INPUT_SNMP_IPV6_ACL))
def test_VerifySnmpIPv6Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySnmpIPv6Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySnmpIPv6Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
