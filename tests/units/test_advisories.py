# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the built-in security advisory catalog."""

from __future__ import annotations

from anta.tests.advisories import _ADVISORY_TESTS, get_catalog


def test_get_catalog_contains_every_registered_advisory() -> None:
    """Build the default catalog from the complete explicit registry."""
    catalog = get_catalog()

    assert len(catalog.tests) == len(_ADVISORY_TESTS)
