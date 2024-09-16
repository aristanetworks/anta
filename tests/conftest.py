# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

import asyncio
from collections.abc import Iterator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import respx

from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory


@pytest.fixture(params=[{"count": 1, "disable_cache": True}])
def inventory(request: pytest.FixtureRequest) -> Iterator[AntaInventory]:
    """Generate an ANTA inventory."""
    inv = AntaInventory()
    for i in range(request.param["count"]):
        inv.add_device(
            AsyncEOSDevice(
                host=f"device-{i}.anta.arista.com",
                username="admin",
                password="admin",  # noqa: S106
                name=f"device-{i}",
                disable_cache=request.param["disable_cache"],
            )
        )
    # This context manager makes all devices reachable
    with patch("asyncio.open_connection", AsyncMock(spec=asyncio.open_connection, return_value=(Mock(), Mock()))), respx.mock:
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show version").respond(
            json={
                "result": [
                    {
                        "modelName": "pytest",
                    }
                ],
            }
        )
        yield inv
