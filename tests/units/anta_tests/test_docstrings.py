# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Validate the examples in ANTA test docstrings."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from typing import TYPE_CHECKING

import pytest
import yaml

import anta.tests
from anta.catalog import AntaCatalogFile
from anta.cli.get.utils import extract_examples
from anta.models import AntaTest

if TYPE_CHECKING:
    from types import ModuleType


def _get_anta_tests() -> list[type[AntaTest]]:
    """Return every concrete test defined in the anta.tests package."""
    modules: list[ModuleType] = [anta.tests]
    modules.extend(importlib.import_module(module_name) for _, module_name, _ in pkgutil.walk_packages(anta.tests.__path__, prefix=f"{anta.tests.__name__}."))

    tests = {
        member
        for module in modules
        for _, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, AntaTest) and member is not AntaTest and not inspect.isabstract(member) and member.__module__ == module.__name__
    }
    return sorted(tests, key=lambda test: (test.__module__, test.name))


ANTA_TESTS = _get_anta_tests()


@pytest.mark.parametrize("anta_test", ANTA_TESTS, ids=lambda test: f"{test.__module__}.{test.name}")
def test_docstring_example(anta_test: type[AntaTest]) -> None:
    """Verify that each test docstring contains a valid catalog for that test."""
    example = extract_examples(anta_test.__doc__ or "")
    assert example is not None, f"{anta_test.__module__}.{anta_test.name} is missing an Examples section"

    match = re.fullmatch(r"```yaml\s*\n(?P<catalog>.*)\n\s*```", inspect.cleandoc(example), flags=re.DOTALL)
    assert match is not None, f"{anta_test.__module__}.{anta_test.name} must contain one fenced YAML example"

    catalog = AntaCatalogFile(yaml.safe_load(match.group("catalog")))
    documented_tests = [test_definition.test for test_definitions in catalog.root.values() for test_definition in test_definitions]
    assert documented_tests
    assert all(documented_test is anta_test for documented_test in documented_tests)
    assert {module.__name__ for module in catalog.root} == {anta_test.__module__}
