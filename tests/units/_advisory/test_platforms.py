# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for shared advisory platform-family patterns."""

import pytest

from anta._advisory.platforms import PLATFORM_FAMILY_PATTERNS, PlatformFamily, patterns_for


def test_every_platform_family_has_patterns() -> None:
    """Verify the registry covers every declared family."""
    assert set(PlatformFamily) == set(PLATFORM_FAMILY_PATTERNS)
    assert all(PLATFORM_FAMILY_PATTERNS.values())


@pytest.mark.parametrize(
    ("family", "positive", "negative"),
    [
        pytest.param(PlatformFamily.SERIES_720_D, "CCS-720DF-48Y6", "CCS-720XP-48ZC2", id="720d"),
        pytest.param(PlatformFamily.SERIES_755_758, "CCS-755-CH-F", "DCS-7508N", id="755-758"),
        pytest.param(PlatformFamily.SERIES_7050_X3, "DCS-7050CX3-32S", "DCS-7050SX2-72Q", id="7050x3"),
        pytest.param(PlatformFamily.SERIES_7250_X, "DCS-7250QX-64", "DCS-7260CX-64", id="7250x"),
        pytest.param(PlatformFamily.SERIES_7280_R3, "DCS-7280CR3-32P4", "DCS-7280CR2-60", id="7280r3"),
        pytest.param(PlatformFamily.SERIES_7368_X4, "7368-F", "7358-R", id="7368x4"),
    ],
)
def test_platform_family_patterns(family: PlatformFamily, positive: str, negative: str) -> None:
    """Verify representative positive and adjacent negative model names."""
    patterns = patterns_for(family)

    assert any(pattern.fullmatch(positive) for pattern in patterns)
    assert not any(pattern.fullmatch(negative) for pattern in patterns)


def test_patterns_for_composes_families() -> None:
    """Verify callers can combine atomic platform families."""
    patterns = patterns_for(PlatformFamily.SERIES_7050_X3, PlatformFamily.SERIES_7050_X4)

    assert any(pattern.fullmatch("DCS-7050CX3-32S") for pattern in patterns)
    assert any(pattern.fullmatch("DCS-7050CX4-40D") for pattern in patterns)
    assert not any(pattern.fullmatch("DCS-7050SX2-72Q") for pattern in patterns)
