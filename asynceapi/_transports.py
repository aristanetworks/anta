# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Transports used for the asynceapi package."""

from __future__ import annotations

from aiohttp import ClientSession, TCPConnector
from httpx_aiohttp import AiohttpTransport


async def build_aiohttp_transport(*, verify_ssl: bool = True) -> AiohttpTransport:
    """Build a custom `httpx` transport using the `aiohttp` library. Can be used with the `asynceapi.Device` client."""
    aiohttp_client = ClientSession(connector=TCPConnector(ssl=verify_ssl))
    return AiohttpTransport(aiohttp_client)
