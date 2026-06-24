# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Expose page Git update dates to Zensical templates."""

from __future__ import annotations

import subprocess
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

from markdown import Extension
from markdown.preprocessors import Preprocessor

from zensical.extensions.context import ContextPreprocessor


class GitDatesPreprocessor(Preprocessor):  # pylint: disable=too-few-public-methods
    """Populate Material's expected Git date page metadata."""

    def run(self, lines: list[str]) -> list[str]:
        """Set the current page's Git revision metadata."""
        context = ContextPreprocessor.from_markdown(self.md)
        if context is None:
            return lines

        root_dir = Path(context.config.get("root_dir", ".")).resolve()
        docs_dir = Path(context.config.get("docs_dir", "docs"))
        path = docs_dir / context.page.path
        if path.is_absolute():
            path = path.relative_to(root_dir)
        date = _last_update(root_dir, path)
        if date is not None:
            context.page.meta["git_revision_date_localized"] = date

        return lines


class GitDatesExtension(Extension):  # pylint: disable=too-few-public-methods
    """Register the Git date metadata preprocessor."""

    def extendMarkdown(self, md: Any) -> None:  # noqa: N802
        """Register the Git dates preprocessor with Python-Markdown."""
        md.registerExtension(self)
        md.preprocessors.register(GitDatesPreprocessor(md), "zensical_git_dates", 5)


def makeExtension(**_: Any) -> GitDatesExtension:  # noqa: N802
    """Create the Markdown extension instance."""
    return GitDatesExtension()


@cache
def _last_update(root_dir: Path, path: Path) -> str | None:
    """Return the latest Git date for Markdown body changes."""
    relpath = path.as_posix()
    for commit, parents, timestamp in _history(root_dir, relpath):
        parent = parents.split(" ", 1)[0]
        if not parent:
            return _format_date(timestamp)

        current = _content_at(root_dir, commit, relpath)
        previous = _content_at(root_dir, parent, relpath)
        if current is None or previous is None:
            return _format_date(timestamp)

        if _markdown_body(current) != _markdown_body(previous):
            return _format_date(timestamp)

    return None


def _history(root_dir: Path, relpath: str) -> list[tuple[str, str, str]]:
    try:
        output = subprocess.check_output(
            [
                "git",
                "-C",
                str(root_dir),
                "log",
                "--follow",
                "--format=%H%x00%P%x00%ct",
                "--",
                relpath,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return []

    history = []
    for line in output.splitlines():
        parts = line.split("\x00")
        if len(parts) == 3:
            history.append((parts[0], parts[1], parts[2]))
    return history


def _content_at(root_dir: Path, commit: str, relpath: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root_dir), "show", f"{commit}:{relpath}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None


def _markdown_body(content: str) -> str:
    """Return Markdown content without leading metadata/license boilerplate."""
    lines = [line.rstrip() for line in content.splitlines()]
    while lines:
        stripped = _strip_leading_blank_lines(lines)
        stripped = _strip_front_matter(stripped)
        stripped = _strip_leading_blank_lines(stripped)
        stripped = _strip_license_comment(stripped)
        stripped = _strip_leading_blank_lines(stripped)
        if stripped == lines:
            break
        lines = stripped
    return "\n".join(line.rstrip() for line in lines).strip()


def _strip_leading_blank_lines(lines: list[str]) -> list[str]:
    """Remove leading blank lines."""
    for index, line in enumerate(lines):
        if line:
            return lines[index:]
    return []


def _strip_front_matter(lines: list[str]) -> list[str]:
    """Remove leading YAML front matter."""
    if lines and lines[0] == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line == "---":
                return lines[index + 1 :]
    return lines


def _strip_license_comment(lines: list[str]) -> list[str]:
    """Remove a leading repository license HTML comment."""
    if not lines or lines[0] != "<!--":
        return lines
    for index, line in enumerate(lines[1:], start=1):
        if line == "  -->":
            block = "\n".join(lines[: index + 1])
            if "Copyright (c)" in block and "LICENSE file" in block:
                return lines[index + 1 :]
            break
    return lines


def _format_date(timestamp: str) -> str:
    return datetime.fromtimestamp(int(timestamp)).strftime("%B %-d, %Y")
