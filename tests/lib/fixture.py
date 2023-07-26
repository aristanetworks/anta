"""Fixture for Anta Testing"""

from typing import Callable
from unittest.mock import MagicMock, create_autospec

import pytest
from aioeapi import Device
from click.testing import CliRunner

from anta.device import AntaDevice
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.result_manager.models import ListResult, TestResult
from tests.lib.utils import default_anta_env


@pytest.fixture
def mocked_device(hw_model: str = "unknown_hw") -> MagicMock:
    """
    Returns a mocked device with initiazlied fields
    """

    mock = create_autospec(AntaDevice)
    mock.host = "42.42.42.42"
    mock.name = "testdevice"
    mock.username = "toto"
    mock.password = "mysuperdupersecret"
    mock.enable_password = "mysuperduperenablesecret"
    mock.session = create_autospec(Device)
    mock.is_online = True
    mock.established = True
    mock.hw_model = hw_model

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
            test_category=["test"],
            test_description=f"Verifies Test {index}",
        )

    return _create


@pytest.fixture
def list_result_factory(test_result_factory: Callable[[int], TestResult]) -> Callable[[int], ListResult]:
    """
    Return a ListResult with 'size' TestResult instanciated using the test_result_factory fixture
    """
    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0) -> ListResult:
        """
        Factory for ListResult entry of size entries
        """
        result = ListResult()
        for i in range(size):
            result.append(test_result_factory(i))
        return result

    return _factory


@pytest.fixture
def result_manager_factory(list_result_factory: Callable[[int], ListResult]) -> Callable[[int], ResultManager]:
    """
    Return a ResultManager factory that takes as input a number of tests
    """
    # pylint: disable=redefined-outer-name

    def _factory(number: int = 0) -> ResultManager:
        """
        Factory for ListResult entry of size entries
        """
        result_manager = ResultManager()
        result_manager.add_test_results(list_result_factory(number).root)
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
