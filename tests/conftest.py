# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""See https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files."""

from __future__ import annotations

import pytest

# Load fixtures from dedicated file tests/lib/fixture.py
pytest_plugins = [
    "tests.lib.fixture",
]

# Enable nice assert messages
# https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("tests.unit.anta_tests")
