# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.routing.bgp.py
"""
from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests.lib.utils import generate_test_ids_list


# Patching the decorator
# Thanks - https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc
def mock_decorator(*args, **kwargs):  # type: ignore
    """Decorate by doing nothing."""
    # pylint: disable=W0613

    def decorator(f):  # type: ignore
        @wraps(f)
        def decorated_function(*args, **kwargs):  # type: ignore
            return f(*args, **kwargs)

        return decorated_function

    return decorator


patch("anta.decorators.check_bgp_family_enable", mock_decorator).start()

# pylint: disable=C0413
# because of the patch above
from anta.tests.routing.bgp import (  # noqa: E402
    VerifyBGPEVPNCount,
    VerifyBGPEVPNState,
    VerifyBGPIPv4UnicastCount,
    VerifyBGPIPv4UnicastState,
    VerifyBGPIPv6UnicastState,
    VerifyBGPRTCCount,
    VerifyBGPRTCState,
)

from .data import (  # noqa: E402
    INPUT_BGP_EVPN_COUNT,
    INPUT_BGP_EVPN_STATE,
    INPUT_BGP_IPV4_UNICAST_COUNT,
    INPUT_BGP_IPV4_UNICAST_STATE,
    INPUT_BGP_IPV6_UNICAST_STATE,
    INPUT_BGP_RTC_COUNT,
    INPUT_BGP_RTC_STATE,
)

# pylint: enable=C0413


@pytest.mark.parametrize("test_data", INPUT_BGP_IPV4_UNICAST_STATE, ids=generate_test_ids_list(INPUT_BGP_IPV4_UNICAST_STATE))
def test_VerifyBGPIPv4UnicastState(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPIPv4UnicastState."""

    test = VerifyBGPIPv4UnicastState(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_IPV4_UNICAST_COUNT, ids=generate_test_ids_list(INPUT_BGP_IPV4_UNICAST_COUNT))
def test_VerifyBGPIPv4UnicastCount(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPIPv4UnicastCount."""

    test = VerifyBGPIPv4UnicastCount(
        mocked_device,
        inputs=test_data["inputs"],
        eos_data=test_data["eos_data"],
    )
    asyncio.run(test.test())

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_IPV6_UNICAST_STATE, ids=generate_test_ids_list(INPUT_BGP_IPV6_UNICAST_STATE))
def test_VerifyBGPIPv6UnicastState(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPIPv6UnicastState."""

    test = VerifyBGPIPv6UnicastState(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_EVPN_STATE, ids=generate_test_ids_list(INPUT_BGP_EVPN_STATE))
def test_VerifyBGPEVPNState(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPEVPNState."""

    test = VerifyBGPEVPNState(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_EVPN_COUNT, ids=generate_test_ids_list(INPUT_BGP_EVPN_COUNT))
def test_VerifyBGPEVPNCount(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPEVPNCount."""

    test = VerifyBGPEVPNCount(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"]["number"]))

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_RTC_STATE, ids=generate_test_ids_list(INPUT_BGP_RTC_STATE))
def test_VerifyBGPRTCState(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPRTCState."""

    test = VerifyBGPRTCState(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_BGP_RTC_COUNT, ids=generate_test_ids_list(INPUT_BGP_RTC_COUNT))
def test_VerifyBGPRTCCount(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyBGPRTCCount."""

    test = VerifyBGPRTCCount(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(number=test_data["side_effect"]["number"]))

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
