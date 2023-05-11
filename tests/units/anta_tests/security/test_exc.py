"""
Tests for anta.tests.security.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.security import (
    VerifyAPIHttpsSSL,
    VerifyAPIHttpStatus,
    VerifyAPIIPv4Acl,
    VerifyAPIIPv6Acl,
    VerifySSHIPv4Acl,
    VerifySSHIPv6Acl,
    VerifySSHStatus,
    VerifyTelnetStatus,
)
from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_API_IPV4_ACL,
    INPUT_API_IPV6_ACL,
    INPUT_HTTP_STATUS,
    INPUT_HTTPS_SSL_PROFILE,
    INPUT_SSH_IPV4_ACL,
    INPUT_SSH_IPV6_ACL,
    INPUT_SSH_STATUS,
    INPUT_TELNET_STATUS,
)


@pytest.mark.parametrize("test_data", INPUT_SSH_STATUS, ids=generate_test_ids_list(INPUT_SSH_STATUS))
def test_VerifySSHStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySSHStatus."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySSHStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SSH_IPV4_ACL, ids=generate_test_ids_list(INPUT_SSH_IPV4_ACL))
def test_VerifySSHIPv4Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySSHIPv4Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySSHIPv4Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SSH_IPV6_ACL, ids=generate_test_ids_list(INPUT_SSH_IPV6_ACL))
def test_VerifySSHIPv6Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySSHIPv6Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySSHIPv6Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_TELNET_STATUS, ids=generate_test_ids_list(INPUT_TELNET_STATUS))
def test_VerifyTelnetStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTelnetStatus."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTelnetStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_HTTP_STATUS, ids=generate_test_ids_list(INPUT_HTTP_STATUS))
def test_VerifyAPIHttpStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAPIHttpStatus."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAPIHttpStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_HTTPS_SSL_PROFILE, ids=generate_test_ids_list(INPUT_HTTPS_SSL_PROFILE))
def test_VerifyAPIHttpsSSL(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAPIHttpsSSL"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAPIHttpsSSL(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(profile=test_data["side_effect"]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_API_IPV4_ACL, ids=generate_test_ids_list(INPUT_API_IPV4_ACL))
def test_VerifyAPIIPv4Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAPIIPv4Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAPIIPv4Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_API_IPV6_ACL, ids=generate_test_ids_list(INPUT_API_IPV6_ACL))
def test_VerifyAPIIPv6Acl(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAPIIPv6Acl"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAPIIPv6Acl(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
