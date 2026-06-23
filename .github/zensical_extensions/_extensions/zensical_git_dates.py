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


class GitDatesPreprocessor(Preprocessor):
    """Populate Material's expected Git date page metadata."""

    def run(self, lines: list[str]) -> list[str]:
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


class GitDatesExtension(Extension):
    """Register the Git date metadata preprocessor."""

    def extendMarkdown(self, md: Any) -> None:  # noqa: N802
        md.registerExtension(self)
        md.preprocessors.register(GitDatesPreprocessor(md), "zensical_git_dates", 5)


def makeExtension(**_: Any) -> GitDatesExtension:  # noqa: N802
    return GitDatesExtension()


@cache
def _last_update(root_dir: Path, path: Path) -> str | None:
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
    lines = content.splitlines()
    if lines and lines[0] == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line == "---":
                lines = lines[index + 1 :]
                break
    return "\n".join(line.rstrip() for line in lines).strip()


def _format_date(timestamp: str) -> str:
    return datetime.fromtimestamp(int(timestamp)).strftime("%B %-d, %Y")
