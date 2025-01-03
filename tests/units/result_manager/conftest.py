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
from tests.units.test_models import FakeTestWithInput

TEST_RESULTS: Path = Path(__file__).parent.resolve() / "test_files" / "test_md_report_results.json"


@pytest.fixture
def result_manager_factory(list_result_factory: Callable[[int, int, bool, bool], list[TestResult]]) -> Callable[[int, int, bool, bool], ResultManager]:
    """Return a ResultManager factory that takes as input a number of tests."""
    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0, nb_atomic_results: int = 0, distinct_tests: bool = False, distinct_devices: bool = False) -> ResultManager:
        """Create a factory for list[TestResult] entry of size entries."""
        result_manager = ResultManager()
        result_manager.results = list_result_factory(size, nb_atomic_results, distinct_tests, distinct_devices)
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
def test_result_factory(device: AntaDevice) -> Callable[[int, int, bool, bool], TestResult]:
    """Return a anta.result_manager.models.TestResult object."""
    # pylint: disable=redefined-outer-name

    def _create(index: int = 0, nb_atomic_results: int = 0, distinct_tests: bool = False, distinct_devices: bool = False) -> TestResult:
        """Actual Factory."""
        test = FakeTestWithInput(device=device, inputs={"string": f"Test instance {index}"})
        res = TestResult(
            name=device.name if not distinct_devices else f"{device.name}{index}",
            test=test.name if not distinct_tests else f"{test.name}{index}",
            inputs=test.inputs,
            categories=["test"],
            description=test.description,
            custom_field=None,
        )
        for i in range(nb_atomic_results):
            res.add(description=f"{test.name}{index}AtomicTestResult{i}", inputs=test.inputs)
        return res

    return _create


@pytest.fixture
def list_result_factory(test_result_factory: Callable[[int, int, bool, bool], TestResult]) -> Callable[[int, int, bool, bool], list[TestResult]]:
    """Return a list[TestResult] with 'size' TestResult instantiated using the test_result_factory fixture."""
    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0, nb_atomic_results: int = 0, distinct_tests: bool = False, distinct_devices: bool = False) -> list[TestResult]:
        """Create a factory for list[TestResult] entry of size entries."""
        return [test_result_factory(i, nb_atomic_results, distinct_tests, distinct_devices) for i in range(size)]

    return _factory
