# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for anta.runner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._runner import AntaRunner, AntaRunnerScope
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

    def bench() -> list[Coroutine[Any, Any, TestResult]]:
        coros = get_coroutines(selected_tests=selected_tests, manager=ResultManager())
        for c in coros:
            c.close()
        return coros

    coroutines = benchmark(bench)

    count = sum(len(tests) for tests in selected_tests.values())
    assert count == len(coroutines)


def test_setup_tests(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta._runner.AntaRunner._setup_tests`."""
    runner = AntaRunner(inventory=inventory, catalog=catalog)
    runner._selected_inventory = inventory

    def bench() -> bool:
        catalog.clear_indexes()
        return runner._setup_tests(scope=AntaRunnerScope())

    benchmark(bench)

    assert runner._selected_tests is not None
    assert len(runner._selected_tests) == len(inventory)
    assert sum(len(tests) for tests in runner._selected_tests.values()) == len(inventory) * len(catalog.tests)
