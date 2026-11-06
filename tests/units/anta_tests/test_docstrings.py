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
from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.status import AdvisoryStatus
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
ADVISORY_TESTS = [test for test in ANTA_TESTS if issubclass(test, _AntaAdvisoryTest)]
ADVISORY_STATE_LABELS = tuple(status.value.replace("_", " ").title() for status in AdvisoryStatus)
ADVISORY_SECTION_LAYOUTS = (("Expected Results", "Examples"), ("Expected Results", "Notes", "Examples"))


@pytest.mark.parametrize("anta_test", ANTA_TESTS, ids=lambda test: f"{test.__module__}.{test.name}")
def test_docstring_example(anta_test: type[AntaTest]) -> None:
    """Verify that each test docstring contains a valid catalog using a supported module path."""
    example = extract_examples(anta_test.__doc__ or "")
    assert example is not None, f"{anta_test.__module__}.{anta_test.name} is missing an Examples section"

    match = re.fullmatch(r"```yaml\s*\n(?P<catalog>.*)\n\s*```", inspect.cleandoc(example), flags=re.DOTALL)
    assert match is not None, f"{anta_test.__module__}.{anta_test.name} must contain one fenced YAML example"

    catalog = AntaCatalogFile(yaml.safe_load(match.group("catalog")))
    documented_tests = [test_definition.test for test_definitions in catalog.root.values() for test_definition in test_definitions]
    assert documented_tests
    assert all(documented_test is anta_test for documented_test in documented_tests)
    assert len(catalog.root) == 1
    catalog_module = next(iter(catalog.root))
    is_defining_module = catalog_module.__name__ == anta_test.__module__
    is_explicit_reexport = anta_test.__name__ in getattr(catalog_module, "__all__", ()) and getattr(catalog_module, anta_test.__name__, None) is anta_test
    assert is_defining_module or is_explicit_reexport, f"{catalog_module.__name__} must define or explicitly export {anta_test.__name__}"


@pytest.mark.parametrize("anta_test", ADVISORY_TESTS, ids=lambda test: test.name)
def test_advisory_docstring_layout(anta_test: type[AntaTest]) -> None:
    """Verify that each advisory test docstring uses the advisory sections and assessment state labels."""
    lines = inspect.cleandoc(anta_test.__doc__ or "").splitlines()
    headers = [index for index in range(1, len(lines) - 1) if re.fullmatch(r"-+", lines[index + 1]) and len(lines[index + 1]) == len(lines[index])]
    layout = tuple(lines[index] for index in headers)
    assert layout in ADVISORY_SECTION_LAYOUTS, f"{anta_test.name} sections must be one of {ADVISORY_SECTION_LAYOUTS}, got {layout}"
    assert not any(line.strip() for line in lines[1 : headers[0]]), f"{anta_test.name} must not have text between the summary and Expected Results"

    expected_results = [line for line in lines[headers[0] + 2 : headers[1]] if line.strip()]
    assert all(line.startswith(("* ", "  ")) for line in expected_results), f"{anta_test.name} Expected Results must only contain bullets"
    labels = [line[2:].split(":", 1)[0] for line in expected_results if line.startswith("* ")]
    assert set(labels) <= set(ADVISORY_STATE_LABELS), f"{anta_test.name} Expected Results labels must be in {ADVISORY_STATE_LABELS}, got {labels}"
    assert labels == sorted(set(labels), key=ADVISORY_STATE_LABELS.index), f"{anta_test.name} Expected Results labels must be unique and ordered"
