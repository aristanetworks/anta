# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for documentation version management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from docs.scripts.manage_doc_versions import VersionMetadataError, manage_doc_versions, order_and_filter_versions

if TYPE_CHECKING:
    from pathlib import Path


def entry(version: str, *, aliases: list[str] | None = None, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a versions.json entry."""
    version_entry: dict[str, Any] = {"version": version, "title": version, "aliases": aliases or []}
    if properties is not None:
        version_entry["properties"] = properties
    return version_entry


def version_names(entries: list[dict[str, Any]]) -> list[str]:
    """Return version names from metadata entries."""
    return [version_entry["version"] for version_entry in entries]


def test_order_versions_keeps_main_and_finals_before_prereleases() -> None:
    """Versions should be sorted within the main, final, and prerelease groups."""
    stable_properties = {"channel": "stable"}
    entries = [
        entry("v1.10.0.dev1"),
        entry("v1.8.0"),
        entry("main"),
        entry("v1.10.0rc1"),
        entry("v1.9.0", aliases=["stable"], properties=stable_properties),
        entry("v1.10.0.dev3"),
        entry("v1.10.0.dev2"),
    ]

    ordered, removed = order_and_filter_versions(entries)

    assert version_names(ordered) == ["main", "v1.9.0", "v1.8.0", "v1.10.0rc1", "v1.10.0.dev3", "v1.10.0.dev2", "v1.10.0.dev1"]
    assert ordered[1]["aliases"] == ["stable"]
    assert ordered[1]["properties"] == stable_properties
    assert not removed


def test_manage_versions_removes_same_base_prereleases_and_paths(tmp_path: Path) -> None:
    """A final release should remove all same-base PEP 440 prerelease documentation."""
    versions = [
        entry("main"),
        entry("v1.10.0", aliases=["stable"]),
        entry("v1.10.0rc1", aliases=["candidate"]),
        entry("v1.10.0b1"),
        entry("v1.10.0a1"),
        entry("v1.10.0.dev1"),
        entry("v1.9.0"),
        entry("v1.11.0.dev1"),
    ]
    (tmp_path / "versions.json").write_text(json.dumps(versions), encoding="utf-8")
    removed_paths = ["v1.10.0rc1", "candidate", "v1.10.0b1", "v1.10.0a1", "v1.10.0.dev1"]
    for path_name in removed_paths:
        path = tmp_path / path_name
        if path_name == "candidate":
            path.write_text("alias", encoding="utf-8")
        else:
            path.mkdir()
            (path / "index.html").write_text(path_name, encoding="utf-8")

    removed = manage_doc_versions(tmp_path, "v1.10.0")

    assert removed == ["v1.10.0rc1", "v1.10.0b1", "v1.10.0a1", "v1.10.0.dev1"]
    assert all(not (tmp_path / path_name).exists() for path_name in removed_paths)
    managed = json.loads((tmp_path / "versions.json").read_text(encoding="utf-8"))
    assert version_names(managed) == ["main", "v1.10.0", "v1.9.0", "v1.11.0.dev1"]

    assert manage_doc_versions(tmp_path, "v1.10.0") == []


@pytest.mark.parametrize("final_version", ["main", "v1.10.0.dev1", "not-a-version"])
def test_cleanup_requires_a_deployed_final_version(final_version: str) -> None:
    """Cleanup should reject non-final and invalid release identifiers."""
    with pytest.raises(VersionMetadataError):
        order_and_filter_versions([entry("main"), entry("v1.10.0")], final_version)


def test_cleanup_rejects_unsafe_alias_before_removing_content(tmp_path: Path) -> None:
    """Unsafe aliases should fail without deleting already validated content."""
    prerelease_path = tmp_path / "v1.10.0.dev1"
    prerelease_path.mkdir()
    versions = [entry("main"), entry("v1.10.0"), entry("v1.10.0.dev1", aliases=["../outside"])]
    (tmp_path / "versions.json").write_text(json.dumps(versions), encoding="utf-8")

    with pytest.raises(VersionMetadataError, match="Unsafe deployed documentation path"):
        manage_doc_versions(tmp_path, "v1.10.0")

    assert prerelease_path.exists()


def test_invalid_metadata_is_rejected() -> None:
    """Malformed or duplicate version metadata should fail clearly."""
    with pytest.raises(VersionMetadataError, match="must contain a list"):
        order_and_filter_versions({})
    with pytest.raises(VersionMetadataError, match="Duplicate"):
        order_and_filter_versions([entry("main"), entry("main")])
    with pytest.raises(VersionMetadataError, match="Invalid deployed"):
        order_and_filter_versions([entry("invalid")])
