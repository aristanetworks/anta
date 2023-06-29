# -*- coding: utf-8 -*-

"""
Tests for anta.tests.hardware.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.interfaces import (
    VerifyIllegalLACP,
    VerifyInterfaceDiscards,
    VerifyInterfaceErrDisabled,
    VerifyInterfaceErrors,
    VerifyInterfacesStatus,
    VerifyInterfaceUtilization,
    VerifyIPProxyARP,
    VerifyL3MTU,
    VerifyLoopbackCount,
    VerifyPortChannels,
    VerifyStormControlDrops,
    VerifySVI,
)
from tests.lib.utils import generate_test_ids_list

from .data import (
    INPUT_ILLEGAL_LACP,
    INPUT_INTERFACE_DISCARDS,
    INPUT_INTERFACE_ERR_DISABLED,
    INPUT_INTERFACE_ERRORS,
    INPUT_INTERFACE_UTILIZATION,
    INPUT_INTERFACES_STATUS,
    INPUT_IP_PROXY_ARP,
    INPUT_L3MTU,
    INPUT_LOOPBACK_COUNT,
    INPUT_PORT_CHANNELS,
    INPUT_STORM_CONTROL_DROPS,
    INPUT_SVI,
)


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_UTILIZATION, ids=generate_test_ids_list(INPUT_INTERFACE_UTILIZATION))
def test_VerifyInterfaceUtilization(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceUtilization"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceUtilization(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_ERRORS, ids=generate_test_ids_list(INPUT_INTERFACE_ERRORS))
def test_VerifyInterfaceErrors(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceErrors"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceErrors(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_DISCARDS, ids=generate_test_ids_list(INPUT_INTERFACE_DISCARDS))
def test_VerifyInterfaceDiscards(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceDiscards"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceDiscards(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_INTERFACE_ERR_DISABLED, ids=generate_test_ids_list(INPUT_INTERFACE_ERR_DISABLED))
def test_VerifyInterfaceErrDisabled(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfaceErrDisabled"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfaceErrDisabled(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_INTERFACES_STATUS, ids=generate_test_ids_list(INPUT_INTERFACES_STATUS))
def test_VerifyInterfacesStatus(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyInterfacesStatus"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyInterfacesStatus(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(minimum=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_STORM_CONTROL_DROPS, ids=generate_test_ids_list(INPUT_STORM_CONTROL_DROPS))
def test_VerifyStormControlDrops(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyStormControlDrops"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyStormControlDrops(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_PORT_CHANNELS, ids=generate_test_ids_list(INPUT_PORT_CHANNELS))
def test_VerifyPortChannels(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyPortChannels"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyPortChannels(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_ILLEGAL_LACP, ids=generate_test_ids_list(INPUT_ILLEGAL_LACP))
def test_VerifyIllegalLACP(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyIllegalLACP"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyIllegalLACP(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_LOOPBACK_COUNT, ids=generate_test_ids_list(INPUT_LOOPBACK_COUNT))
def test_VerifyLoopbackCount(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyLoopbackCount"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyLoopbackCount(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_SVI, ids=generate_test_ids_list(INPUT_SVI))
def test_VerifySVI(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifySVI"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifySVI(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_L3MTU, ids=generate_test_ids_list(INPUT_L3MTU))
def test_VerifyL3MTU(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyL3MTU"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyL3MTU(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(mtu=test_data["side_effect"]["mtu"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_IP_PROXY_ARP, ids=generate_test_ids_list(INPUT_IP_PROXY_ARP))
def test_VerifyIPProxyARP(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyIPProxyARP"""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyIPProxyARP(mocked_device, eos_data=test_data["eos_data"], template_params=test_data["side_effect"]["template_params"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
