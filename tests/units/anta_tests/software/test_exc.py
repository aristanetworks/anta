# -*- coding: utf-8 -*-

"""
Tests for anta.tests.software.py
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from anta.tests.software import VerifyEOSExtensions, VerifyEOSVersion, VerifyTerminAttrVersion
from tests.lib.utils import generate_test_ids_list

from .data import INPUT_VERIFY_EOS_EXTENSIONS, INPUT_VERIFY_EOS_VERSION, INPUT_VERIFY_TERMINATTR_VERSION


@pytest.mark.parametrize("test_data", INPUT_VERIFY_EOS_VERSION, ids=generate_test_ids_list(INPUT_VERIFY_EOS_VERSION))
def test_VerifyEOSVersion(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyEOSVersion."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyEOSVersion(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(versions=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_VERIFY_TERMINATTR_VERSION, ids=generate_test_ids_list(INPUT_VERIFY_TERMINATTR_VERSION))
def test_VerifyTerminAttrVersion(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyTerminAttrVersion."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyTerminAttrVersion(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test(versions=test_data["side_effect"]))

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]


@pytest.mark.parametrize("test_data", INPUT_VERIFY_EOS_EXTENSIONS, ids=generate_test_ids_list(INPUT_VERIFY_EOS_EXTENSIONS))
def test_VerifyEOSExtensions(mocked_device: MagicMock, test_data: Any) -> None:
    """Check VerifyEOSExtensions."""

    logging.info(f"Mocked device is: {mocked_device.host}")
    logging.info(f"Mocked HW is: {mocked_device.hw_model}")

    test = VerifyEOSExtensions(mocked_device, eos_data=test_data["eos_data"])
    asyncio.run(test.test())

    logging.info(f"test result is: {test.result}")

    assert str(test.result.name) == mocked_device.name
    assert test.result.result == test_data["expected_result"]
    assert test.result.messages == test_data["expected_messages"]
