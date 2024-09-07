# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils for the ANTA benchmark tests."""

import json

import httpx

from anta.catalog import AntaCatalog
from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory

from .data import CATALOGS, OUTPUTS


def get_catalog(size: str) -> AntaCatalog:
    """Return the catalog for the given size."""
    return CATALOGS[size]


def generate_response(request: httpx.Request) -> httpx.Response:
    """Generate a response for the eAPI request."""
    jsonrpc = json.loads(request.content)
    req_id = jsonrpc["id"]
    ofmt = jsonrpc["params"]["format"]

    # Extract the test name from the request ID
    test_name = req_id.split("-")[1]

    # This should never happen, but better be safe than sorry
    if test_name not in OUTPUTS:
        msg = f"Error while generating a mock response for test {test_name}: test not found in unit tests data."
        raise RuntimeError(msg)

    output = OUTPUTS[test_name]

    result = {"output": output} if ofmt == "text" else output

    return httpx.Response(
        status_code=200,
        json={
            "jsonrpc": "2.0",
            "id": req_id,
            "result": [result],
        },
    )


def generate_inventory(size: int = 10) -> AntaInventory:
    """Generate an ANTA inventory with fake devices."""
    inventory = AntaInventory()
    for i in range(size):
        inventory.add_device(
            AsyncEOSDevice(
                host=f"device-{i}.example.com",
                username="admin",
                password="admin",  # noqa: S106
                name=f"device-{i}",
                enable_password="admin",  # noqa: S106
                enable=True,
                disable_cache=True,
            )
        )

    return inventory
