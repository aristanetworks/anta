# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from collections.abc import Iterator
from pathlib import Path

import pytest
import respx

from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory

DATA_DIR: Path = Path(__file__).parent.resolve() / "data"


@pytest.fixture
def inventory(request: pytest.FixtureRequest) -> Iterator[AntaInventory]:
    """Generate an ANTA inventory."""
    user = "admin"
    password = "password"  # noqa: S105
    params = request.param if hasattr(request, "param") else {}
    count = params.get("count", 1)
    disable_cache = params.get("disable_cache", True)
    reachable = params.get("reachable", True)
    if "filename" in params:
        inv = AntaInventory.parse(DATA_DIR / params["filename"], username=user, password=password, disable_cache=disable_cache)
    else:
        inv = AntaInventory()
        for i in range(count):
            inv.add_device(
                AsyncEOSDevice(
                    host=f"device-{i}.anta.arista.com",
                    username=user,
                    password=password,
                    name=f"device-{i}",
                    disable_cache=disable_cache,
                )
            )
    if reachable:
        # This context manager makes all devices reachable
        with respx.mock:
            respx.head(path="/command-api")
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
    else:
        with respx.mock:
            respx.head(path="/command-api").respond(status_code=401)
            yield inv
