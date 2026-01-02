# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for anta.runner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._runner import AntaRunContext, AntaRunFilters, AntaRunner
from anta.result_manager import ResultManager
from anta.runner import get_coroutines, prepare_tests

if TYPE_CHECKING:
    from collections import defaultdict
    from collections.abc import Coroutine

    from pytest_codspeed import BenchmarkFixture

    from anta.catalog import AntaCatalog, AntaTestDefinition
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory
    from anta.result_manager.models import TestResult


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_prepare_tests(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta.runner.prepare_tests`."""

    def _() -> defaultdict[AntaDevice, set[AntaTestDefinition]] | None:
        catalog.clear_indexes()
        return prepare_tests(inventory=inventory, catalog=catalog, tests=None, tags=None)

    selected_tests = benchmark(_)

    assert selected_tests is not None
    assert len(selected_tests) == len(inventory)
    assert sum(len(tests) for tests in selected_tests.values()) == len(inventory) * len(catalog.tests)


# TODO: Remove this in ANTA v2.0.0
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_get_coroutines(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta.runner.get_coroutines`."""
    selected_tests = prepare_tests(inventory=inventory, catalog=catalog, tests=None, tags=None)

    assert selected_tests is not None
    results = ResultManager()

    def bench() -> list[Coroutine[Any, Any, TestResult]]:
        results.reset()
        coros = get_coroutines(selected_tests=selected_tests, manager=results)
        for c in coros:
            c.close()
        return coros

    coroutines = benchmark(bench)

    count = sum(len(tests) for tests in selected_tests.values())
    assert count == len(coroutines)


def test__setup_tests(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta._runner.AntaRunner._setup_tests`."""
    runner = AntaRunner()
    ctx = AntaRunContext(inventory=inventory, catalog=catalog, manager=ResultManager(), filters=AntaRunFilters(), selected_inventory=inventory)

    def bench() -> None:
        catalog.clear_indexes()
        runner._setup_tests(ctx)

    benchmark(bench)

    assert ctx.total_tests_scheduled != 0
    assert ctx.total_devices_selected_for_testing == len(inventory)
    assert ctx.total_tests_scheduled == len(inventory) * len(catalog.tests)


def test__get_test_coroutines(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta._runner.AntaRunner._get_test_coroutines`."""
    runner = AntaRunner()
    ctx = AntaRunContext(inventory=inventory, catalog=catalog, manager=ResultManager(), filters=AntaRunFilters(), selected_inventory=inventory)
    runner._setup_tests(ctx)

    assert ctx.selected_tests is not None

    def bench() -> list[Coroutine[Any, Any, TestResult]]:
        coros = runner._get_test_coroutines(ctx)
        for c in coros:
            c.close()
        return coros

    coroutines = benchmark(bench)

    assert ctx.total_tests_scheduled == len(coroutines)
