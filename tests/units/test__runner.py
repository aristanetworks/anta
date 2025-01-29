# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta._runner.py."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from httpx import Limits
from pydantic import ValidationError

from anta._runner import AntaRunner, AntaRunnerScope
from anta.result_manager import ResultManager

# Import as Result to avoid PytestCollectionWarning
from anta.result_manager.models import TestResult as Result
from anta.settings import get_file_descriptor_limit, get_max_concurrency

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Sequence


class TestAntaRunnerBasic:
    """Test AntaRunner basic functionality."""

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "manager": ResultManager()}], indirect=True
    )
    def test_init(self, anta_runner: AntaRunner) -> None:
        """Test basic initialization."""
        assert anta_runner.manager is not None
        assert len(anta_runner.inventory.devices) == 3
        assert len(anta_runner.catalog.tests) == 11
        assert len(anta_runner.manager.results) == 0

        # Test limit values (these should match get_*_limit functions' defaults)
        assert anta_runner.file_descriptor_limit == get_file_descriptor_limit()
        assert anta_runner.max_concurrency == get_max_concurrency()

        # Check private attributes are initialized
        assert anta_runner._selected_inventory is None
        assert anta_runner._selected_tests is None
        assert anta_runner._inventory_stats is None
        assert anta_runner._total_tests == 0
        assert anta_runner._potential_connections is None

    @pytest.mark.parametrize(
        ("anta_runner"),
        [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 1000, "file_descriptor_limit": 1024}],
        indirect=True,
    )
    def test_init_with_override_limits(self, anta_runner: AntaRunner) -> None:
        """Test initialization with custom limits."""
        assert anta_runner.max_concurrency == 1000
        assert anta_runner.file_descriptor_limit == 1024

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_reset(self, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.reset method."""
        await anta_runner.run(dry_run=True)

        # After a run, the following attributes should be set
        assert anta_runner._selected_inventory is not None
        assert anta_runner._selected_tests is not None
        assert anta_runner._inventory_stats is not None
        assert anta_runner._total_tests != 0
        assert anta_runner._potential_connections is not None

        anta_runner.reset()

        # After reset, the following attributes should be None
        assert anta_runner._selected_inventory is None
        assert anta_runner._selected_tests is None
        assert anta_runner._inventory_stats is None
        assert anta_runner._total_tests == 0
        assert anta_runner._potential_connections is None


class TestAntaRunnerRun:
    """Test AntaRunner.run method."""

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_run_dry_run(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.run method in dry-run mode."""
        caplog.set_level(logging.INFO)

        await anta_runner.run(dry_run=True)

        # In dry-run mode, the selected inventory is the original inventory
        assert anta_runner._selected_inventory is not None
        assert len(anta_runner._selected_inventory) == len(anta_runner.inventory)

        # In dry-run mode, the inventory stats total should match the original inventory length
        assert anta_runner._inventory_stats is not None
        assert anta_runner._inventory_stats.total == len(anta_runner.inventory)

        assert "Dry-run mode, exiting before running the tests." in caplog.records[-1].message

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_run_invalid_scope(self, anta_runner: AntaRunner) -> None:
        """Test AntaRunner.run method with invalid scope."""
        with pytest.raises(ValidationError, match="1 validation error for AntaRunnerScope"):
            await anta_runner.run(scope=AntaRunnerScope(devices="invalid", tests=None, tags=None), dry_run=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("anta_runner", "scope", "expected_devices", "expected_tests"),
        [
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests=None, tags=None),
                3,
                27,
                id="all-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests=None, tags={"leaf"}),
                2,
                6,
                id="1-tag",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests=None, tags={"leaf", "spine"}),
                3,
                9,
                id="2-tags",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags=None),
                3,
                5,
                id="filtered-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests={"VerifyMlagStatus", "VerifyUptime"}, tags={"leaf"}),
                2,
                4,
                id="1-tag-filtered-tests",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests=None, tags={"invalid"}),
                0,
                0,
                id="invalid-tag",
            ),
            pytest.param(
                {"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"},
                AntaRunnerScope(devices=None, tests=None, tags={"dc1"}),
                0,
                0,
                id="device-tag-no-tests",
            ),
        ],
        indirect=["anta_runner"],
    )
    async def test_run_scope(
        self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner, scope: AntaRunnerScope, expected_devices: int, expected_tests: int
    ) -> None:
        """Test AntaRunner.run method with different scopes."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(scope, dry_run=True)

        # Check when all tests are filtered out
        if expected_devices == 0 and expected_tests == 0:
            assert anta_runner._total_tests == 0
            assert anta_runner._selected_tests is None
            msg = f"There are no tests matching the tags {scope.tags} to run in the current test catalog and device inventory, please verify your inputs."
            assert msg in caplog.messages
            return

        assert anta_runner._selected_tests is not None
        assert len(anta_runner._selected_tests) == expected_devices
        assert sum(len(tests) for tests in anta_runner._selected_tests.values()) == expected_tests

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_multiple_runs_no_manager(self, anta_runner: AntaRunner) -> None:
        """Test multiple runs without a ResultManager instance."""
        assert anta_runner.manager is None

        first_run_manager = await anta_runner.run(dry_run=True)
        assert isinstance(first_run_manager, ResultManager)
        assert len(first_run_manager.results) == 27

        second_run_manager = await anta_runner.run(dry_run=True)
        assert isinstance(second_run_manager, ResultManager)
        assert len(second_run_manager.results) == 27

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "manager": ResultManager()}], indirect=True
    )
    async def test_multiple_runs_with_manager(self, anta_runner: AntaRunner) -> None:
        """Test multiple runs with a provided ResultManager instance."""
        assert anta_runner.manager is not None

        first_run_manager = await anta_runner.run(dry_run=True)
        assert len(first_run_manager.results) == 27
        assert first_run_manager.results == anta_runner.manager.results

        # When a manager is provided, results from subsequent runs are appended to the manager
        second_run_manager = await anta_runner.run(dry_run=True)
        assert len(second_run_manager.results) == 54
        assert first_run_manager.results == second_run_manager.results


class TestAntaRunnerConcurrency:
    """Test AntaRunner._run method."""

    # Helper classes and functions for testing _run method
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

    # Unit tests for _run method
    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 0}], indirect=True
    )
    async def test_run_with_zero_limit(self, anta_runner: AntaRunner) -> None:
        """Test that _run raises RuntimeError when limit is 0."""
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await anta_runner._run(generator).__anext__()  # pylint: disable=unnecessary-dunder-call

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": -1}], indirect=True
    )
    async def test_run_with_negative_limit(self, anta_runner: AntaRunner) -> None:
        """Test that _run raises RuntimeError when limit is negative."""
        mock_result = Mock(spec=Result)
        generator = self._create_test_generator([mock_result])

        with pytest.raises(RuntimeError, match="Concurrency limit must be greater than 0"):
            await anta_runner._run(generator).__anext__()  # pylint: disable=unnecessary-dunder-call

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 1}], indirect=True
    )
    async def test_run_with_empty_generator(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _run behavior with an empty generator."""
        caplog.set_level(logging.DEBUG)

        results = [result async for result in anta_runner._run(self._EmptyGenerator())]  # type: ignore[arg-type]
        assert len(results) == 0
        assert "All tests have been added to the pending set" in caplog.text
        assert "No pending tests and all tests have been processed. Exiting" in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 2}], indirect=True
    )
    async def test_run_with_concurrent_limit(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _run behavior with concurrent limit."""
        caplog.set_level(logging.DEBUG)

        # Create 3 mock results
        results = [Mock(spec=Result) for _ in range(3)]
        generator = self._create_test_generator(results)

        # Run with limit of 2 to test concurrency limit
        completed_results = [result async for result in anta_runner._run(generator)]

        # Verify all results were returned
        assert len(completed_results) == 3

        # Verify logging messages
        assert "Concurrency limit reached: 2 tests running" in caplog.text
        assert any("Completed" in msg and "Pending count:" in msg for msg in caplog.messages)

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 1}], indirect=True
    )
    async def test_run_immediate_stop_iteration(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _run behavior when generator raises StopIteration immediately."""
        caplog.set_level(logging.DEBUG)

        results = [result async for result in anta_runner._run(self._EmptyGenerator())]  # type: ignore[arg-type]
        assert len(results) == 0
        assert "All tests have been added to the pending set" in caplog.text
        assert "No pending tests and all tests have been processed. Exiting" in caplog.text


class TestAntaRunnerLogging:
    """Test AntaRunner logging."""

    @pytest.mark.parametrize(("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml"}], indirect=True)
    async def test_log_run_information_default(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with default values."""
        caplog.set_level(logging.INFO)

        await anta_runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 10000",
            "  Total potential connections: 300",
            f"  Max file descriptors: {anta_runner.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"),
        [
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "httpx_limits": Limits(max_connections=5, max_keepalive_connections=5),
            }
        ],
        indirect=True,
    )
    async def test_log_run_information_max_connections(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with custom max connections."""
        caplog.set_level(logging.INFO)

        await anta_runner.run(dry_run=True)

        expected_output = [
            "ANTA NRFU Run Information",
            "Devices:",
            "  Total: 3",
            "  Selected: 0 (dry-run mode)",
            "Tests: 27 total",
            "Limits:",
            "  Max concurrent tests: 10000",
            "  Total potential connections: 15",
            f"  Max file descriptors: {anta_runner.file_descriptor_limit}",
        ]
        for line in expected_output:
            assert line in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"),
        [
            {
                "inventory": "test_inventory_with_tags.yml",
                "catalog": "test_catalog_with_tags.yml",
                "httpx_limits": Limits(max_connections=None, max_keepalive_connections=None),
            }
        ],
        indirect=True,
    )
    async def test_log_run_information_unlimited(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with unlimited max connections."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(dry_run=True)

        warning = f"Running with unlimited connections. Connection errors may occur due to file descriptor limit ({anta_runner.file_descriptor_limit})."
        assert warning in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "max_concurrency": 20}], indirect=True
    )
    async def test_log_run_information_concurrency_limit(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with higher tests count than concurrency limit."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(dry_run=True)

        warning = "Tests count (27) exceeds concurrent limit (20). Tests will be throttled."
        assert warning in caplog.text

    @pytest.mark.parametrize(
        ("anta_runner"), [{"inventory": "test_inventory_with_tags.yml", "catalog": "test_catalog_with_tags.yml", "file_descriptor_limit": 128}], indirect=True
    )
    async def test_log_run_information_file_descriptor_limit(self, caplog: pytest.LogCaptureFixture, anta_runner: AntaRunner) -> None:
        """Test _log_run_information with higher connections count than file descriptor limit."""
        caplog.set_level(logging.WARNING)

        await anta_runner.run(dry_run=True)

        warning = "Potential connections (300) exceeds file descriptor limit (128). Connection errors may occur."
        assert warning in caplog.text
