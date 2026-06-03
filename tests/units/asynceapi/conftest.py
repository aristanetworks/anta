# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures for the asynceapi client package."""

import pytest

from asynceapi import Device
from asynceapi._auth import EapiSessionAuth

_TEST_HOST = "192.0.2.1"
_TEST_USERNAME = "admin"
_TEST_SECRET = "test1234"
_TEST_LOGIN_URL = f"https://{_TEST_HOST}:443/login"


@pytest.fixture
def asynceapi_device() -> Device:
    """Return an asynceapi Device instance."""
    return Device(
        host="localhost",
        username="admin",
        password="admin",
        proto="https",
        port=443,
    )


@pytest.fixture
def session_auth() -> EapiSessionAuth:
    """Return a fresh EapiSessionAuth with known credentials."""
    return EapiSessionAuth(username=_TEST_USERNAME, password=_TEST_SECRET, login_url=_TEST_LOGIN_URL, host=_TEST_HOST)
