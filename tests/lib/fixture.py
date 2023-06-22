# -*- coding: utf-8 -*-

"""Fixture for Anta Testing"""

from unittest.mock import MagicMock, create_autospec

import pytest
from aioeapi import Device

from anta.inventory.models import AntaDevice


@pytest.fixture
def mocked_device(hw_model: str = "unknown_hw") -> MagicMock:
    """
    Returns a mocked device with initiazlied fields
    """

    mock = create_autospec(AntaDevice)
    mock.host = "42.42.42.42"
    mock.name = "testdevice"
    mock.username = "toto"
    mock.password = "mysuperdupersecret"
    mock.enable_password = "mysuperduperenablesecret"
    mock.session = create_autospec(Device)
    mock.is_online = True
    mock.established = True
    mock.hw_model = hw_model

    return mock
