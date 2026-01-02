# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test examples/run_eos_commands.py script."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
import respx
from yaml import safe_dump

from anta.inventory import AntaInventory

DATA = Path(__file__).parent / "data"
RUN_EOS_COMMANDS_PATH = Path(__file__).parents[2] / "examples/run_eos_commands.py"


@pytest.mark.parametrize("inventory", [{"count": 3}], indirect=["inventory"])
def test_run_eos_commands(capsys: pytest.CaptureFixture[str], inventory: AntaInventory) -> None:
    """Test run_eos_commands script."""
    # Create the inventory.yaml file expected by the script
    # TODO: 2.0.0 this is horrendous - need to align how to dump things properly
    inventory_path = Path.cwd() / "inventory.yaml"
    yaml_data = {AntaInventory.INVENTORY_ROOT_KEY: inventory.dump().model_dump()}
    with inventory_path.open("w") as f:
        safe_dump(yaml_data, f)

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
        # This is only to make sure we get the expected output - what counts is that the script runs.
        assert "'device-0': [AntaCommand(command='show version', version='latest', revision=None, ofmt='json', output={'modelName': 'pytest'}," in captured.out
        assert "'device-1': [AntaCommand(command='show version', version='latest', revision=None, ofmt='json', output={'modelName': 'pytest'}," in captured.out
        assert "'device-2': [AntaCommand(command='show version', version='latest', revision=None, ofmt='json', output={'modelName': 'pytest'}," in captured.out
        assert "AntaCommand(command='show ip bgp summary', version='latest', revision=None, ofmt='json', output={'mocked': 'mock'}, " in captured.out

    finally:
        # Cleanup
        inventory_path.unlink()
