# Copyright (c) 2023-2025 Arista Networks, Inc.
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

from .utils import collect, collect_commands

logger = logging.getLogger(__name__)


def test_anta_dry_run(
    benchmark: BenchmarkFixture,
    event_loop: asyncio.AbstractEventLoop,
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
        event_loop.run_until_complete(main(results, inventory, catalog, dry_run=True))

    logging.disable(logging.NOTSET)

    if len(results.results) != len(inventory) * len(catalog.tests):
        pytest.fail(f"Expected {len(inventory) * len(catalog.tests)} tests but got {len(results.results)}", pytrace=False)
    bench_info = f"\n--- ANTA NRFU Dry-Run Benchmark Information ---\nTest count: {len(results.results)}\n-----------------------------------------------"
    logger.info(bench_info)


@patch("anta.models.AntaTest.collect", collect)
@patch("anta.device.AntaDevice.collect_commands", collect_commands)
@pytest.mark.dependency(name="anta_benchmark", scope="package")
@respx.mock  # Mock eAPI responses
def test_anta(
    benchmark: BenchmarkFixture,
    event_loop: asyncio.AbstractEventLoop,
    catalog: AntaCatalog,
    inventory: AntaInventory,
    request: pytest.FixtureRequest,
    session_results: defaultdict[str, ResultManager],
) -> None:
    """Benchmark ANTA."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    results = session_results[request.node.callspec.id]

    # TODO: Use AntaRunner directly in ANTA v2.0.0
    @benchmark
    def _() -> None:
        results.reset()
        catalog.clear_indexes()
        event_loop.run_until_complete(main(results, inventory, catalog))

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
