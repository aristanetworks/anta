# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixture for Anta Testing"""
from __future__ import annotations

import logging
from typing import Any, Callable, Iterator
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from pytest import CaptureFixture

from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.models import AntaCommand
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from tests.lib.utils import default_anta_env

logger = logging.getLogger(__name__)

DEVICE_HW_MODEL = "pytest"
DEVICE_NAME = "pytest"
COMMAND_OUTPUT = "retrieved"

MOCK_CLI: dict[str, dict[str, Any]] = {
    "show version": {
        "modelName": "DCS-7280CR3-32P4-F",
        "version": "4.31.1F",
    },
    "enable": {},
}


@pytest.fixture
def device(request: pytest.FixtureRequest) -> Iterator[AntaDevice]:
    """
    Returns an AntaDevice instance with mocked abstract method
    """

    def _collect(command: AntaCommand) -> None:
        command.output = COMMAND_OUTPUT

    kwargs = {"name": DEVICE_NAME, "hw_model": DEVICE_HW_MODEL}

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    with patch.object(AntaDevice, "__abstractmethods__", set()):
        with patch("anta.device.AntaDevice._collect", side_effect=_collect):
            # AntaDevice constructor does not have hw_model argument
            hw_model = kwargs.pop("hw_model")
            dev = AntaDevice(**kwargs)  # type: ignore[abstract, arg-type]  # pylint: disable=abstract-class-instantiated, unexpected-keyword-arg
            dev.hw_model = hw_model
            yield dev


@pytest.fixture
def async_device(request: pytest.FixtureRequest) -> AntaDevice:
    """
    Returns an AsyncEOSDevice instance
    """

    kwargs = {"name": DEVICE_NAME, "host": "42.42.42.42", "username": "anta", "password": "anta"}

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    dev = AsyncEOSDevice(**kwargs)  # type: ignore[arg-type]
    return dev


@pytest.fixture
def test_result_factory(device: AntaDevice) -> Callable[[int], TestResult]:
    """
    Return a anta.result_manager.models.TestResult object
    """

    # pylint: disable=redefined-outer-name

    def _create(index: int = 0) -> TestResult:
        """
        Actual Factory
        """
        return TestResult(
            name=device.name,
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
        filename=env["ANTA_INVENTORY"],
        username=env["ANTA_USERNAME"],
        password=env["ANTA_PASSWORD"],
    )


@pytest.fixture
def click_runner(capsys: CaptureFixture[str]) -> CliRunner:
    """
    Convenience fixture to return a click.CliRunner for cli testing
    """

    class AntaCliRunner(CliRunner):
        def invoke(self, *args, **kwargs) -> Result:  # type: ignore[override, no-untyped-def]
            # Inject default env if not provided
            kwargs["env"] = kwargs["env"] if "env" in kwargs else default_anta_env()
            kwargs["auto_envvar_prefix"] = "ANTA"
            # Way to fix https://github.com/pallets/click/issues/824
            with capsys.disabled():
                result = super().invoke(*args, **kwargs)  # type: ignore[arg-type]
            print("--- CLI Output ---")
            print(result.output)
            return result

    def cli(
        command: str | None = None, commands: list[dict[str, Any]] | None = None, ofmt: str = "json", **kwargs: dict[str, Any]
    ) -> dict[str, Any] | list[dict[str, Any]]:
        def get_output(command: str | dict[str, Any]) -> dict[str, Any]:
            if isinstance(command, dict):
                command = command["cmd"]
            for mock_cmd, output in MOCK_CLI.items():
                if command == mock_cmd:
                    logger.info(f"Mocking command {mock_cmd}")
                    return output
            raise NotImplementedError(f"Command '{command}' is not mocked")

        # pylint: disable=unused-argument
        if ofmt != "json":
            raise NotImplementedError()
        res: dict[str, Any] | list[dict[str, Any]]
        if command is not None:
            logger.debug(f"Mock input {command}")
            res = get_output(command)
        if commands is not None:
            logger.debug(f"Mock input {commands}")
            res = list(map(get_output, commands))
        logger.debug(f"Mock output {res}")
        return res

    # Patch aioeapi methods used by AsyncEOSDevice. See tests/units/test_device.py
    with patch("aioeapi.device.Device.check_connection", return_value=True):
        with patch("aioeapi.device.Device.cli", side_effect=cli):
            yield AntaCliRunner()
