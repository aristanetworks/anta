# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures for the asynceapi client package."""

import pytest

from asynceapi import Device


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
