# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from typing import Any

import pytest


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate ANTA tests unit tests dynamically during test collection.

    It will parametrize test cases based on the `DATA` or private `_DATA` data structure defined in `tests.units.anta_tests` modules.
    See `tests/units/anta_tests/README.md` for more information on how to use it.

    Checking that only the function "test" is parametrized with data to allow for writing tests for helper functions
    in each module.
    """
    assert metafunc.module is not None
    if "tests.units.anta_tests" in metafunc.module.__package__ and metafunc.function.__name__ == "test":
        data = getattr(metafunc.module, "_DATA", None)
        if data is None:
            data = getattr(metafunc.module, "DATA", None)
        if data is None:
            msg = f"Tried to generate tests for {metafunc.module} but could not find 'DATA' or '_DATA'."
            raise RuntimeError(msg)

        # This is a unit test for an AntaTest subclass
        # Extract the test class, the unit test name and test data from the nested structure AntaUnitTestData
        test_data = tuple((x[0][0], x[1]) for x in data.items())
        metafunc.parametrize(
            "anta_test,unit_test_data",
            test_data,
            ids=[f"{anta_test.__module__}.{anta_test.__name__}-{unit_test_name}" for (anta_test, unit_test_name) in data],
        )
