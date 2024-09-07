# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Patched objects for the ANTA benchmark tests."""

from anta.device import AsyncEOSDevice


async def mock_refresh(self: AsyncEOSDevice) -> None:
    """Mock the refresh method for the AsyncEOSDevice object."""
    self.hw_model = "cEOSLab"
    self.established = True
    self.is_online = True
