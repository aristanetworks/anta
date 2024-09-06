# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Loader of DATA from all tests/units/anta_tests modules."""

import importlib
import pkgutil
from collections.abc import Generator
from types import ModuleType
from typing import Any

ALL_DATA: list[dict[str, Any]] = []
"""List of all unit tests DATA from all tests/units/anta_tests modules."""


def import_test_modules(package_name: str) -> Generator[ModuleType, None, None]:
    """Yield all test modules from the given package."""
    package = importlib.import_module(package_name)
    prefix = package.__name__ + "."
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix):
        if not is_pkg and module_name.split(".")[-1].startswith("test_"):
            module = importlib.import_module(module_name)
            if hasattr(module, "DATA"):
                yield module


def collect_all_data() -> None:
    """Collect DATA from all test modules in tests/units/anta_tests."""
    for module in import_test_modules("tests.units.anta_tests"):
        ALL_DATA.extend(module.DATA)


# Collect all data when this module is loaded
# TODO: Pytest already loads all test modules, so we could collect DATA from there. Maybe in a pytest hook? Investigate with `pytest_collection_modifyitems`
collect_all_data()
