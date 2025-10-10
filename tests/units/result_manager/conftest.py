# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

import json
from pathlib import Path
from typing import Protocol

import pytest

from anta.device import AntaDevice
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from tests.units.test_models import FakeTestWithInput

TEST_RESULTS: Path = Path(__file__).parent.resolve() / "test_files" / "test_md_report_results.json"

FAKE_TEST = FakeTestWithInput


class TestResultFactoryProtocol(Protocol):
    """https://mypy.readthedocs.io/en/stable/protocols.html#callback-protocols."""

    # pylint: disable=R0903

    def __call__(self, index: int, *, distinct_tests: bool = False, distinct_devices: bool = False) -> TestResult: ...  # noqa: D102


class ResultManagerFactoryProtocol(Protocol):
    """https://mypy.readthedocs.io/en/stable/protocols.html#callback-protocols."""

    # pylint: disable=R0903

    def __call__(self, size: int, *, distinct_tests: bool = False, distinct_devices: bool = False) -> ResultManager: ...  # noqa: D102


@pytest.fixture(name="result_manager_factory")
def result_manager_factory_fixture(test_result_factory: TestResultFactoryProtocol) -> ResultManagerFactoryProtocol:
    """Return a function that creates a ResultManager instance."""

    def _create(size: int = 0, *, distinct_tests: bool = False, distinct_devices: bool = False) -> ResultManager:
        """ResultManager factory.

        Parameters
        ----------
        size
            Size of the ResultManager.
        distinct_tests
            Whether or not to use the index in the test name.
        distinct_devices
            Whether or not to use the index in the device name.
        """
        result_manager = ResultManager()
        result_manager.results = [test_result_factory(i, distinct_tests=distinct_tests, distinct_devices=distinct_devices) for i in range(size)]
        return result_manager

    return _create


@pytest.fixture(name="result_manager")
def result_manager_fixture() -> ResultManager:
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


@pytest.fixture(name="test_result_factory")
def test_result_factory_fixture(device: AntaDevice) -> TestResultFactoryProtocol:
    """Return a function that creates a TestResult instance."""

    def _create(index: int = 0, *, distinct_tests: bool = False, distinct_devices: bool = False) -> TestResult:
        """TestResult factory.

        Parameters
        ----------
        index
            Index of the TestResult instance, used to create distinct device and test names (if applicable) and a unique input for the test.
        distinct_tests
            Whether or not to use the index in the test name.
        distinct_devices
            Whether or not to use the index in the device name.
        """
        test = FAKE_TEST(device=device, inputs={"string": f"Test instance {index}"})
        return TestResult(
            name=device.name if not distinct_devices else f"{device.name}{index}",
            test=test.name if not distinct_tests else f"{test.name}{index}",
            categories=["test"],
            description=test.description,
            custom_field=None,
        )

    return _create
