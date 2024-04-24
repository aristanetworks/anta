# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fixture for Anta Testing."""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
from unittest.mock import patch

import pytest
import pytest_asyncio
from click.testing import CliRunner, Result

from anta import aioeapi
from anta.catalog import AntaCatalog
from anta.cli.console import console
from anta.device import AntaDevice, AsyncEOSDevice
from anta.inventory import AntaInventory
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult
from tests.lib.utils import default_anta_env

if TYPE_CHECKING:
    from collections.abc import Iterator

    from anta.models import AntaCommand

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
        passed=[],
        failed="show version",
        errors=["Authorization denied for command 'show version'"],
        errmsg="Invalid command",
        not_exec=[],
    ),
}

MOCK_CLI_TEXT: dict[str, aioeapi.EapiCommandError | str] = {
    "show version": "Arista cEOSLab",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support": "dummy_tech-support_2023-12-01.1115.log.gz\ndummy_tech-support_2023-12-01.1015.log.gz",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support | head -1": "dummy_tech-support_2023-12-01.1115.log.gz",
    "show running-config | include aaa authorization exec default": "aaa authorization exec default local",
}


@pytest.fixture()
def device(request: pytest.FixtureRequest) -> Iterator[AntaDevice]:
    """Return an AntaDevice instance with mocked abstract method."""

    def _collect(command: AntaCommand) -> None:
        command.output = COMMAND_OUTPUT

    kwargs = {"name": DEVICE_NAME, "hw_model": DEVICE_HW_MODEL}

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    with patch.object(AntaDevice, "__abstractmethods__", set()), patch("anta.device.AntaDevice._collect", side_effect=_collect):
        # AntaDevice constructor does not have hw_model argument
        hw_model = kwargs.pop("hw_model")
        dev = AntaDevice(**kwargs)  # type: ignore[abstract, arg-type]  # pylint: disable=abstract-class-instantiated, unexpected-keyword-arg
        dev.hw_model = hw_model
        yield dev


@pytest.fixture()
def test_inventory(request: pytest.FixtureRequest) -> AntaInventory:
    """Return the test_inventory."""
    env = default_anta_env()
    if hasattr(request, "param"):
        # Fixture is parametrized indirectly with a specific test inventory filename
        env["ANTA_INVENTORY"] = str(Path(__file__).parent.parent / "data" / request.param)
    assert env["ANTA_INVENTORY"]
    assert env["ANTA_USERNAME"]
    assert env["ANTA_PASSWORD"] is not None
    return AntaInventory.parse(
        filename=env["ANTA_INVENTORY"],
        username=env["ANTA_USERNAME"],
        password=env["ANTA_PASSWORD"],
    )


@pytest.fixture()
def test_catalog(request: pytest.FixtureRequest) -> AntaCatalog:
    """Return the test_catalog."""
    env = default_anta_env()
    if hasattr(request, "param"):
        # Fixture is parametrized indirectly with a specific test inventory filename
        env["ANTA_CATALOG"] = str(Path(__file__).parent.parent / "data" / request.param)
    assert env["ANTA_CATALOG"]
    return AntaCatalog.parse(filename=env["ANTA_CATALOG"])


# tests.unit.test_device.py fixture
@pytest.fixture()
def async_device(request: pytest.FixtureRequest) -> AsyncEOSDevice:
    """Return an AsyncEOSDevice instance."""
    kwargs = {
        "name": DEVICE_NAME,
        "host": "42.42.42.42",
        "username": "anta",
        "password": "anta",
    }

    if hasattr(request, "param"):
        # Fixture is parametrized indirectly
        kwargs.update(request.param)
    return AsyncEOSDevice(**kwargs)  # type: ignore[arg-type]


# tests.units.result_manager fixtures
@pytest.fixture()
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


@pytest.fixture()
def list_result_factory(test_result_factory: Callable[[int], TestResult]) -> Callable[[int], list[TestResult]]:
    """Return a list[TestResult] with 'size' TestResult instantiated using the test_result_factory fixture."""
    # pylint: disable=redefined-outer-name

    def _factory(size: int = 0) -> list[TestResult]:
        """Create a factory for list[TestResult] entry of size entries."""
        return [test_result_factory(i) for i in range(size)]

    return _factory


@pytest.fixture()
def result_manager_factory(list_result_factory: Callable[[int], list[TestResult]]) -> Callable[[int], ResultManager]:
    """Return a ResultManager factory that takes as input a number of tests."""
    # pylint: disable=redefined-outer-name

    def _factory(number: int = 0) -> ResultManager:
        """Create a factory for list[TestResult] entry of size entries."""
        result_manager = ResultManager()
        result_manager.results = list_result_factory(number)
        return result_manager

    return _factory


# tests.units.cli fixtures
@pytest.fixture()
def temp_env(tmp_path: Path) -> dict[str, str | None]:
    """Fixture that create a temporary ANTA inventory.

    The inventory can be overridden and returns the corresponding environment variables.
    """
    env = default_anta_env()
    anta_inventory = str(env["ANTA_INVENTORY"])
    temp_inventory = tmp_path / "test_inventory.yml"
    shutil.copy(anta_inventory, temp_inventory)
    env["ANTA_INVENTORY"] = str(temp_inventory)
    return env


@pytest.fixture()
# Disabling C901 - too complex as we like our runner like this
def click_runner(capsys: pytest.CaptureFixture[str]) -> Iterator[CliRunner]:  # noqa: C901
    """Return a click.CliRunner for cli testing."""

    class AntaCliRunner(CliRunner):
        """Override CliRunner to inject specific variables for ANTA."""

        def invoke(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> Result:
            # Inject default env if not provided
            kwargs["env"] = kwargs["env"] if "env" in kwargs else default_anta_env()
            # Deterministic terminal width
            kwargs["env"]["COLUMNS"] = "165"

            kwargs["auto_envvar_prefix"] = "ANTA"
            # Way to fix https://github.com/pallets/click/issues/824
            with capsys.disabled():
                result = super().invoke(*args, **kwargs)
            # disabling T201 as we want to print here
            print("--- CLI Output ---")  # noqa: T201
            print(result.output)  # noqa: T201
            return result

    def cli(
        command: str | None = None,
        commands: list[dict[str, Any]] | None = None,
        ofmt: str = "json",
        _version: int | str | None = "latest",
        **_kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
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
                    logger.info("Mocking command %s", mock_cmd)
                    if isinstance(output, aioeapi.EapiCommandError):
                        raise output
                    return output
            message = f"Command '{command}' is not mocked"
            logger.critical(message)
            raise NotImplementedError(message)

        res: dict[str, Any] | list[dict[str, Any]]
        if command is not None:
            logger.debug("Mock input %s", command)
            res = get_output(command)
        if commands is not None:
            logger.debug("Mock input %s", commands)
            res = list(map(get_output, commands))
        logger.debug("Mock output %s", res)
        return res

    # Patch aioeapi methods used by AsyncEOSDevice. See tests/units/test_device.py
    with (
        patch("aioeapi.device.Device.check_connection", return_value=True),
        patch("aioeapi.device.Device.cli", side_effect=cli),
        patch("asyncssh.connect"),
        patch(
            "asyncssh.scp",
        ),
    ):
        console._color_system = None  # pylint: disable=protected-access
        yield AntaCliRunner()


@pytest_asyncio.fixture()
async def aio_benchmark(benchmark: Callable[..., Any]) -> Callable[..., Any]:
    """Fixture to benchmark a coroutine function.

    https://github.com/ionelmc/pytest-benchmark/issues/66#issuecomment-2058337929
    """

    async def run_async_coroutine(func: Any, *args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    def _wrapper(func: Any, *args: Any, **kwargs: Any) -> Any:
        if asyncio.iscoroutinefunction(func):

            @benchmark
            def _() -> asyncio.Future:
                future = asyncio.ensure_future(run_async_coroutine(func, *args, **kwargs))
                return asyncio.get_event_loop().run_until_complete(future)
        else:
            benchmark(func, *args, **kwargs)

    return _wrapper
