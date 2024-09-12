# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures for benchmarking ANTA."""

import logging

import pytest
import respx
from _pytest.terminal import TerminalReporter

from anta.catalog import AntaCatalog
from anta.device import AsyncEOSDevice
from anta.inventory import AntaInventory

from .utils import AntaMockEnvironment

logger = logging.getLogger(__name__)

TEST_CASE_COUNT = None


@pytest.fixture(scope="session")
def catalog() -> AntaCatalog:
    """Fixture that generate an ANTA catalog from unit test data. Also configure respx to mock eAPI responses."""
    global TEST_CASE_COUNT  # noqa: PLW0603  pylint: disable=global-statement
    eapi_route = respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"})
    env = AntaMockEnvironment()
    TEST_CASE_COUNT = len(env.catalog.tests)
    eapi_route.side_effect = env.eapi_response
    return env.catalog


@pytest.fixture
def inventory(request: pytest.FixtureRequest) -> AntaInventory:
    """Generate an ANTA inventory."""
    inv = AntaInventory()
    for i in range(request.param["count"]):
        inv.add_device(
            AsyncEOSDevice(
                host=f"device-{i}.avd.arista.com",
                username="admin",
                password="admin",  # noqa: S106
                name=f"device-{i}",
                disable_cache=(not request.param["cache"]),
            )
        )
    return inv


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    """Display the total number of ANTA unit test cases used to benchmark."""
    terminalreporter.write_sep("=", f"{TEST_CASE_COUNT} ANTA test cases")
