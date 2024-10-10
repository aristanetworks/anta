# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures for benchmarking ANTA."""

import logging

import pytest
import respx
from _pytest.terminal import TerminalReporter

from anta.catalog import AntaCatalog

from .utils import AntaMockEnvironment

logger = logging.getLogger(__name__)

TEST_CASE_COUNT = None


@pytest.fixture(name="anta_mock_env", scope="session")  # We want this fixture to have a scope set to session to avoid reparsing all the unit tests data.
def anta_mock_env_fixture() -> AntaMockEnvironment:
    """Return an AntaMockEnvironment for this test session. Also configure respx to mock eAPI responses."""
    global TEST_CASE_COUNT  # noqa: PLW0603
    eapi_route = respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"})
    env = AntaMockEnvironment()
    TEST_CASE_COUNT = env.tests_count
    eapi_route.side_effect = env.eapi_response
    return env


@pytest.fixture  # This fixture should have a scope set to function as the indexing result is stored in this object
def catalog(anta_mock_env: AntaMockEnvironment) -> AntaCatalog:
    """Fixture that return an ANTA catalog from the AntaMockEnvironment of this test session."""
    return anta_mock_env.catalog


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    """Display the total number of ANTA unit test cases used to benchmark."""
    terminalreporter.write_sep("=", f"{TEST_CASE_COUNT} ANTA test cases")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize inventory for benchmark tests."""
    if "inventory" in metafunc.fixturenames:
        for marker in metafunc.definition.iter_markers(name="parametrize"):
            if "inventory" in marker.args[0]:
                # Do not override test function parametrize marker for inventory arg
                return
        metafunc.parametrize(
            "inventory",
            [
                pytest.param({"count": 1, "disable_cache": True, "reachable": True}, id="1-device"),
                pytest.param({"count": 2, "disable_cache": True, "reachable": True}, id="2-devices"),
            ],
            indirect=True,
        )
