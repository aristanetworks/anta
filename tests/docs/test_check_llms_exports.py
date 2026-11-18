# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Exercise the export check against omissions and misleading build output."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from docs.scripts.check_llms_exports import check_exports


def build_fixture(tmp_path: Path, sources: list[str], targets: list[str], *, directory_urls: bool = True) -> tuple[Path, Path]:
    """Create independent documentation sources and an index with real outputs."""
    config = tmp_path / "zensical.toml"
    config.write_text(
        f'[project]\ndocs_dir = "docs"\nuse_directory_urls = {str(directory_urls).lower()}\n[project.plugins.exclude]\nglob = ["scripts/**"]\n',
        encoding="utf-8",
    )
    for source in sources:
        path = tmp_path / "docs" / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Documentation\n", encoding="utf-8")
    site = tmp_path / "site"
    site.mkdir()
    for target in targets:
        path = site / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Exported content\n", encoding="utf-8")
    (site / "llms.txt").write_text("\n".join(f"- [Page](<{target}>): Useful description." for target in targets), encoding="utf-8")
    return config, site


@pytest.mark.parametrize("directory_urls", [True, False])
def test_export_mapping_and_exclusions(tmp_path: Path, *, directory_urls: bool) -> None:
    """Home, nested index, spaces, descriptions, and excluded scripts are supported."""
    page_target = "guide/new page/index.md" if directory_urls else "guide/new page.md"
    config, site = build_fixture(
        tmp_path,
        ["README.md", "guide/index.md", "guide/new page.md", "scripts/internal.md"],
        ["index.md", "guide/index.md", page_target],
        directory_urls=directory_urls,
    )
    assert not check_exports(config, site)


def test_new_page_missing_from_sections_is_reported(tmp_path: Path) -> None:
    """An unselected source must fail even when all current index links work."""
    config, site = build_fixture(tmp_path, ["README.md", "new-page.md"], ["index.md"])
    assert check_exports(config, site) == ["Missing export: new-page.md (expected new-page/index.md in llms.txt)"]


def test_duplicate_sections_and_missing_output_are_reported(tmp_path: Path) -> None:
    """A valid-looking index must not hide duplicate entries or absent artifacts."""
    config, site = build_fixture(tmp_path, ["README.md"], ["index.md", "index.md"])
    (site / "index.md").unlink()
    assert check_exports(config, site) == [
        "Duplicate export: index.md appears 2 times in llms.txt",
        f"Missing Markdown output: {site / 'index.md'}",
    ]


@pytest.mark.parametrize("destination", ["https://anta.arista.com/stable/index.md", "../index.md"])
def test_links_cannot_leave_selected_version(tmp_path: Path, destination: str) -> None:
    """Canonical URLs and parent paths must not escape the selected version."""
    config, site = build_fixture(tmp_path, ["README.md"], ["index.md"])
    (site / "llms.txt").write_text(f"- [Home](<{destination}>)\n", encoding="utf-8")
    assert check_exports(config, site)[0] == f"Export link must be local to this documentation version: {destination}"


def test_stale_export_is_reported(tmp_path: Path) -> None:
    """A removed source cannot leave a silently accepted stale index entry."""
    config, site = build_fixture(tmp_path, ["README.md"], ["index.md", "old/index.md"])
    assert check_exports(config, site) == ["Unexpected export: old/index.md has no documentation source"]


def test_source_collision_is_reported(tmp_path: Path) -> None:
    """One index entry must not be accepted as covering two source pages."""
    config, site = build_fixture(tmp_path, ["README.md", "index.md"], ["index.md"])
    assert check_exports(config, site) == ["Export path collision: README.md and index.md both map to index.md"]


def test_cli_reports_missing_index_without_traceback(tmp_path: Path) -> None:
    """A missing build should tell a maintainer which artifact is unavailable."""
    config, site = build_fixture(tmp_path, ["README.md"], ["index.md"])
    (site / "llms.txt").unlink()
    script = Path(__file__).parents[2] / "docs/scripts/check_llms_exports.py"
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(script), "--config", str(config), "--site-dir", str(site)], check=False, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Cannot check LLM documentation exports:" in result.stderr
    assert str(site / "llms.txt") in result.stderr
    assert "Traceback" not in result.stderr
