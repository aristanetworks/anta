# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for reproducible documentation output examples."""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]
README_HELP_PATTERN = re.compile(r"^Run the ANTA CLI:\n\n(?P<help>```bash\n.*?^```)", flags=re.DOTALL | re.MULTILINE)


def test_readme_help_matches_generated_snippet() -> None:
    """Verify the standalone README help block matches generated CLI help."""
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    generated_help = (REPOSITORY_ROOT / "docs/snippets/anta_help.txt").read_text(encoding="utf-8").rstrip()
    match = README_HELP_PATTERN.search(readme)

    assert match is not None
    assert match.group("help") == f"```bash\n{generated_help}\n```"
