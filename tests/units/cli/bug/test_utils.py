# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for anta.cli.bug.utils."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from anta.cli.bug.utils import _count_severities, _format_fixed_in, _sev_display, _split_bugs_by_target


@dataclass
class _FakeBug:
    """Minimal bug stand-in for unit tests."""

    severity: str
    version_introduced: list[str] = field(default_factory=list)
    version_fixed: list[str] = field(default_factory=list)


@dataclass
class _FakeMatch:
    """Minimal BugMatch stand-in."""

    bug: _FakeBug


@dataclass
class _FakeReport:
    """Minimal DeviceBugReport stand-in."""

    matching_bugs: list[_FakeMatch] = field(default_factory=list)


def test_format_fixed_in_empty() -> None:
    """Test _format_fixed_in with empty list."""
    assert _format_fixed_in([]) == "-"


def test_format_fixed_in_nofixyet_only() -> None:
    """Test _format_fixed_in with only nofixyet entries."""
    assert _format_fixed_in(["4.30.0.nofixyet"]) == "-"


def test_format_fixed_in_filters_nofixyet() -> None:
    """Test _format_fixed_in filters nofixyet entries."""
    result = _format_fixed_in(["4.30.0.nofixyet", "4.35.0", "4.36.0"])
    assert "nofixyet" not in result
    assert "4.35.0" in result


def test_format_fixed_in_truncation() -> None:
    """Test _format_fixed_in truncates with (+N) indicator."""
    versions = ["4.35.0", "4.35.1", "4.36.0", "4.37.0"]
    result = _format_fixed_in(versions, max_entries=3)
    assert "(+1)" in result
    assert "4.37.0" not in result


def test_format_fixed_in_no_limit() -> None:
    """Test _format_fixed_in with no truncation limit."""
    versions = ["4.35.0", "4.35.1", "4.36.0", "4.37.0"]
    result = _format_fixed_in(versions, max_entries=None)
    assert "4.37.0" in result
    assert "(+" not in result


def test_sev_display_zero() -> None:
    """Test _sev_display returns dash for zero."""
    assert _sev_display(0) == "-"


def test_sev_display_nonzero() -> None:
    """Test _sev_display returns str for nonzero."""
    assert _sev_display(5) == "5"


def test_count_severities() -> None:
    """Test _count_severities counts by severity level."""
    matches = [
        _FakeMatch(_FakeBug("sev1", [], [])),
        _FakeMatch(_FakeBug("sev1", [], [])),
        _FakeMatch(_FakeBug("sev3", [], [])),
    ]
    report = _FakeReport(matches)
    counts = _count_severities(report)  # type: ignore[arg-type]
    assert counts["sev1"] == 2
    assert counts["sev2"] == 0
    assert counts["sev3"] == 1
    assert counts["sev4"] == 0


def test_split_bugs_by_target() -> None:
    """Test _split_bugs_by_target splits fixed vs still-present bugs."""
    from anta.bugdb.version import EOSVersion

    target = EOSVersion("4.36.0F")
    matches = [
        _FakeMatch(_FakeBug("sev1", ["4.30.0"], ["4.35.0"])),
        _FakeMatch(_FakeBug("sev2", ["4.30.0"], ["4.37.0"])),
    ]
    fixed, still_present = _split_bugs_by_target(matches, target)  # type: ignore[arg-type]
    assert len(fixed) == 1
    assert fixed[0].bug.version_fixed == ["4.35.0"]
    assert len(still_present) == 1
    assert still_present[0].bug.version_fixed == ["4.37.0"]


@pytest.mark.parametrize(
    ("version_fixed", "expected_fixed"),
    [
        (["4.35.0"], True),
        (["4.37.0"], False),
        (["4.36.0"], True),
    ],
    ids=["fixed-below-target", "fixed-above-target", "fixed-at-target"],
)
def test_split_bugs_by_target_parametrized(version_fixed: list[str], expected_fixed: bool) -> None:
    """Test _split_bugs_by_target with various version_fixed values."""
    from anta.bugdb.version import EOSVersion

    target = EOSVersion("4.36.0F")
    matches = [_FakeMatch(_FakeBug("sev2", ["4.30.0"], version_fixed))]
    fixed, still_present = _split_bugs_by_target(matches, target)  # type: ignore[arg-type]
    if expected_fixed:
        assert len(fixed) == 1
        assert len(still_present) == 0
    else:
        assert len(fixed) == 0
        assert len(still_present) == 1
