#!/usr/bin/env python
# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Generate stable CLI help snippets and synchronize README help text."""

import re
import sys
from pathlib import Path

from generate_snippet import main as generate_snippet

REPOSITORY_ROOT = Path(__file__).parents[2]
README_HELP_PATTERN = re.compile(r"(?P<intro>^Run the ANTA CLI:\n\n)```bash\n.*?^```", flags=re.DOTALL | re.MULTILINE)

sys.path.insert(0, str(REPOSITORY_ROOT))

COMMANDS = [
    "anta --help",
    "anta nrfu --help",
    "anta nrfu csv --help",
    "anta nrfu json --help",
    "anta nrfu table --help",
    "anta nrfu text --help",
    "anta nrfu tpl-report --help",
    "anta nrfu md-report --help",
    "anta psirt --help",
    "anta get tags --help",
    "anta get inventory --help",
    "anta get tests --help",
    "anta get from-cvp --help",
    "anta get from-ansible --help",
    "anta get commands --help",
    "anta check --help",
    "anta check catalog --help",
    "anta exec --help",
    "anta exec clear-counters --help",
    "anta exec snapshot --help",
    "anta exec collect-tech-support --help",
    "anta debug --help",
    "anta debug run-cmd --help",
    "anta debug run-template --help",
]


def sync_readme_help(readme: Path, help_snippet: Path) -> None:
    """Synchronize the standalone README help block with its generated text snippet."""
    readme_content = readme.read_text(encoding="utf-8")
    help_content = help_snippet.read_text(encoding="utf-8").rstrip()
    replacement = rf"\g<intro>```bash\n{help_content}\n```"
    updated_content, replacement_count = README_HELP_PATTERN.subn(replacement, readme_content)
    if replacement_count != 1:
        msg = f"Expected exactly one help block after 'Run the ANTA CLI:' in {readme}, found {replacement_count}"
        raise ValueError(msg)
    readme.write_text(updated_content, encoding="utf-8")


def main() -> None:
    """Generate CLI help snippets and update their standalone README copy."""
    for command in COMMANDS:
        generate_snippet(command.split(" "), output="txt")

    sync_readme_help(REPOSITORY_ROOT / "README.md", REPOSITORY_ROOT / "docs/snippets/anta_help.txt")


if __name__ == "__main__":
    main()
