# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test examples/run_eos_commands.py script."""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import respx

if TYPE_CHECKING:
    from anta.inventory import AntaInventory

DATA = Path(__file__).parent / "data"
RUN_EOS_COMMANDS_PATH = Path(__file__).parents[2] / "examples/run_eos_commands.py"


@pytest.mark.parametrize("inventory", [{"count": 3}], indirect=["inventory"])
def test_run_eos_commands(capsys: pytest.CaptureFixture[str], inventory: AntaInventory) -> None:
    """Test run_eos_commands script."""
    # Create the inventory.yaml file expected by the script
    inventory_path = Path(__file__).parent / "inventory.yaml"
    inventory.dump(inventory_path)

    try:
        respx.post(path="/command-api", headers={"Content-Type": "application/json-rpc"}, json__params__cmds__0__cmd="show ip bgp summary").respond(
            json={
                "result": [
                    {
                        "mocked": "mock",
                    }
                ],
            }
        )
        # Run the script
        runpy.run_path(str(RUN_EOS_COMMANDS_PATH), run_name="__main__")
        captured = capsys.readouterr()
        assert "Device device-0 is online" in captured.out
        assert "Device device-1 is online" in captured.out
        assert "Device device-2 is online" in captured.out

    finally:
        # Cleanup
        inventory_path.unlink()
