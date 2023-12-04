# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixture for Anta Testing"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Callable, Iterator
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from pytest import CaptureFixture

from anta import aioeapi
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

MOCK_CLI_JSON: dict[str, aioeapi.EapiCommandError | dict[str, Any]] = {
    "show version": {
        "modelName": "DCS-7280CR3-32P4-F",
        "version": "4.31.1F",
    },
    "enable": {},
    "clear counters": {},
    "clear hardware counter drop": {},
    "undefined": aioeapi.EapiCommandError(
        passed=[], failed="show version", errors=["Authorization denied for command 'show version'"], errmsg="Invalid command", not_exec=[]
    ),
}

MOCK_CLI_TEXT: dict[str, aioeapi.EapiCommandError | str] = {
    "show version": "Arista cEOSLab",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support": "dummy_tech-support_2023-12-01.1115.log.gz\ndummy_tech-support_2023-12-01.1015.log.gz",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support | head -1": "dummy_tech-support_2023-12-01.1115.log.gz",
    "show running-config | include aaa authorization exec default": "aaa authorization exec default local",
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
def test_inventory() -> AntaInventory:
    """
    Return the test_inventory
    """
    env = default_anta_env()
    assert env["ANTA_INVENTORY"] and env["ANTA_USERNAME"] and env["ANTA_PASSWORD"] is not None
    return AntaInventory.parse(
        filename=env["ANTA_INVENTORY"],
        username=env["ANTA_USERNAME"],
        password=env["ANTA_PASSWORD"],
    )


# tests.unit.test_device.py fixture
@pytest.fixture
def async_device(request: pytest.FixtureRequest) -> AsyncEOSDevice:
    """
    Returns an AsyncEOSDevice instance
    """

    kwargs = {"name": DEVICE_NAME, "host": "42.42.42.42", "username": "anta", "password": "anta"}

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    dev = AsyncEOSDevice(**kwargs)  # type: ignore[arg-type]
    return dev


# tests.units.result_manager fixtures
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


# tests.units.cli fixtures
@pytest.fixture
def temp_env(tmp_path: Path) -> dict[str, str | None]:
    """Fixture that create a temporary ANTA inventory that can be overriden
    and returns the corresponding environment variables"""
    env = default_anta_env()
    anta_inventory = str(env["ANTA_INVENTORY"])
    temp_inventory = tmp_path / "test_inventory.yml"
    shutil.copy(anta_inventory, temp_inventory)
    env["ANTA_INVENTORY"] = str(temp_inventory)
    return env


@pytest.fixture
def click_runner(capsys: CaptureFixture[str]) -> Iterator[CliRunner]:
    """
    Convenience fixture to return a click.CliRunner for cli testing
    """

    class AntaCliRunner(CliRunner):
        """Override CliRunner to inject specific variables for ANTA"""

        def invoke(self, *args, **kwargs) -> Result:  # type: ignore[no-untyped-def]
            # Inject default env if not provided
            kwargs["env"] = kwargs["env"] if "env" in kwargs else default_anta_env()
            kwargs["auto_envvar_prefix"] = "ANTA"
            # Way to fix https://github.com/pallets/click/issues/824
            with capsys.disabled():
                result = super().invoke(*args, **kwargs)
            print("--- CLI Output ---")
            print(result.output)
            return result

    def cli(
        command: str | None = None, commands: list[dict[str, Any]] | None = None, ofmt: str = "json", **kwargs: dict[str, Any]
    ) -> dict[str, Any] | list[dict[str, Any]]:
        # pylint: disable=unused-argument
        def get_output(command: str | dict[str, Any]) -> dict[str, Any]:
            if isinstance(command, dict):
                command = command["cmd"]
            mock_cli: dict[str, Any]
            if ofmt == "json":
                mock_cli = MOCK_CLI_JSON
            elif ofmt == "text":
                mock_cli = MOCK_CLI_TEXT
            for mock_cmd, output in mock_cli.items():
                if command == mock_cmd:
                    logger.info(f"Mocking command {mock_cmd}")
                    if isinstance(output, aioeapi.EapiCommandError):
                        raise output
                    return output
            message = f"Command '{command}' is not mocked"
            logger.critical(message)
            raise NotImplementedError(message)

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
    with patch("aioeapi.device.Device.check_connection", return_value=True), patch("aioeapi.device.Device.cli", side_effect=cli), patch("asyncssh.connect"), patch(
        "asyncssh.scp"
    ):
        yield AntaCliRunner()
