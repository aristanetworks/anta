# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.matcher."""

from __future__ import annotations

import pytest

from anta.bugdb.matcher import match_bug, match_bugs
from anta.bugdb.models import Bug
from anta.bugdb.version import EOSVersion


def _make_bug(
    bug_id: int = 1,
    severity: str = "sev2",
    product: str = "eos",
    introduced: list[str] | None = None,
    fixed: list[str] | None = None,
    conjunction: list[list[dict[str, str]]] | None = None,
) -> Bug:
    """Create a Bug instance for testing."""
    conj = [[{"tag": c["tag"]} for c in clause] for clause in conjunction] if conjunction else []
    return Bug.model_validate(
        {
            "bugId": bug_id,
            "severity": severity,
            "alertSummary": f"Bug {bug_id}",
            "product": product,
            "versionIntroduced": introduced or ["4.20.0"],
            "versionFixed": fixed or ["4.25.0"],
            "conjunction": conj,
        }
    )


class TestMatchBug:
    """Tests for match_bug function."""

    def test_non_eos_product(self) -> None:
        """Test that non-EOS bugs are not matched."""
        bug = _make_bug(product="cvp")
        assert match_bug(bug, EOSVersion("4.22.0F"), set()) is None

    def test_not_affected_version(self) -> None:
        """Test that unaffected versions are not matched."""
        bug = _make_bug(introduced=["4.20.0"], fixed=["4.22.0"])
        assert match_bug(bug, EOSVersion("4.22.1F"), set()) is None

    def test_version_only_match(self) -> None:
        """Test matching a bug with no conjunction (version-only)."""
        bug = _make_bug(introduced=["4.20.0"], fixed=["4.25.0"])
        result = match_bug(bug, EOSVersion("4.22.0F"), set())
        assert result is not None
        assert "version-only" in result.matched_by

    def test_conjunction_match(self) -> None:
        """Test matching a bug via conjunction tags."""
        bug = _make_bug(conjunction=[[{"tag": "Sand"}, {"tag": "bgpEnabled"}]])
        result = match_bug(bug, EOSVersion("4.22.0F"), {"Sand", "bgpEnabled", "SandGen4"})
        assert result is not None
        assert "Sand" in result.matched_by
        assert "bgpEnabled" in result.matched_by

    def test_conjunction_no_match(self) -> None:
        """Test that missing tags prevent conjunction match."""
        bug = _make_bug(conjunction=[[{"tag": "Sand"}, {"tag": "bgpEnabled"}]])
        result = match_bug(bug, EOSVersion("4.22.0F"), {"Sand"})
        assert result is None

    def test_conjunction_or_match(self) -> None:
        """Test OR logic: second clause matches."""
        bug = _make_bug(
            conjunction=[
                [{"tag": "Trident3"}],
                [{"tag": "Sand"}],
            ],
        )
        result = match_bug(bug, EOSVersion("4.22.0F"), {"Sand"})
        assert result is not None
        assert "clause 1" in result.matched_by

    def test_conjunction_or_no_match(self) -> None:
        """Test that no OR clause matches."""
        bug = _make_bug(
            conjunction=[
                [{"tag": "Trident3"}],
                [{"tag": "Jericho2"}],
            ],
        )
        assert match_bug(bug, EOSVersion("4.22.0F"), {"Sand"}) is None


class TestMatchBugs:
    """Tests for match_bugs function."""

    def test_empty_bugs(self) -> None:
        """Test with no bugs."""
        assert match_bugs([], EOSVersion("4.22.0F"), set()) == []

    def test_multiple_matches(self) -> None:
        """Test matching multiple bugs."""
        bugs = [
            _make_bug(bug_id=1, severity="sev1"),
            _make_bug(bug_id=2, severity="sev2"),
            _make_bug(bug_id=3, severity="sev3"),
        ]
        matches = match_bugs(bugs, EOSVersion("4.22.0F"), set())
        assert len(matches) == 3

    def test_sorted_by_severity(self) -> None:
        """Test that results are sorted by severity then bug_id."""
        bugs = [
            _make_bug(bug_id=3, severity="sev3"),
            _make_bug(bug_id=1, severity="sev1"),
            _make_bug(bug_id=2, severity="sev2"),
        ]
        matches = match_bugs(bugs, EOSVersion("4.22.0F"), set())
        assert [m.bug.severity for m in matches] == ["sev1", "sev2", "sev3"]

    @pytest.mark.parametrize(
        ("min_severity", "expected_count"),
        [
            ("sev1", 1),
            ("sev2", 2),
            ("sev3", 3),
            (None, 3),
        ],
    )
    def test_severity_filter(self, min_severity: str | None, expected_count: int) -> None:
        """Test severity filtering."""
        bugs = [
            _make_bug(bug_id=1, severity="sev1"),
            _make_bug(bug_id=2, severity="sev2"),
            _make_bug(bug_id=3, severity="sev3"),
        ]
        matches = match_bugs(bugs, EOSVersion("4.22.0F"), set(), min_severity=min_severity)
        assert len(matches) == expected_count
