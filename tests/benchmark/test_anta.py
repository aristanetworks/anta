# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for ANTA."""

import asyncio
import logging
from collections import defaultdict
from unittest.mock import patch

import pytest
import respx
from pytest_codspeed import BenchmarkFixture

from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.runner import main

from .utils import AntaMockEnvironment, collect, collect_commands

logger = logging.getLogger(__name__)


def test_anta_dry_run(
    benchmark: BenchmarkFixture,
    catalog: AntaCatalog,
    inventory: AntaInventory,
    request: pytest.FixtureRequest,
    session_results: defaultdict[str, ResultManager],
) -> None:
    """Benchmark ANTA in Dry-Run Mode."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    results = session_results[request.node.callspec.id]

    # TODO: Use AntaRunner directly in ANTA v2.0.0
    @benchmark
    def _() -> None:
        results.reset()
        catalog.clear_indexes()
        asyncio.run(main(results, inventory, catalog, dry_run=True))

    logging.disable(logging.NOTSET)

    if len(results.results) != len(inventory) * len(catalog.tests):
        pytest.fail(f"Expected {len(inventory) * len(catalog.tests)} tests but got {len(results.results)}", pytrace=False)
    bench_info = f"\n--- ANTA NRFU Dry-Run Benchmark Information ---\nTest count: {len(results.results)}\n-----------------------------------------------"
    logger.info(bench_info)


@patch("anta.models.AntaTest.collect", collect)
@patch("anta.device.AntaDevice.collect_commands", collect_commands)
@pytest.mark.dependency(name="anta_benchmark", scope="package")
def test_anta(
    benchmark: BenchmarkFixture,
    catalog: AntaCatalog,
    inventory: AntaInventory,
    request: pytest.FixtureRequest,
    session_results: defaultdict[str, ResultManager],
    anta_mock_env: AntaMockEnvironment,
    httpx2_mock: respx.Router,
) -> None:
    """Benchmark ANTA."""
    # Clear routes from the inventory fixture and set up the benchmark-specific eAPI mock.
    # The eapi_response side_effect handles all commands including 'show version'.
    httpx2_mock.clear()
    httpx2_mock.head(path="/command-api")
    httpx2_mock.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}).side_effect = anta_mock_env.eapi_response

    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    results = session_results[request.node.callspec.id]

    # TODO: Use AntaRunner directly in ANTA v2.0.0
    @benchmark
    def _() -> None:
        results.reset()
        catalog.clear_indexes()
        asyncio.run(main(results, inventory, catalog))

    logging.disable(logging.NOTSET)

    bench_info = (
        "\n--- ANTA NRFU Benchmark Information ---\n"
        f"Test results: {len(results.results)}\n"
        f"Success: {results.get_total_results({AntaTestStatus.SUCCESS})}\n"
        f"Failure: {results.get_total_results({AntaTestStatus.FAILURE})}\n"
        f"Skipped: {results.get_total_results({AntaTestStatus.SKIPPED})}\n"
        f"Error: {results.get_total_results({AntaTestStatus.ERROR})}\n"
        f"Unset: {results.get_total_results({AntaTestStatus.UNSET})}\n"
        "---------------------------------------"
    )
    logger.info(bench_info)
    assert results.get_total_results({AntaTestStatus.ERROR}) == 0
    assert results.get_total_results({AntaTestStatus.UNSET}) == 0
