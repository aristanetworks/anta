# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.exec.utils."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import call, patch

import pytest

from anta.cli.exec.utils import (
    clear_counters,
)
from anta.models import AntaCommand

# , collect_commands, collect_scheduled_show_tech

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.inventory import AntaInventory


# TODO: complete test cases
@pytest.mark.parametrize(
    ("inventory_state", "per_device_command_output", "tags"),
    [
        pytest.param(
            {
                "dummy": {"is_online": False},
                "dummy2": {"is_online": False},
                "dummy3": {"is_online": False},
            },
            {},
            None,
            id="no_connected_device",
        ),
        pytest.param(
            {
                "dummy": {"is_online": True, "hw_model": "cEOSLab"},
                "dummy2": {"is_online": True, "hw_model": "vEOS-lab"},
                "dummy3": {"is_online": False},
            },
            {},
            None,
            id="cEOSLab and vEOS-lab devices",
        ),
        pytest.param(
            {
                "dummy": {"is_online": True},
                "dummy2": {"is_online": True},
                "dummy3": {"is_online": False},
            },
            {"dummy": None},  # None means the command failed to collect
            None,
            id="device with error",
        ),
        pytest.param(
            {
                "dummy": {"is_online": True},
                "dummy2": {"is_online": True},
                "dummy3": {"is_online": True},
            },
            {},
            ["spine"],
            id="tags",
        ),
    ],
)
async def test_clear_counters(
    caplog: pytest.LogCaptureFixture,
    test_inventory: AntaInventory,
    inventory_state: dict[str, Any],
    per_device_command_output: dict[str, Any],
    tags: set[str] | None,
) -> None:
    """Test anta.cli.exec.utils.clear_counters."""

    async def mock_connect_inventory() -> None:
        """Mock connect_inventory coroutine."""
        for name, device in test_inventory.items():
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
        await clear_counters(test_inventory, tags=tags)

    mocked_connect_inventory.assert_awaited_once()
    devices_established = test_inventory.get_inventory(established_only=True, tags=tags).devices
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
