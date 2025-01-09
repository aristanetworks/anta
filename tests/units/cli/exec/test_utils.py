# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.exec.utils."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import call, patch

import pytest
import respx

from anta.cli.exec.utils import clear_counters, collect_commands
from anta.models import AntaCommand
from anta.tools import safe_command

# collect_scheduled_show_tech

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory


# TODO: complete test cases
@pytest.mark.parametrize(
    ("inventory", "inventory_state", "per_device_command_output", "tags"),
    [
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": False},
                "device-1": {"is_online": False},
                "device-2": {"is_online": False},
            },
            {},
            None,
            id="no_connected_device",
        ),
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": True, "hw_model": "cEOSLab"},
                "device-1": {"is_online": True, "hw_model": "vEOS-lab"},
                "device-2": {"is_online": False},
            },
            {},
            None,
            id="cEOSLab and vEOS-lab devices",
        ),
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": True},
                "device-1": {"is_online": True},
                "device-2": {"is_online": False},
            },
            {"device-0": None},  # None means the command failed to collect
            None,
            id="device with error",
        ),
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": True},
                "device-1": {"is_online": True},
                "device-2": {"is_online": True},
            },
            {},
            ["spine"],
            id="tags",
        ),
    ],
    indirect=["inventory"],
)
async def test_clear_counters(
    caplog: pytest.LogCaptureFixture,
    inventory: AntaInventory,
    inventory_state: dict[str, Any],
    per_device_command_output: dict[str, Any],
    tags: set[str] | None,
) -> None:
    """Test anta.cli.exec.utils.clear_counters."""

    async def mock_connect_inventory() -> None:
        """Mock connect_inventory coroutine."""
        for name, device in inventory.items():
            device.is_online = inventory_state[name].get("is_online", True)
            device.established = inventory_state[name].get("established", device.is_online)
            device.hw_model = inventory_state[name].get("hw_model", "dummy")

    async def collect(self: AntaDevice, command: AntaCommand, *args: Any, **kwargs: Any) -> None:  # noqa: ARG001, ANN401
        """Mock collect coroutine."""
        command.output = per_device_command_output.get(self.name, "")

    # Need to patch the child device class
    with (
        patch("anta.device.AsyncEOSDevice.collect", side_effect=collect, autospec=True) as mocked_collect,
        patch(
            "anta.inventory.AntaInventory.connect_inventory",
            side_effect=mock_connect_inventory,
        ) as mocked_connect_inventory,
    ):
        await clear_counters(inventory, tags=tags)

    mocked_connect_inventory.assert_awaited_once()
    devices_established = inventory.get_inventory(established_only=True, tags=tags).devices
    if devices_established:
        # Building the list of calls
        calls = []
        for device in devices_established:
            calls.append(
                call(
                    device,
                    command=AntaCommand(
                        command="clear counters",
                        version="latest",
                        revision=None,
                        ofmt="json",
                        output=per_device_command_output.get(device.name, ""),
                        errors=[],
                    ),
                    collection_id=None,
                ),
            )
            if device.hw_model not in ["cEOSLab", "vEOS-lab"]:
                calls.append(
                    call(
                        device,
                        command=AntaCommand(
                            command="clear hardware counter drop",
                            version="latest",
                            revision=None,
                            ofmt="json",
                            output=per_device_command_output.get(device.name, ""),
                        ),
                        collection_id=None,
                    ),
                )
        mocked_collect.assert_has_awaits(calls)
        # Check error
        for key, value in per_device_command_output.items():
            if value is None:
                # means some command failed to collect
                assert "ERROR" in caplog.text
                assert f"Could not clear counters on device {key}: []" in caplog.text
    else:
        mocked_collect.assert_not_awaited()


# TODO: test with changing root_dir, test with failing to write (OSError)
@pytest.mark.parametrize(
    ("inventory", "inventory_state", "commands", "tags"),
    [
        pytest.param(
            {"count": 1},
            {
                "device-0": {"is_online": False},
            },
            {"json_format": ["show version"]},
            None,
            id="no_connected_device",
        ),
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": True},
                "device-1": {"is_online": True},
                "device-2": {"is_online": False},
            },
            {"json_format": ["show version", "show ip interface brief"]},
            None,
            id="JSON commands",
        ),
        pytest.param(
            {"count": 3},
            {
                "device-0": {"is_online": True},
                "device-1": {"is_online": True},
                "device-2": {"is_online": False},
            },
            {"json_format": ["show version"], "text_format": ["show running-config", "show ip interface"]},
            None,
            id="Text commands",
        ),
        pytest.param(
            {"count": 2},
            {
                "device-0": {"is_online": True, "tags": {"spine"}},
                "device-1": {"is_online": True},
            },
            {"json_format": ["show version"]},
            {"spine"},
            id="tags",
        ),
        pytest.param(  # TODO: This test should not be there we should catch the wrong user input with pydantic.
            {"count": 1},
            {
                "device-0": {"is_online": True},
            },
            {"blah_format": ["42"]},
            None,
            id="bad-input",
        ),
        pytest.param(
            {"count": 1},
            {
                "device-0": {"is_online": True},
            },
            {"json_format": ["undefined command", "show version"]},
            None,
            id="command-failed-to-be-collected",
        ),
        pytest.param(
            {"count": 1},
            {
                "device-0": {"is_online": True},
            },
            {"json_format": ["uncaught exception"]},
            None,
            id="uncaught-exception",
        ),
    ],
    indirect=["inventory"],
)
async def test_collect_commands(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
    inventory: AntaInventory,
    inventory_state: dict[str, Any],
    commands: dict[str, list[str]],
    tags: set[str] | None,
) -> None:
    """Test anta.cli.exec.utils.collect_commands."""
    caplog.set_level(logging.INFO)
    root_dir = tmp_path

    async def mock_connect_inventory() -> None:
        """Mock connect_inventory coroutine."""
        for name, device in inventory.items():
            device.is_online = inventory_state[name].get("is_online", True)
            device.established = inventory_state[name].get("established", device.is_online)
            device.hw_model = inventory_state[name].get("hw_model", "dummy")
            device.tags = inventory_state[name].get("tags", set())

    # Need to patch the child device class
    # ruff: noqa: C901
    with (
        respx.mock,
        patch(
            "anta.inventory.AntaInventory.connect_inventory",
            side_effect=mock_connect_inventory,
        ) as mocked_connect_inventory,
    ):
        # Mocking responses from devices
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show version").respond(
            json={"result": [{"toto": 42}]}
        )
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip interface brief").respond(
            json={"result": [{"toto": 42}]}
        )
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show running-config").respond(
            json={"result": [{"output": "blah"}]}
        )
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip interface").respond(
            json={"result": [{"output": "blah"}]}
        )
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="undefined command").respond(
            json={
                "error": {
                    "code": 1002,
                    "message": "CLI command 1 of 1 'undefined command' failed: invalid command",
                    "data": [{"errors": ["Invalid input (at token 0: 'undefined')"]}],
                }
            }
        )
        await collect_commands(inventory, commands, root_dir, tags=tags)

    mocked_connect_inventory.assert_awaited_once()
    devices_established = inventory.get_inventory(established_only=True, tags=tags or None).devices
    if not devices_established:
        assert "INFO" in caplog.text
        assert "No online device found. Exiting" in caplog.text
        return

    for device in devices_established:
        # Verify tags selection
        assert device.tags.intersection(tags) != {} if tags else True
        json_path = root_dir / device.name / "json"
        text_path = root_dir / device.name / "text"
        if "json_format" in commands:
            # Handle undefined command
            if "undefined command" in commands["json_format"]:
                assert "ERROR" in caplog.text
                assert "Command 'undefined command' failed on device-0: Invalid input (at token 0: 'undefined')" in caplog.text
                # Verify we don't claim it was collected
                assert f"Collected command 'undefined command' from device {device.name}" not in caplog.text
                commands["json_format"].remove("undefined command")
            # Handle uncaught exception
            elif "uncaught exception" in commands["json_format"]:
                assert "ERROR" in caplog.text
                assert "Error when collecting commands: " in caplog.text
                # Verify we don't claim it was collected
                assert f"Collected command 'uncaught exception' from device {device.name}" not in caplog.text
                commands["json_format"].remove("uncaught exception")

            assert json_path.is_dir()
            assert len(list(Path.iterdir(json_path))) == len(commands["json_format"])
            for command in commands["json_format"]:
                assert Path.is_file(json_path / f"{safe_command(command)}.json")
                assert f"Collected command '{command}' from device {device.name}" in caplog.text
        if "text_format" in commands:
            assert text_path.is_dir()
            assert len(list(text_path.iterdir())) == len(commands["text_format"])
            for command in commands["text_format"]:
                assert Path.is_file(text_path / f"{safe_command(command)}.log")
                assert f"Collected command '{command}' from device {device.name}" in caplog.text
