# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi._transports module."""

from aiohttp import ClientSession, TCPConnector

from asynceapi import Device
from asynceapi._transports import build_aiohttp_transport


async def test_build_aiohttp_transport() -> None:
    """Test build_aiohttp_transport."""
    transport = await build_aiohttp_transport()
    assert transport
    assert hasattr(transport, "client")
    assert isinstance(transport.client, ClientSession)
    assert hasattr(transport.client, "connector")
    assert isinstance(transport.client.connector, TCPConnector)


async def test_device_with_aiohttp_transport() -> None:
    """Test instantiating a Device with an aiohttp transport."""
    transport = await build_aiohttp_transport()
    device = Device(transport=transport)
    assert device
    assert device._transport == transport
