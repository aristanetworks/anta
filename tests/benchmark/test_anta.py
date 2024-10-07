# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for ANTA."""

import asyncio
import logging
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


@pytest.mark.parametrize(
    "inventory",
    [
        pytest.param({"count": 1, "disable_cache": True, "reachable": False}, id="1 device"),
        pytest.param({"count": 2, "disable_cache": True, "reachable": False}, id="2 devices"),
    ],
    indirect=True,
)
def test_anta_dry_run(benchmark: BenchmarkFixture, event_loop: asyncio.AbstractEventLoop, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Test and benchmark ANTA in Dry-Run Mode."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    def bench() -> ResultManager:
        """Need to wrap the ANTA Runner to instantiate a new ResultManger for each benchmark run."""
        manager = ResultManager()
        catalog.clear_indexes()
        t = event_loop.create_task(main(manager, inventory, catalog, dry_run=True), name="benchmark-anta-dry-run")
        event_loop.run_until_complete(t)
        return manager

    manager = benchmark(bench)

    logging.disable(logging.NOTSET)
    if len(manager.results) != len(inventory) * len(catalog.tests):
        pytest.fail(f"Expected {len(inventory) * len(catalog.tests)} tests but got {len(manager.results)}", pytrace=False)
    bench_info = "\n--- ANTA NRFU Dry-Run Benchmark Information ---\n" f"Test count: {len(manager.results)}\n" "-----------------------------------------------"
    logger.info(bench_info)


@pytest.mark.parametrize(
    "inventory",
    [
        pytest.param({"count": 1, "disable_cache": True}, id="1 device"),
        pytest.param({"count": 2, "disable_cache": True}, id="2 devices"),
    ],
    indirect=True,
)
@patch("anta.models.AntaTest.collect", collect)
@patch("anta.device.AntaDevice.collect_commands", collect_commands)
@respx.mock  # Mock eAPI responses
def test_anta(benchmark: BenchmarkFixture, event_loop: asyncio.AbstractEventLoop, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Test and benchmark ANTA. Mock eAPI responses."""
    # Disable logging during ANTA execution to avoid having these function time in benchmarks
    logging.disable()

    def bench() -> ResultManager:
        """Need to wrap the ANTA Runner to instantiate a new ResultManger for each benchmark run."""
        manager = ResultManager()
        catalog.clear_indexes()
        event_loop.run_until_complete(main(manager, inventory, catalog))
        return manager

    manager = benchmark(bench)

    logging.disable(logging.NOTSET)

    if len(catalog.tests) * len(inventory) != len(manager.results):
        # This could mean duplicates exist.
        # TODO: consider removing this code and refactor unit test data as a dictionary with tuple keys instead of a list
        seen = set()
        dupes = []
        for test in catalog.tests:
            if test in seen:
                dupes.append(test)
            else:
                seen.add(test)
        if dupes:
            for test in dupes:
                msg = f"Found duplicate in test catalog: {test}"
                logger.error(msg)
        pytest.fail(f"Expected {len(catalog.tests) * len(inventory)} tests but got {len(manager.results)}", pytrace=False)
    bench_info = (
        "\n--- ANTA NRFU Benchmark Information ---\n"
        f"Test results: {len(manager.results)}\n"
        f"Success: {manager.get_total_results({AntaTestStatus.SUCCESS})}\n"
        f"Failure: {manager.get_total_results({AntaTestStatus.FAILURE})}\n"
        f"Skipped: {manager.get_total_results({AntaTestStatus.SKIPPED})}\n"
        f"Error: {manager.get_total_results({AntaTestStatus.ERROR})}\n"
        f"Unset: {manager.get_total_results({AntaTestStatus.UNSET})}\n"
        "---------------------------------------"
    )
    logger.info(bench_info)
    assert manager.get_total_results({AntaTestStatus.ERROR}) == 0
    assert manager.get_total_results({AntaTestStatus.UNSET}) == 0
