# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Post an ANTA release announcement to Google Chat."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


HIGHLIGHTS_HEADING = "Highlights"
DEFAULT_DOCS_URL = "https://anta.arista.com/stable"
DEFAULT_UPGRADE_COMMAND = "pipx upgrade anta"
MAX_HIGHLIGHTS = 5
PLACEHOLDER_HIGHLIGHTS = {
    "...",
    "fill in",
    "fill this in",
    "todo",
    "tbd",
}


def _normalize_heading(heading: str) -> str:
    """Return a normalized Markdown heading title."""
    return heading.strip().strip("#").strip().strip("⭐").strip().casefold()


def _sections(markdown: str) -> dict[str, list[str]]:
    """Split a Markdown document into sections keyed by normalized heading."""
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None

    for line in markdown.splitlines():
        heading_match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if heading_match is not None:
            current_heading = _normalize_heading(heading_match.group(1))
            sections.setdefault(current_heading, [])
            continue
        if current_heading is not None:
            sections[current_heading].append(line)

    return sections


def _clean_highlight_line(line: str) -> str | None:
    """Clean a Markdown line for use as a Google Chat highlight."""
    clean_line = line.strip()
    if not clean_line or clean_line.startswith("<!--"):
        return None

    bullet_match = re.match(r"^(?:[-*+]|\d+\.)\s+(.+?)\s*$", clean_line)
    if bullet_match is not None:
        clean_line = bullet_match.group(1).strip()

    if not clean_line or clean_line.startswith("#"):
        return None
    if clean_line.casefold().startswith("full changelog"):
        return None
    if clean_line.casefold() in PLACEHOLDER_HIGHLIGHTS:
        return None

    return clean_line


def _extract_lines_from_section(section_lines: list[str], max_highlights: int) -> list[str]:
    """Extract announcement-ready highlights from a Markdown section."""
    highlights: list[str] = []
    for line in section_lines:
        highlight = _clean_highlight_line(line)
        if highlight is None:
            continue
        highlights.append(highlight)
        if len(highlights) == max_highlights:
            break
    return highlights


def extract_highlights(release_body: str, max_highlights: int = MAX_HIGHLIGHTS) -> list[str]:
    """Extract curated highlights from the release body."""
    sections = _sections(release_body)
    return _extract_lines_from_section(sections.get(_normalize_heading(HIGHLIGHTS_HEADING), []), max_highlights)


def require_highlights(release_body: str) -> list[str]:
    """Return release highlights or raise when the release body is not announcement-ready."""
    highlights = extract_highlights(release_body)
    if highlights:
        return highlights

    msg = (
        "GitHub release body must contain a non-empty '## Highlights' section before publishing. "
        "Add 3-5 curated bullets and publish the release again."
    )
    raise ValueError(msg)


def build_announcement(
    *,
    tag_name: str,
    release_url: str,
    release_body: str,
    docs_url: str = DEFAULT_DOCS_URL,
    upgrade_command: str = DEFAULT_UPGRADE_COMMAND,
) -> str:
    """Build the Google Chat release announcement text."""
    version = tag_name if tag_name.startswith("v") else f"v{tag_name}"
    highlights = require_highlights(release_body)
    highlight_lines = "\n".join(highlights)

    return (
        f"🐜 ANTA {version} is out 🐜\n\n"
        "📝 Release Notes 📝\n\n"
        f"{release_url}\n\n"
        "⭐ Highlights ⭐\n\n"
        f"{highlight_lines}\n\n"
        "📖 Documentation 📖\n\n"
        f"{docs_url}\n\n"
        "⬆️ Upgrade ⬆️\n\n"
        f"{upgrade_command}\n\n"
        "Thanks for the community feedback!\n\n"
        "Happy testing! 🐜"
    )


def load_release_event(event_path: Path) -> dict[str, str]:
    """Load release metadata from a GitHub Actions event payload."""
    with event_path.open(encoding="utf-8") as event_file:
        event = json.load(event_file)

    release = event.get("release", {})
    if not isinstance(release, dict):
        msg = "GitHub event payload does not contain a release object."
        raise ValueError(msg)

    tag_name = release.get("tag_name")
    release_url = release.get("html_url")
    if not isinstance(tag_name, str) or not tag_name:
        msg = "GitHub release payload does not contain release.tag_name."
        raise ValueError(msg)
    if not isinstance(release_url, str) or not release_url:
        msg = "GitHub release payload does not contain release.html_url."
        raise ValueError(msg)

    release_body = release.get("body", "")
    if not isinstance(release_body, str):
        release_body = ""

    return {"tag_name": tag_name, "release_url": release_url, "release_body": release_body}


def post_to_google_chat(webhook_url: str, message: str) -> None:
    """Post a text message to a Google Chat incoming webhook."""
    payload = json.dumps({"text": message}).encode()
    request = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                msg = f"Google Chat webhook returned HTTP {response.status}."
                raise RuntimeError(msg)
    except urllib.error.HTTPError as error:
        msg = f"Google Chat webhook returned HTTP {error.code}."
        raise RuntimeError(msg) from error
    except urllib.error.URLError as error:
        msg = f"Failed to reach Google Chat webhook: {error.reason}"
        raise RuntimeError(msg) from error


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate that the release body has curated highlights without posting to Google Chat.")
    parser.add_argument("--dry-run", action="store_true", help="Print the rendered announcement without posting to Google Chat.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Post the current GitHub release announcement."""
    args = parse_args(argv or [])
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("GITHUB_EVENT_PATH is not set.", file=sys.stderr)
        return 1

    try:
        release = load_release_event(Path(event_path))
        if args.check:
            require_highlights(release["release_body"])
            print("Release announcement highlights are ready.")
            return 0
        message = build_announcement(**release)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Failed to build release announcement: {error}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(message)
        return 0

    webhook_url = os.environ.get("ANTA_FIELD_WEBHOOK_URL")
    if not webhook_url:
        print("ANTA_FIELD_WEBHOOK_URL is not set.", file=sys.stderr)
        return 1

    try:
        post_to_google_chat(webhook_url, message)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print("Posted ANTA release announcement to Google Chat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
