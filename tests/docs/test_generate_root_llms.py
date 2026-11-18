# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Check root discovery across the rollout of versioned documentation exports."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from docs.scripts.generate_root_llms import generate_root_llms


def deployment_fixture(tmp_path: Path, exported: list[str]) -> tuple[Path, Path]:
    """Create normalized metadata with releases both before and after exports."""
    root = tmp_path / "deployment"
    root.mkdir()
    versions = [
        {"version": "main", "title": "main", "aliases": []},
        {"version": "v1.12.0", "title": "v1.12.0", "aliases": ["stable"]},
        {"version": "v1.11.0", "title": "v1.11.0", "aliases": []},
        {"version": "v1.10.0", "title": "v1.10.0", "aliases": []},
    ]
    (root / "versions.json").write_text(json.dumps(versions), encoding="utf-8")
    for version in exported:
        (root / version).mkdir()
        (root / version / "llms.txt").write_text("Versioned export\n", encoding="utf-8")
    config = tmp_path / "zensical.toml"
    config.write_text('[project]\nsite_url = "https://example.org/anta/"\n', encoding="utf-8")
    return root, config


def test_main_only_rollout_skips_old_releases(tmp_path: Path) -> None:
    """The first main deployment is discoverable before stable is rebuilt."""
    root, config = deployment_fixture(tmp_path, ["main"])
    generate_root_llms(root, config)
    content = (root / "llms.txt").read_text(encoding="utf-8")
    assert "- [Development (main)](<https://example.org/anta/main/llms.txt>)" in content
    assert "stable/llms.txt" not in content
    assert "v1.12.0/llms.txt" not in content
    assert "unreleased development" in content


def test_stable_alias_is_preferred_and_only_deployed_versions_are_listed(tmp_path: Path) -> None:
    """Stable comes first, remaining releases retain normalized order, and stale directories are ignored."""
    root, config = deployment_fixture(tmp_path, ["main", "v1.12.0", "v1.11.0", "removed-version"])
    (root / "stable").symlink_to("v1.12.0", target_is_directory=True)
    generate_root_llms(root, config)
    links = [line for line in (root / "llms.txt").read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
    assert links == [
        "- [Stable (v1.12.0)](<https://example.org/anta/stable/llms.txt>)",
        "- [Development (main)](<https://example.org/anta/main/llms.txt>)",
        "- [v1.11.0](<https://example.org/anta/v1.11.0/llms.txt>)",
    ]
    before = (root / "llms.txt").read_bytes()
    generate_root_llms(root, config)
    assert (root / "llms.txt").read_bytes() == before


def test_stable_release_falls_back_to_version_url_without_alias_export(tmp_path: Path) -> None:
    """An available release stays discoverable without linking to a missing alias."""
    root, config = deployment_fixture(tmp_path, ["v1.12.0"])
    generate_root_llms(root, config)
    assert "- [Stable (v1.12.0)](<https://example.org/anta/v1.12.0/llms.txt>)" in (root / "llms.txt").read_text(encoding="utf-8")


def test_cli_explains_missing_exports_without_traceback(tmp_path: Path) -> None:
    """Deployment should stop with the affected directory and preserve old output."""
    root, config = deployment_fixture(tmp_path, [])
    index = root / "llms.txt"
    index.write_text("Existing discovery index\n", encoding="utf-8")
    script = Path(__file__).parents[2] / "docs/scripts/generate_root_llms.py"
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(script), str(root), "--config", str(config)], check=False, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Cannot generate root llms.txt: No versioned llms.txt exports found" in result.stderr
    assert str(root) in result.stderr
    assert "Traceback" not in result.stderr
    assert index.read_text(encoding="utf-8") == "Existing discovery index\n"
