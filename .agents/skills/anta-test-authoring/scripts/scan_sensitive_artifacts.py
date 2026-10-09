#!/usr/bin/env python3
"""Fail when temporary skill artifacts contain obvious secret material."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]+PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[^\s#]+"),
    re.compile(r"(?i)https?://[^\s/:]+:[^\s/@]+@"),
    re.compile(r"(?i)\b(ANTA_PASSWORD|LAB_PASSWORD|SSH_PASSWORD)\s*="),
)


def iter_files(path: Path) -> list[Path]:
    """Return regular files below ``path`` or the single file itself."""
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    raise FileNotFoundError(path)


def scan(path: Path) -> list[str]:
    """Return sanitized findings for files matching a sensitive pattern."""
    findings: list[str] = []
    for file_path in iter_files(path):
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append(f"{file_path}:{line_number}")
    return findings


def main() -> int:
    """Run the sensitive-artifact scan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="File or directory to scan")
    args = parser.parse_args()
    try:
        findings = scan(args.path)
    except FileNotFoundError as error:
        parser.error(f"path does not exist: {error.args[0]}")

    if findings:
        print("Sensitive-looking material found:", file=sys.stderr)
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"No sensitive-looking material found under {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
