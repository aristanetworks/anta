"""
Tests for anta.tests.aaa.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.aaa import (
    VerifyAcctConsoleMethods,
    VerifyAcctDefaultMethods,
    VerifyAuthenMethods,
    VerifyAuthzMethods,
    VerifyTacacsServerGroups,
    VerifyTacacsServers,
    VerifyTacacsSourceIntf,
)
from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_ACCT_CONSOLE_METHODS,
    INPUT_ACCT_DEFAULT_METHODS,
    INPUT_AUTHEN_METHODS,
    INPUT_AUTHZ_METHODS,
    INPUT_TACACS_SERVER_GROUPS,
    INPUT_TACACS_SERVERS,
    INPUT_TACACS_SRC_INTF,
)


@pytest.mark.parametrize("test_data", INPUT_TACACS_SRC_INTF, ids=generate_test_ids_list(INPUT_TACACS_SRC_INTF))
def test_VerifyTacacsSourceIntf(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTacacsSourceIntf"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTacacsSourceIntf(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(intf=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_TACACS_SERVERS, ids=generate_test_ids_list(INPUT_TACACS_SERVERS))
def test_VerifyTacacsServers(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTacacsServers"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTacacsServers(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(servers=test_data["side_effect"][0], vrf=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_TACACS_SERVER_GROUPS, ids=generate_test_ids_list(INPUT_TACACS_SERVER_GROUPS))
def test_VerifyTacacsServerGroups(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTacacsServerGroups"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTacacsServerGroups(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(groups=test_data["side_effect"]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_AUTHEN_METHODS, ids=generate_test_ids_list(INPUT_AUTHEN_METHODS))
def test_VerifyAuthenMethods(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAuthenMethods"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAuthenMethods(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(methods=test_data["side_effect"][0], auth_types=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_AUTHZ_METHODS, ids=generate_test_ids_list(INPUT_AUTHZ_METHODS))
def test_VerifyAuthzMethods(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAuthzMethods"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAuthzMethods(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(methods=test_data["side_effect"][0], auth_types=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_ACCT_DEFAULT_METHODS, ids=generate_test_ids_list(INPUT_ACCT_DEFAULT_METHODS))
def test_VerifyAcctDefaultMethods(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAcctDefaultMethods"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAcctDefaultMethods(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(methods=test_data["side_effect"][0], auth_types=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_ACCT_CONSOLE_METHODS, ids=generate_test_ids_list(INPUT_ACCT_CONSOLE_METHODS))
def test_VerifyAcctConsoleMethods(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyAcctConsoleMethods"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyAcctConsoleMethods(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(methods=test_data["side_effect"][0], auth_types=test_data["side_effect"][1]))

    logging.info(f"Test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
