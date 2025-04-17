# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from typing import Any

import pytest

from anta.models import AntaTest
from tests.units.anta_tests import AntaUnitTest


def build_test_id(val: tuple[tuple[type[AntaTest], str], AntaUnitTest]) -> str:
    """Build id for a unit test of an AntaTest subclass.

    {
        "name": "meaniful test name",
        "test": <AntaTest instance>,
        ...
    }
    """
    # Extract the test class and its name from a nested tuple structure:
    # `val: Tuple[Tuple[Type[AntaTest], str], AntaUnitTest]`
    (anta_test, test_name) = val[0]

    return f"{anta_test.__module__}.{anta_test.__name__}-{test_name}"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate ANTA tests unit tests dynamically during test collection.

    It will parametrize test cases based on the `DATA` data structure defined in `tests.units.anta_tests` modules.
    See `tests/units/anta_tests/README.md` for more information on how to use it.
    Test IDs are generated using the `build_test_id` function above.

    Checking that only the function "test" is parametrized with data to allow for writing tests for helper functions
    in each module.
    """
    if "tests.units.anta_tests" in metafunc.module.__package__ and metafunc.function.__name__ == "test":
        # This is a unit test for an AntaTest subclass
        metafunc.parametrize("data", metafunc.module.DATA.items(), ids=build_test_id)
