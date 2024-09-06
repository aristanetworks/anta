# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark ANTA runner."""

from unittest.mock import patch

import pytest
import respx

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaTest
from anta.result_manager import ResultManager
from anta.runner import main as anta_runner

from .data import ALL_DATA
from .patched_objects import mock_refresh, patched_collect, patched_collect_commands
from .utils import generate_catalog, generate_inventory, generate_response


# Parametrize the test to run with different inventory sizes, and test multipliers if needed
@pytest.mark.asyncio
@pytest.mark.respx(assert_all_mocked=True, assert_all_called=True)
@pytest.mark.parametrize(
    ("inventory_size", "test_multiplier"),
    [
        (10, 1),
        (20, 1),
        (30, 1),
    ],
    ids=["small_run", "medium_run", "large_run"],
)
async def test_runner(respx_mock: respx.MockRouter, inventory_size: int, test_multiplier: int) -> None:
    """Test the ANTA runner."""
    # We mock all POST requests to eAPI
    route = respx_mock.route(path="/command-api", method="POST")

    # We also mock all responses using data from the unit tests
    route.side_effect = generate_response

    # Create the required ANTA objects
    inventory = generate_inventory(inventory_size)
    catalog = generate_catalog(ALL_DATA, test_multiplier)
    manager = ResultManager()

    # Apply the patches for the run
    with (
        patch.object(AsyncEOSDevice, "refresh", mock_refresh),
        patch.object(AntaTest, "collect", patched_collect),
        patch.object(AntaDevice, "collect_commands", patched_collect_commands),
    ):
        # Run ANTA
        await anta_runner(manager, inventory, catalog)

    # NOTE: See if we want to generate a report and benchmark

    device_count = len(inventory.devices)
    test_count = len(catalog.tests)

    assert respx_mock.calls.called
    assert respx_mock.calls.call_count > device_count * test_count

    # No filtering in place, we should have results for all devices and tests
    assert len(manager.results) == len(inventory.devices) * len(catalog.tests)
