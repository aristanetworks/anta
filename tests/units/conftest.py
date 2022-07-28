"""
conftest.py

used to store anta specific fixtures used for tests
"""
import functools
from unittest.mock import create_autospec, MagicMock
import pytest
from anta.inventory.models import InventoryDevice


@pytest.fixture
def mocked_device() -> MagicMock:
    """
    Returns a mocked device with initiazlied fields
    """
    mock = create_autospec(InventoryDevice)
    mock.host = "42.42.42.42"
    mock.username = "toto"
    mock.password = "mysuperdupersecret"
    mock.enable_password = "mysuperduperenablesecret"
    mock.session = MagicMock()
    mock.is_online = True
    mock.established = True
    mock.hw_model = "unset"
    mock.url = "https://42.42.42.42:666"

    # keeping the original assert_enable_password_is_not_none() method
    mock.assert_enable_password_is_not_none = functools.partial(
        InventoryDevice.assert_enable_password_is_not_none, mock
    )
    return mock
