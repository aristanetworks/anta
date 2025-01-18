# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta._runner.py."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from httpx import Limits
from pydantic import ValidationError

from anta._runner import AntaRunner, AntaRunnerScope
from anta.catalog import AntaCatalog
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager

# Import as Result to avoid PytestCollectionWarning
from anta.result_manager.models import TestResult as Result
from anta.settings import get_file_descriptor_limit, get_max_concurrency

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Sequence

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"
INVENTORY = AntaInventory.parse(
    filename=DATA_DIR / "test_inventory_with_tags.yml",
    username="arista",
    password="arista",
)
CATALOG = AntaCatalog.parse(filename=DATA_DIR / "test_catalog_with_tags.yml")
MANAGER = ResultManager()


# TODO: Split this test class into multiple classes
class TestAntaRunner:
    """Test AntaRunner class."""

    def test__init__(self) -> None:
        """Test AntaRunner.__init__ method."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, manager=MANAGER)

        # Test core attributes
        assert runner.inventory == INVENTORY
        assert runner.catalog == CATALOG
        assert runner.manager == MANAGER

        # Test limit values (these should match get_*_limit functions' defaults)
        assert runner.file_descriptor_limit == get_file_descriptor_limit()
        assert runner.max_concurrency == get_max_concurrency()

    def test__init__with_override_limits(self) -> None:
        """Test AntaRunner.__init__ method with overridden limits."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, manager=MANAGER, max_concurrency=1000, file_descriptor_limit=1024)

        # Test that provided values override env vars
        assert runner.max_concurrency == 1000
        assert runner.file_descriptor_limit == 1024

    async def test_reset(self) -> None:
        """Test AntaRunner.reset method."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)
        await runner.run(dry_run=True)

        # After a run, the following attributes should be set
        assert runner._selected_inventory is not None
        assert runner._selected_tests is not None
        assert runner._inventory_stats is not None
        assert runner._total_tests != 0
        assert runner._potential_connections is not None

        runner.reset()

        # After reset, the following attributes should be None
        assert runner._selected_inventory is None
        assert runner._selected_tests is None
        assert runner._inventory_stats is None
        assert runner._total_tests == 0
        assert runner._potential_connections is None

    async def test_run_no_manager(self) -> None:
        """Test AntaRunner.__init__ method without manager."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)
        assert runner.manager is None

        results = await runner.run(dry_run=True)
        assert isinstance(results, ResultManager)

    async def test_run_dry_run(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test AntaRunner.run method in dry-run mode."""
        caplog.set_level(logging.INFO)

        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)
        await runner.run(dry_run=True)

        # In dry-run mode, the selected inventory is the original inventory
        assert runner._selected_inventory is not None
        assert len(runner._selected_inventory) == len(runner.inventory)

        # In dry-run mode, the inventory stats total should match the original inventory length
        assert runner._inventory_stats is not None
        assert runner._inventory_stats.total == len(runner.inventory)

        assert "Dry-run mode, exiting before running the tests." in caplog.records[-1].message

    async def test_run_invalid_scope(self) -> None:
        """Test AntaRunner.run method with invalid scope."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)

        with pytest.raises(ValidationError, match="1 validation error for AntaRunnerScope"):
            await runner.run(scope=AntaRunnerScope(devices="invalid", tests=None, tags=None), dry_run=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("scope", "expected_devices", "expected_tests"),
        [
            pytest.param(
                AntaRunnerScope(devices=None, tests=None, tags=None),
                3,
                27,
                id="all-tests",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests=None, tags={"leaf"}),
                2,
                6,
                id="1-tag",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests=None, tags={"leaf", "spine"}),
                3,
                9,
                id="2-tags",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags=None),
                3,
                5,
                id="filtered-tests",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags={"leaf"}),
                2,
                4,
                id="1-tag-filtered-tests",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests=None, tags={"invalid"}),
                0,
                0,
                id="invalid-tag",
            ),
            pytest.param(
                AntaRunnerScope(devices=None, tests=None, tags={"dc1"}),
                0,
                0,
                id="device-tag-no-tests",
            ),
        ],
    )
    async def test_run_scope(self, caplog: pytest.LogCaptureFixture, scope: AntaRunnerScope, expected_devices: int, expected_tests: int) -> None:
        """Test AntaRunner.run method with different scopes."""
        caplog.set_level(logging.WARNING)

        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)
        await runner.run(scope, dry_run=True)

        # Check when all tests are filtered out
        if expected_devices == 0 and expected_tests == 0:
            assert runner._total_tests == 0
            assert runner._selected_tests is None
            msg = f"There are no tests matching the tags {scope.tags} to run in the current test catalog and device inventory, please verify your inputs."
            assert msg in caplog.messages
            return

        assert runner._selected_tests is not None
        assert len(runner._selected_tests) == expected_devices
        assert sum(len(tests) for tests in runner._selected_tests.values()) == expected_tests

    async def test_run_clear_results(self) -> None:
        """Test AntaRunner.run method with clearing results."""
        manager = ResultManager()
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, manager=manager)

        initial_run = await runner.run(dry_run=True, clear_results=False)
        assert initial_run.results == manager.results

        second_run = await runner.run(dry_run=True, clear_results=False)
        assert initial_run.results * 2 == second_run.results

        third_run = await runner.run(dry_run=True, clear_results=True)
        assert third_run.results == manager.results

    async def test_log_run_information_default(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the runner logs with default values."""
        caplog.set_level(logging.INFO)

        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG)
        await runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 10000",
            "  Total potential connections: 300",
            f"  Max file descriptors: {runner.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    async def test_log_run_information_max_connections(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the runner logs with custom max connections."""
        caplog.set_level(logging.INFO)

        # Creating a new inventory with HTTPX limits
        inventory = AntaInventory.parse(
            filename=DATA_DIR / "test_inventory_with_tags.yml",
            username="arista",
            password="arista",
            httpx_limits=Limits(max_connections=5, max_keepalive_connections=5),
        )

        runner = AntaRunner(inventory=inventory, catalog=CATALOG)
        await runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 10000",
            "  Total potential connections: 15",
            f"  Max file descriptors: {runner.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    async def test_log_run_information_unlimited(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the runner logs with unlimited max connections."""
        caplog.set_level(logging.WARNING)

        # Creating a new inventory with HTTPX limits
        inventory = AntaInventory.parse(
            filename=DATA_DIR / "test_inventory_with_tags.yml",
            username="arista",
            password="arista",
            httpx_limits=Limits(max_connections=None, max_keepalive_connections=None),
        )

        runner = AntaRunner(inventory=inventory, catalog=CATALOG)
        await runner.run(dry_run=True)

        warning = f"Running with unlimited connections. Connection errors may occur due to file descriptor limit ({runner.file_descriptor_limit})."
        assert warning in caplog.text

    async def test_log_run_information_concurrency_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the runner logs with higher tests count than concurrency limit."""
        caplog.set_level(logging.WARNING)

        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=20)
        await runner.run(dry_run=True)

        warning = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled."
        assert warning in caplog.text

    async def test_log_run_information_file_descriptor_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test the runner logs with higher connections count than file descriptor limit."""
        caplog.set_level(logging.WARNING)

        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, file_descriptor_limit=128)
        await runner.run(dry_run=True)

        warning = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur."
        assert warning in caplog.text

    # Helper classes and functions for testing _run function of the runner module
    class _EmptyGenerator:
        """Helper class to create an empty async generator."""

        def __aiter__(self) -> AsyncIterator[Coroutine[Any, Any, Result]]:
            """Make this class an async iterator."""
            return self

        async def __anext__(self) -> Coroutine[Any, Any, Result]:
            """Raise StopAsyncIteration."""
            raise StopAsyncIteration

    async def _mock_test_coro(self, result: Result) -> Result:
        """Mock coroutine simulating a test."""
        # Simulate some work
        await asyncio.sleep(0.1)
        return result

    async def _create_test_generator(self, results: Sequence[Result]) -> AsyncGenerator[Coroutine[Any, Any, Result], None]:
        """Create a test generator yielding mock test coroutines."""
        for result in results:
            yield self._mock_test_coro(result)

    # Tests for the _run function of the runner module
    async def test_run_with_zero_limit(self) -> None:
        """Test that run raises RuntimeError when limit is 0."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=0)
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await runner._run(generator).__anext__()

    async def test_run_with_negative_limit(self) -> None:
        """Test that run raises RuntimeError when limit is negative."""
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=-1)
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await runner._run(generator).__anext__()

    async def test_run_with_empty_generator(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test run behavior with an empty generator."""
        caplog.set_level(logging.DEBUG)
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=1)

        results = [result async for result in runner._run(self._EmptyGenerator())]  # type: ignore[arg-type]
        assert len(results) == 0
        assert "All tests have been added to the pending set" in caplog.text
        assert "No pending tests and all tests have been processed. Exiting" in caplog.text

    async def test_run_with_concurrent_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test run behavior with concurrent limit."""
        caplog.set_level(logging.DEBUG)
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=2)

        # Create 3 mock results
        results = [Mock(spec=Result) for _ in range(3)]
        generator = self._create_test_generator(results)

        # Run with limit of 2 to test concurrency limit
        completed_results = [result async for result in runner._run(generator)]

        # Verify all results were returned
        assert len(completed_results) == 3

        # Verify logging messages
        assert "Concurrency limit reached: 2 tests running" in caplog.text
        assert any("Completed" in msg and "Pending count:" in msg for msg in caplog.messages)

    async def test_run_immediate_stop_iteration(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test run behavior when generator raises StopIteration immediately."""
        caplog.set_level(logging.DEBUG)
        runner = AntaRunner(inventory=INVENTORY, catalog=CATALOG, max_concurrency=1)

        results = [result async for result in runner._run(self._EmptyGenerator())]  # type: ignore[arg-type]
        assert len(results) == 0
        assert "All tests have been added to the pending set" in caplog.text
        assert "No pending tests and all tests have been processed. Exiting" in caplog.text
