# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for anta.runner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.result_manager import ResultManager
from anta.runner import RunnerContext, _setup_tests
from anta.settings import DEFAULT_MAX_CONCURRENCY, DEFAULT_NOFILE

if TYPE_CHECKING:
    from pytest_codspeed import BenchmarkFixture

    from anta.catalog import AntaCatalog
    from anta.inventory import AntaInventory


def test_setup_tests(benchmark: BenchmarkFixture, catalog: AntaCatalog, inventory: AntaInventory) -> None:
    """Benchmark `anta.runner._setup_tests`."""
    ctx = RunnerContext(
        manager=ResultManager(),
        inventory=inventory,
        catalog=catalog,
        devices=None,
        tests=None,
        tags=None,
        established_only=True,
        dry_run=True,
        selected_inventory=inventory,
        max_concurrency=DEFAULT_MAX_CONCURRENCY,
        file_descriptor_limit=DEFAULT_NOFILE,
    )

    def _() -> None:
        catalog.clear_indexes()
        _setup_tests(ctx)

    benchmark(_)

    assert ctx.selected_tests is not None
    assert len(ctx.selected_tests) == len(inventory)
    assert sum(len(tests) for tests in ctx.selected_tests.values()) == len(inventory) * len(catalog.tests)
