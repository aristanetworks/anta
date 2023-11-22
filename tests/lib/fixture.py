# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixture for Anta Testing"""
from __future__ import annotations

from os import environ
from typing import Callable
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from click.testing import CliRunner

from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from tests.lib.utils import default_anta_env

DEVICE_HW_MODEL = "pytest"
DEVICE_NAME = "pytest"


@pytest.fixture
def device() -> AntaDevice:
    """
    Returns an AntaDevice instance with mocked abstract method
    """
    with patch.object(AntaDevice, "__abstractmethods__", set()):
        dev = AntaDevice(DEVICE_NAME)  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated
    dev.hw_model = DEVICE_HW_MODEL
    return dev


@pytest.fixture
def mocked_device() -> MagicMock:
    """
    Returns a mocked device with initiazlied fields
    """

    mock = create_autospec(AntaDevice, instance=True)
    mock.host = "42.42.42.42"
    mock.name = "testdevice"
    mock.username = "toto"
    mock.password = "mysuperdupersecret"
    mock.enable_password = "mysuperduperenablesecret"
    mock.is_online = True
    mock.established = True
    mock.hw_model = "mocked_AntaDevice"
    return mock


@pytest.fixture
def test_result_factory(mocked_device: MagicMock) -> Callable[[int], TestResult]:
    """
    Return a anta.result_manager.models.TestResult object
    """

    # pylint: disable=redefined-outer-name

    def _create(index: int = 0) -> TestResult:
        """
        Actual Factory
        """
        return TestResult(
            name=mocked_device.name,
            test=f"VerifyTest{index}",
            categories=["test"],
            description=f"Verifies Test {index}",
        )

    return _create


@pytest.fixture
def list_result_factory(test_result_factory: Callable[[int], TestResult]) -> Callable[[int], list[TestResult]]:
    """
    Return a list[TestResult] with 'size' TestResult instanciated using the test_result_factory fixture
    """

    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0) -> list[TestResult]:
        """
        Factory for list[TestResult] entry of size entries
        """
        result: list[TestResult] = []
        for i in range(size):
            result.append(test_result_factory(i))
        return result

    return _factory


@pytest.fixture
def result_manager_factory(list_result_factory: Callable[[int], list[TestResult]]) -> Callable[[int], ResultManager]:
    """
    Return a ResultManager factory that takes as input a number of tests
    """

    # pylint: disable=redefined-outer-name

    def _factory(number: int = 0) -> ResultManager:
        """
        Factory for list[TestResult] entry of size entries
        """
        result_manager = ResultManager()
        result_manager.add_test_results(list_result_factory(number))
        return result_manager

    return _factory


@pytest.fixture
def test_inventory() -> AntaInventory:
    """
    Return the test_inventory
    """
    env = default_anta_env()
    return AntaInventory.parse(
        inventory_file=env["ANTA_INVENTORY"],
        username=env["ANTA_USERNAME"],
        password=env["ANTA_PASSWORD"],
    )


@pytest.fixture
def click_runner() -> CliRunner:
    """
    Convenience fixture to return a click.CliRunner for cli testing
    """
    return CliRunner()


@pytest.fixture(autouse=True)
def clean_anta_env_variables() -> None:
    """
    Autouse fixture that cleans the various ANTA_FOO env variables
    that could come from the user environment and make some tests fail.
    """
    for envvar in environ:
        if envvar.startswith("ANTA_"):
            environ.pop(envvar)
