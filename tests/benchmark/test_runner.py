# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark ANTA runner."""

from typing import Literal
from unittest.mock import patch

import pytest
import respx

from anta.device import AsyncEOSDevice
from anta.result_manager import ResultManager
from anta.runner import main as anta_runner

from .patched_objects import mock_refresh
from .utils import generate_inventory, generate_response, get_catalog


# Parametrize the test to run with different inventory sizes, and test multipliers if needed
@pytest.mark.asyncio
@pytest.mark.respx(assert_all_mocked=True, assert_all_called=True)
@pytest.mark.parametrize(
    ("inventory_size", "catalog_size"),
    [
        (10, "small"),
        (10, "medium"),
        (10, "large"),
    ],
    ids=["small_run", "medium_run", "large_run"],
)
async def test_runner(respx_mock: respx.MockRouter, inventory_size: int, catalog_size: Literal["small", "medium", "large"]) -> None:
    """Test the ANTA runner."""
    # We mock all POST requests to eAPI
    route = respx_mock.route(path="/command-api", method="POST")

    # We also mock all responses using data from the unit tests
    route.side_effect = generate_response

    # Create the required ANTA objects
    inventory = generate_inventory(inventory_size)
    catalog = get_catalog(catalog_size)
    manager = ResultManager()

    # Apply the patches for the run
    with patch.object(AsyncEOSDevice, "refresh", mock_refresh):
        # Run ANTA
        await anta_runner(manager, inventory, catalog)

    # NOTE: See if we want to generate a report and benchmark

    assert respx_mock.calls.called
