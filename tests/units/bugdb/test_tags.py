# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.tags."""

from __future__ import annotations

import pytest

from anta.bugdb.tags import build_implication_graph, resolve_hardware_tags


class TestBuildImplicationGraph:
    """Tests for build_implication_graph."""

    def test_empty(self) -> None:
        """Test empty implications."""
        graph = build_implication_graph([])
        assert graph == {}

    def test_simple(self) -> None:
        """Test simple direct implications."""
        implications = [["7280SR3", "DCS-7280SR3"], ["7280SR3", "Sand"]]
        graph = build_implication_graph(implications)
        assert "DCS-7280SR3" in graph["7280SR3"]
        assert "Sand" in graph["7280SR3"]

    def test_transitive(self) -> None:
        """Test transitive closure of implications."""
        implications = [["A", "B"], ["B", "C"], ["C", "D"]]
        graph = build_implication_graph(implications)
        assert graph["A"] == {"B", "C", "D"}
        assert graph["B"] == {"C", "D"}
        assert graph["C"] == {"D"}

    def test_no_cycles(self) -> None:
        """Test that cycles don't cause infinite loops."""
        implications = [["A", "B"], ["B", "A"]]
        graph = build_implication_graph(implications)
        assert "B" in graph["A"]
        assert "A" in graph["B"]


class TestResolveHardwareTags:
    """Tests for resolve_hardware_tags."""

    def test_none_model(self) -> None:
        """Test with None hw_model."""
        assert resolve_hardware_tags(None, {}) == set()

    def test_direct_match(self) -> None:
        """Test direct model match in implication graph."""
        graph = {"7280SR3": {"DCS-7280SR3", "Sand", "SandGen4"}}
        tags = resolve_hardware_tags("DCS-7280SR3-48YC8-F", graph)
        assert "DCS-7280SR3-48YC8-F" in tags
        assert "DCS-7280SR3" in tags or "Sand" in tags

    def test_suffix_stripping(self) -> None:
        """Test that -F, -R, -SSD-F etc. are stripped."""
        graph = {"DCS-7280SR3-48YC8": {"Sand"}}
        tags = resolve_hardware_tags("DCS-7280SR3-48YC8-F", graph)
        assert "Sand" in tags

    def test_dcs_prefix_stripping(self) -> None:
        """Test DCS- prefix stripping for matching."""
        graph = {"7280SR3": {"Sand", "SandGen4", "Jericho2"}}
        tags = resolve_hardware_tags("DCS-7280SR3-48YC8-F", graph)
        assert "Sand" in tags

    @pytest.mark.parametrize(
        ("model", "expected_tags"),
        [
            ("DCS-7280SR3-48YC8-F", {"DCS-7280SR3-48YC8-F", "DCS-7280SR3-48YC8", "Sand"}),
            ("DCS-7050SX3-48YC12", {"DCS-7050SX3-48YC12", "Trident3"}),
        ],
    )
    def test_realistic_models(self, model: str, expected_tags: set[str]) -> None:
        """Test with realistic model names."""
        graph = {
            "DCS-7280SR3-48YC8": {"Sand"},
            "7280SR3": {"Sand", "SandGen4"},
            "DCS-7050SX3-48YC12": {"Trident3"},
            "7050SX3": {"Trident3"},
        }
        tags = resolve_hardware_tags(model, graph)
        for expected in expected_tags:
            assert expected in tags, f"Expected tag {expected} not found in {tags}"
