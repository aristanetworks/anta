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

from .utils import AntaMockEnvironment, build_inventory, collect, collect_commands

logger = logging.getLogger(__name__)


def test_anta_dry_run(
    benchmark: BenchmarkFixture,
    anta_mock_env: AntaMockEnvironment,
    inventory: AntaInventory,
) -> None:
    """Benchmark ANTA in Dry-Run Mode."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    # TODO: Use AntaRunner directly in ANTA v2.0.0
    def setup() -> tuple[tuple[ResultManager, AntaInventory, AntaCatalog], dict[str, object]]:
        """Create state that is not shared between CodSpeed's warm-up and measured invocations."""
        return (ResultManager(), build_inventory(len(inventory)), anta_mock_env.catalog), {}

    def run(results: ResultManager, benchmark_inventory: AntaInventory, catalog: AntaCatalog) -> ResultManager:
        """Run ANTA in dry-run mode and return the populated results."""
        asyncio.run(main(results, benchmark_inventory, catalog, dry_run=True))
        return results

    def teardown(_results: ResultManager, benchmark_inventory: AntaInventory, _catalog: AntaCatalog) -> None:
        """Release resources after each warm-up or measured invocation."""
        asyncio.run(benchmark_inventory.disconnect_inventory())

    results = benchmark.pedantic(run, setup=setup, teardown=teardown, rounds=1)

    logging.disable(logging.NOTSET)

    if len(results.results) != len(inventory) * anta_mock_env.tests_count:
        pytest.fail(f"Expected {len(inventory) * anta_mock_env.tests_count} tests but got {len(results.results)}", pytrace=False)
    bench_info = f"\n--- ANTA NRFU Dry-Run Benchmark Information ---\nTest count: {len(results.results)}\n-----------------------------------------------"
    logger.info(bench_info)


@patch("anta.models.AntaTest.collect", collect)
@patch("anta.device.AntaDevice.collect_commands", collect_commands)
@pytest.mark.dependency(name="anta_benchmark", scope="package")
@respx.mock  # Mock eAPI responses
def test_anta(
    benchmark: BenchmarkFixture,
    anta_mock_env: AntaMockEnvironment,
    inventory: AntaInventory,
    request: pytest.FixtureRequest,
    session_results: defaultdict[str, ResultManager],
) -> None:
    """Benchmark ANTA."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    # TODO: Use AntaRunner directly in ANTA v2.0.0
    def setup() -> tuple[tuple[ResultManager, AntaInventory, AntaCatalog], dict[str, object]]:
        """Create state that is not shared between CodSpeed's warm-up and measured invocations."""
        return (ResultManager(), build_inventory(len(inventory)), anta_mock_env.catalog), {}

    def run(results: ResultManager, benchmark_inventory: AntaInventory, catalog: AntaCatalog) -> ResultManager:
        """Run ANTA and return the populated results."""
        asyncio.run(main(results, benchmark_inventory, catalog))
        return results

    def teardown(_results: ResultManager, benchmark_inventory: AntaInventory, _catalog: AntaCatalog) -> None:
        """Release resources after each warm-up or measured invocation."""
        asyncio.run(benchmark_inventory.disconnect_inventory())

    results = benchmark.pedantic(run, setup=setup, teardown=teardown, rounds=1)
    session_results[request.node.callspec.id] = results

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
