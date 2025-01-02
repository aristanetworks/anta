# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

import json
from pathlib import Path
from typing import Callable

import pytest

from anta.device import AntaDevice
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult

TEST_RESULTS: Path = Path(__file__).parent.resolve() / "test_files" / "test_md_report_results.json"


@pytest.fixture
def result_manager_factory(list_result_factory: Callable[[int], list[TestResult]]) -> Callable[[int], ResultManager]:
    """Return a ResultManager factory that takes as input a number of tests."""
    # pylint: disable=redefined-outer-name

    def _factory(number: int = 0) -> ResultManager:
        """Create a factory for list[TestResult] entry of size entries."""
        result_manager = ResultManager()
        result_manager.results = list_result_factory(number)
        return result_manager

    return _factory


@pytest.fixture
def result_manager() -> ResultManager:
    """Return a ResultManager with 30 random tests loaded from a JSON file.

    Devices: DC1-SPINE1, DC1-LEAF1A

    - Total tests: 30
    - Success: 7
    - Skipped: 2
    - Failure: 19
    - Error: 2

    See `tests/units/result_manager/test_md_report_results.json` for details.
    """
    manager = ResultManager()

    with TEST_RESULTS.open("r", encoding="utf-8") as f:
        results = json.load(f)

    for result in results:
        manager.add(TestResult(**result))

    return manager


@pytest.fixture
def test_result_factory(device: AntaDevice) -> Callable[[int], TestResult]:
    """Return a anta.result_manager.models.TestResult object."""
    # pylint: disable=redefined-outer-name

    def _create(index: int = 0) -> TestResult:
        """Actual Factory."""
        return TestResult(
            name=device.name,
            test=f"VerifyTest{index}",
            categories=["test"],
            description=f"Verifies Test {index}",
            custom_field=None,
        )

    return _create


@pytest.fixture
def list_result_factory(test_result_factory: Callable[[int], TestResult]) -> Callable[[int], list[TestResult]]:
    """Return a list[TestResult] with 'size' TestResult instantiated using the test_result_factory fixture."""
    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0) -> list[TestResult]:
        """Create a factory for list[TestResult] entry of size entries."""
        return [test_result_factory(i) for i in range(size)]

    return _factory
