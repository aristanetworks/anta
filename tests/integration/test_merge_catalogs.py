# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test examples/merge_catalogs.py script."""

from __future__ import annotations

import runpy
from pathlib import Path

from anta.catalog import AntaCatalog

DATA = Path(__file__).parent / "data"
MERGE_CATALOGS_PATH = Path(__file__).parents[2] / "examples/merge_catalogs.py"


def test_merge_catalogs() -> None:
    """Test merge_catalogs script."""
    # Adding symlink to match the script data
    intended_path = Path(__file__).parent / "intended"
    intended_path.mkdir(exist_ok=True)
    intended_catalogs_path = intended_path / "test_catalogs/"
    intended_catalogs_path.symlink_to(DATA, target_is_directory=True)

    try:
        # Run the script
        runpy.run_path(str(MERGE_CATALOGS_PATH), run_name="__main__")
        # Assert that the created file exist and is a combination of the inputs
        output_catalog = Path("anta-catalog.yml")
        assert output_catalog.exists()

        total_tests = sum(len(AntaCatalog.parse(catalog_file).tests) for catalog_file in DATA.rglob("*-catalog.yml"))

        assert total_tests == len(AntaCatalog.parse(output_catalog).tests)

    finally:
        # Cleanup
        output_catalog.unlink()
        intended_catalogs_path.unlink()
        intended_path.rmdir()
