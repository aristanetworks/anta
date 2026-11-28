#!/usr/bin/env python
# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Check that every documentation page has exactly one usable LLM export."""

from __future__ import annotations

import argparse
import re
import tomllib
from collections import Counter
from fnmatch import fnmatchcase
from pathlib import Path
from urllib.parse import unquote, urlsplit

INDEX_LINK = re.compile(r"^- \[.*?\]\(<([^>\n]+)>\)", re.MULTILINE)


def _markdown_target(source: Path, *, directory_urls: bool) -> Path:
    """Map a documentation source to Zensical's exported Markdown path."""
    if source.stem in {"README", "index"}:
        return source.with_name("index.md")
    if directory_urls:
        return source.with_suffix("") / "index.md"
    return source


def check_exports(config_path: Path, site_dir: Path) -> list[str]:
    """Return actionable diagnostics for missing, duplicate, or invalid exports."""
    with config_path.open("rb") as config_file:
        project = tomllib.load(config_file)["project"]
    docs_dir = config_path.parent / project.get("docs_dir", "docs")
    excluded = project.get("plugins", {}).get("exclude", {}).get("glob", [])
    directory_urls = project.get("use_directory_urls", True)
    errors: list[str] = []
    expected: dict[str, str] = {}
    for source in sorted(docs_dir.rglob("*.md")):
        relative = source.relative_to(docs_dir)
        if any(fnmatchcase(relative.as_posix(), pattern) for pattern in excluded):
            continue
        target_name = _markdown_target(relative, directory_urls=directory_urls).as_posix()
        if target_name in expected:
            errors.append(f"Export path collision: {expected[target_name]} and {relative} both map to {target_name}")
        expected[target_name] = relative.as_posix()

    index = (site_dir / "llms.txt").read_text(encoding="utf-8")
    site_root = site_dir.resolve()
    targets: Counter[str] = Counter()
    for destination in INDEX_LINK.findall(index):
        url = urlsplit(destination)
        path = unquote(url.path)
        resolved = (site_dir / path).resolve()
        if any((url.scheme, url.netloc, url.query, url.fragment, Path(path).is_absolute(), not resolved.is_relative_to(site_root))):
            errors.append(f"Export link must be local to this documentation version: {destination}")
            continue
        targets[resolved.relative_to(site_root).as_posix()] += 1

    for target, count in sorted(targets.items()):
        if count != 1:
            errors.append(f"Duplicate export: {target} appears {count} times in llms.txt")
        if target not in expected:
            errors.append(f"Unexpected export: {target} has no documentation source")
        if not (site_dir / target).is_file():
            errors.append(f"Missing Markdown output: {site_dir / target}")
    errors.extend(f"Missing export: {source} (expected {target} in llms.txt)" for target, source in sorted(expected.items()) if target not in targets)
    return errors


def main() -> None:
    """Validate the built index and fail with the affected source/output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("zensical.toml"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    args = parser.parse_args()
    try:
        errors = check_exports(args.config, args.site_dir)
    except (OSError, tomllib.TOMLDecodeError) as error:
        parser.exit(1, f"Cannot check LLM documentation exports: {error}\n")
    if errors:
        parser.exit(1, "LLM documentation export check failed:\n" + "\n".join(f"- {error}" for error in errors) + "\n")
    print("Every documentation page has exactly one LLM export and its Markdown output exists.")  # noqa: T201


if __name__ == "__main__":
    main()
