# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli.check.commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from anta.cli._main import anta
from anta.cli.utils import ExitCode

if TYPE_CHECKING:
    from click.testing import CliRunner

DATA_DIR: Path = Path(__file__).parents[3].resolve() / "data"


@pytest.mark.parametrize(
    ("catalog_path", "expected_exit", "expected_output"),
    [
        pytest.param("ghost_catalog.yml", ExitCode.USAGE_ERROR, "Error: Invalid value for '--catalog'", id="catalog does not exist"),
        pytest.param("test_catalog_with_undefined_module.yml", ExitCode.USAGE_ERROR, "Test catalog is invalid!", id="catalog is not valid"),
        pytest.param("test_catalog.yml", ExitCode.OK, "Catalog is valid", id="catalog valid"),
    ],
)
def test_catalog(click_runner: CliRunner, catalog_path: Path, expected_exit: int, expected_output: str) -> None:
    """Test `anta check catalog -c catalog."""
    result = click_runner.invoke(anta, ["check", "catalog", "-c", str(DATA_DIR / catalog_path)])
    assert result.exit_code == expected_exit
    assert expected_output in result.output
