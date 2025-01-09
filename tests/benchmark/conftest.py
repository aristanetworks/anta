# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixtures for benchmarking ANTA."""

import logging
from collections import defaultdict

import pytest
import respx
from _pytest.terminal import TerminalReporter

from anta.catalog import AntaCatalog
from anta.result_manager import ResultManager

from .utils import AntaMockEnvironment

logger = logging.getLogger(__name__)

TEST_CASE_COUNT = None

# Used to globally configure the benchmarks by specifying parameters for inventories
BENCHMARK_PARAMETERS = [
    pytest.param({"count": 1, "disable_cache": True, "reachable": True}, id="1-device"),
    pytest.param({"count": 2, "disable_cache": True, "reachable": True}, id="2-devices"),
]


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


@pytest.fixture(name="session_results", scope="session")  # We want this fixture to be reused across test modules within tests/benchmark
def session_results_fixture() -> defaultdict[str, ResultManager]:
    """Return a dictionary of ResultManger objects for the benchmarks.

    The key is the test id as defined in the pytest_generate_tests in this module.
    Used to pass a populated ResultManager from one benchmark to another.
    """
    return defaultdict(lambda: ResultManager())


@pytest.fixture
def results(request: pytest.FixtureRequest, session_results: defaultdict[str, ResultManager]) -> ResultManager:
    """Return the unique ResultManger object for the current benchmark parameter."""
    return session_results[request.node.callspec.id]


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
            BENCHMARK_PARAMETERS,
            indirect=True,
        )
    elif "results" in metafunc.fixturenames:
        metafunc.parametrize(
            "results",
            BENCHMARK_PARAMETERS,
            indirect=True,
        )
