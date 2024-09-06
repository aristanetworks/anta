# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Utils for the ANTA benchmark tests."""

import json
import uuid
from typing import Any

import httpx
from pydantic import ValidationError

from anta.catalog import AntaCatalog, AntaTestDefinition
from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.models import AntaTest

EOS_DATA: dict[str, list[Any]] = {}


def generate_response(request: httpx.Request) -> httpx.Response:
    """Generate a response for the eAPI request."""
    jsonrpc = json.loads(request.content)
    req_id = jsonrpc["id"]
    ofmt = jsonrpc["params"]["format"]

    # Extract the test name, UUID, and command index from the request ID
    test_name, test_uuid, idx = parse_req_id(req_id)
    command_index = int(idx)

    # This should never happen, but better be safe than sorry
    if test_uuid not in EOS_DATA:
        msg = f"Error while generating a mock response for test {test_name}: test ID not found in the EOS data."
        raise RuntimeError(msg)

    eos_data = EOS_DATA[test_uuid]

    # This could happen if the unit test data is not correctly defined
    if command_index >= len(eos_data):
        msg = f"Error while generating a mock response for test {test_name}: more commands than provided in the EOS data."
        raise RuntimeError(msg)

    result = {"output": eos_data[command_index]} if ofmt == "text" else eos_data[command_index]

    return httpx.Response(
        status_code=200,
        json={
            "jsonrpc": "2.0",
            "id": req_id,
            "result": [result],
        },
    )


def generate_catalog(data: list[dict[str, Any]], multiplier: int = 1) -> AntaCatalog:
    """Generate an ANTA catalog from the unit tests data."""
    test_definitions = []
    for test_data in data:
        for _ in range(multiplier):
            # Using a UUID to ensure each test is unique and run even if the same test is repeated
            test_uuid = str(uuid.uuid4())
            EOS_DATA[test_uuid] = test_data["eos_data"]
            result_overwrite = AntaTest.Input.ResultOverwrite(custom_field=test_uuid)

            test = test_data["test"]
            # Some unit tests purposely have invalid inputs, we just skip them
            try:
                if test_data["inputs"] is None:
                    inputs = test.Input(result_overwrite=result_overwrite)
                else:
                    inputs = test.Input(**test_data["inputs"], result_overwrite=result_overwrite)
            except ValidationError:
                continue

            test_definition = AntaTestDefinition(
                test=test,
                inputs=inputs,
            )
            test_definitions.append(test_definition)

    return AntaCatalog(tests=test_definitions)


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


def parse_req_id(req_id: str) -> tuple[str, ...]:
    """Parse the patched request ID from the eAPI request."""
    expected_parts = 3
    parts = req_id.split(":", 2)

    if len(parts) != expected_parts:
        msg = f"Invalid request ID format: {req_id}"
        raise ValueError(msg)

    return tuple(parts)
