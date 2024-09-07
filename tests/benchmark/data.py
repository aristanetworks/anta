# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Loader of DATA from all tests/units/anta_tests modules."""

import importlib
import pkgutil
from collections.abc import Generator
from pathlib import Path
from types import ModuleType
from typing import Any

from anta.catalog import AntaCatalog

DATA_DIR: Path = Path(__file__).parent.parent.resolve() / "data"


def import_test_modules(package_name: str) -> Generator[ModuleType, None, None]:
    """Yield all test modules from the given package."""
    package = importlib.import_module(package_name)
    prefix = package.__name__ + "."
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix):
        if not is_pkg and module_name.split(".")[-1].startswith("test_"):
            module = importlib.import_module(module_name)
            if hasattr(module, "DATA"):
                yield module


def collect_outputs() -> dict[str, Any]:
    """Collect DATA from all unit test modules and return a dictionary of outputs per test."""
    outputs = {}
    for module in import_test_modules("tests.units.anta_tests"):
        for test_data in module.DATA:
            test = test_data["test"].__name__
            if test not in outputs:
                outputs[test] = test_data["eos_data"][0]

    return outputs


def load_catalog(filename: Path) -> AntaCatalog:
    """Load a catalog from a Path."""
    catalog = AntaCatalog.parse(filename)

    # Removing filters for testing purposes
    for test in catalog.tests:
        test.inputs.filters = None
    return catalog


def load_catalogs() -> dict[str, AntaCatalog]:
    """Load catalogs from the data directory."""
    return {
        "small": load_catalog(DATA_DIR / "test_catalog.yml"),
        "medium": load_catalog(DATA_DIR / "test_catalog_medium.yml"),
        "large": load_catalog(DATA_DIR / "test_catalog_large.yml"),
    }


OUTPUTS = collect_outputs()
CATALOGS = load_catalogs()
