# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for anta.runner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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


def test_prepare_tests(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta.runner.prepare_tests`."""

    def _() -> defaultdict[AntaDevice, set[AntaTestDefinition]] | None:
        catalog.clear_indexes()
        return prepare_tests(inventory=inventory, catalog=catalog, tests=None, tags=None)

    selected_tests = benchmark(_)

    assert selected_tests is not None
    assert len(selected_tests) == len(inventory)
    assert sum(len(tests) for tests in selected_tests.values()) == len(inventory) * len(catalog.tests)


def test_get_coroutines(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta.runner.get_coroutines`."""
    selected_tests = prepare_tests(inventory=inventory, catalog=catalog, tests=None, tags=None)

    assert selected_tests is not None
    results = ResultManager()

    def bench() -> list[Coroutine[Any, Any, TestResult]]:
        coros = get_coroutines(selected_tests=selected_tests, manager=results)
        for c in coros:
            c.close()
        return coros

    coroutines = benchmark(bench)

    count = sum(len(tests) for tests in selected_tests.values())
    assert count == len(coroutines)
