# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test examples/parse_anta_inventory_file.py script."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from yaml import safe_dump

from anta.inventory import AntaInventory

DATA = Path(__file__).parent / "data"
PARSE_ANTA_INVENTORY_FILE_PATH = Path(__file__).parents[2] / "examples/parse_anta_inventory_file.py"


@pytest.mark.parametrize("inventory", [{"count": 3}], indirect=["inventory"])
def test_parse_anta_inventory_file(capsys: pytest.CaptureFixture[str], inventory: AntaInventory) -> None:
    """Test parse_anta_inventory_file script."""
    # Create the inventory.yaml file expected by the script
    # TODO: 2.0.0 this is horrendous - need to align how to dump things properly
    inventory_path = Path.cwd() / "inventory.yaml"
    yaml_data = {AntaInventory.INVENTORY_ROOT_KEY: inventory.dump().model_dump()}
    with inventory_path.open("w") as f:
        safe_dump(yaml_data, f)

    try:
        # Run the script
        runpy.run_path(str(PARSE_ANTA_INVENTORY_FILE_PATH), run_name="__main__")
        captured = capsys.readouterr()
        assert "Device device-0 is online" in captured.out
        assert "Device device-1 is online" in captured.out
        assert "Device device-2 is online" in captured.out

    finally:
        # Cleanup
        inventory_path.unlink()
