# -*- coding: utf-8 -*-

"""Fixture for Anta Testing"""

import functools
from unittest.mock import MagicMock, create_autospec

import pytest
from aioeapi import Device

from anta.inventory.models import InventoryDevice


@pytest.fixture
def mocked_device(hw_model: str = "unknown_hw") -> MagicMock:
    """
    Returns a mocked device with initiazlied fields
    """

    mock = create_autospec(InventoryDevice)
    mock.host = "42.42.42.42"
    mock.name = "testdevice"
    mock.username = "toto"
    mock.password = "mysuperdupersecret"
    mock.enable_password = "mysuperduperenablesecret"
    mock.session = create_autospec(Device)
    mock.is_online = True
    mock.established = True
    mock.hw_model = hw_model

    # keeping the original assert_enable_password_is_not_none() method
    mock.assert_enable_password_is_not_none = functools.partial(InventoryDevice.assert_enable_password_is_not_none, mock)
    return mock
