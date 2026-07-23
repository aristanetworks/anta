# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import respx

if TYPE_CHECKING:
    from collections.abc import Iterator

from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory

DATA_DIR: Path = Path(__file__).parent.resolve() / "data"


@pytest.fixture
def httpx2_mock(request: pytest.FixtureRequest) -> Iterator[respx.Router]:
    """Override pytest-httpx2 fixture to default assert_all_called=False, matching the previous respx.mock behavior."""
    options: dict[str, Any] = {}
    if (marker := request.node.get_closest_marker("httpx2")) is not None:
        options.update(marker.kwargs)
    options.setdefault("using", "httpcore2")
    options.setdefault("assert_all_called", False)
    with respx.mock(**options) as router:  # pyright: ignore reportGeneralTypeIssues
        yield router


# pylint: disable=redefined-outer-name
@pytest.fixture
def inventory(request: pytest.FixtureRequest, httpx2_mock: respx.Router) -> AntaInventory:
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
        # Mock eAPI endpoints to make all devices reachable
        httpx2_mock.head(path="/command-api")
        httpx2_mock.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show version").respond(
            json={
                "result": [
                    {
                        "modelName": "pytest",
                    }
                ],
            }
        )
    else:
        httpx2_mock.head(path="/command-api").respond(status_code=401)
    return inv
