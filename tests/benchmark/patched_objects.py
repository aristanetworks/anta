# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Patched objects for the ANTA benchmark tests."""

import asyncio

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand, AntaTest


async def mock_refresh(self: AsyncEOSDevice) -> None:
    """Mock the refresh method for the AsyncEOSDevice object."""
    self.hw_model = "cEOSLab"
    self.established = True
    self.is_online = True


async def patched_collect(self: AntaTest) -> None:
    """Patched collect method for the AntaTest objects.

    When generating the catalog, we inject a UUID in the custom_field input to ensure each test is unique and keep track of the EOS data.
    """
    if self.inputs.result_overwrite is None or self.inputs.result_overwrite.custom_field is None:
        msg = "The custom_field input is required for the ANTA benchmark tests."
        raise RuntimeError(msg)
    await self.device.collect_commands(self.instance_commands, collection_id=f"{self.name}:{self.inputs.result_overwrite.custom_field}")


async def patched_collect_commands(self: AntaDevice, commands: list[AntaCommand], collection_id: str) -> None:
    """Patched collect_commands method for the AntaDevice object.

    Same principle here, adding each command index to the collection ID to keep track of the EOS data.
    """
    await asyncio.gather(*(self.collect(command=command, collection_id=f"{collection_id}:{idx}") for idx, command in enumerate(commands)))
