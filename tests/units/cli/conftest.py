# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result

import asynceapi
from anta.cli.console import console

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


logger = logging.getLogger(__name__)


MOCK_CLI_JSON: dict[str, asynceapi.EapiCommandError | dict[str, Any]] = {
    "show version": {
        "modelName": "DCS-7280CR3-32P4-F",
        "version": "4.31.1F",
    },
    "enable": {},
    "clear counters": {},
    "clear hardware counter drop": {},
    "undefined": asynceapi.EapiCommandError(
        passed=[],
        failed="show version",
        errors=["Authorization denied for command 'show version'"],
        errmsg="Invalid command",
        not_exec=[],
    ),
    "show interfaces": {},
}

MOCK_CLI_TEXT: dict[str, asynceapi.EapiCommandError | str] = {
    "show version": "Arista cEOSLab",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support": "dummy_tech-support_2023-12-01.1115.log.gz\ndummy_tech-support_2023-12-01.1015.log.gz",
    "bash timeout 10 ls -1t /mnt/flash/schedule/tech-support | head -1": "dummy_tech-support_2023-12-01.1115.log.gz",
    "show running-config | include aaa authorization exec default": "aaa authorization exec default local",
}


@pytest.fixture
def temp_env(anta_env: dict[str, str], tmp_path: Path) -> dict[str, str]:
    """Fixture that create a temporary ANTA inventory.

    The inventory can be overridden and returns the corresponding environment variables.
    """
    anta_inventory = str(anta_env["ANTA_INVENTORY"])
    temp_inventory = tmp_path / "test_inventory.yml"
    shutil.copy(anta_inventory, temp_inventory)
    anta_env["ANTA_INVENTORY"] = str(temp_inventory)
    return anta_env


@pytest.fixture
# Disabling C901 - too complex as we like our runner like this
def click_runner(capsys: pytest.CaptureFixture[str], anta_env: dict[str, str]) -> Iterator[CliRunner]:  # noqa: C901
    """Return a click.CliRunner for cli testing."""

    class AntaCliRunner(CliRunner):
        """Override CliRunner to inject specific variables for ANTA."""

        def invoke(self, *args: Any, **kwargs: Any) -> Result:  # noqa: ANN401
            # Inject default env vars if not provided
            kwargs["env"] = anta_env | kwargs.get("env", {})
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
        **_kwargs: Any,  # noqa: ANN401
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
                    if isinstance(output, asynceapi.EapiCommandError):
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

    # Patch asynceapi methods used by AsyncEOSDevice. See tests/units/test_device.py
    with (
        patch("asynceapi.device.Device.check_connection", return_value=True),
        patch("asynceapi.device.Device.cli", side_effect=cli),
        patch("asyncssh.connect"),
        patch(
            "asyncssh.scp",
        ),
    ):
        console._color_system = None
        yield AntaCliRunner()
