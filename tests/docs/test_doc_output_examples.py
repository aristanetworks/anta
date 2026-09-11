# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for reproducible documentation output examples."""

from __future__ import annotations

import re
from pathlib import Path

from anta.cli.get.utils import create_inventory_from_ansible

REPOSITORY_ROOT = Path(__file__).parents[2]
README_HELP_PATTERN = re.compile(r"^Run the ANTA CLI:\n\n(?P<help>```bash\n.*?^```)", flags=re.DOTALL | re.MULTILINE)
LOCAL_SVG_PATTERN = re.compile(r"!\[[^]]*\]\((?!https?://)[^)\n]+\.svg\)(?P<attributes>\{[^}\n]*\})?")


def test_readme_help_matches_generated_snippet() -> None:
    """Verify the standalone README help block matches generated CLI help."""
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    generated_help = (REPOSITORY_ROOT / "docs/snippets/anta_help.txt").read_text(encoding="utf-8").rstrip()
    match = README_HELP_PATTERN.search(readme)

    assert match is not None
    assert match.group("help") == f"```bash\n{generated_help}\n```"


def test_documentation_svg_images_are_centered() -> None:
    """Verify local SVG images use the shared centering class."""
    missing_center_class = []

    for markdown_path in (REPOSITORY_ROOT / "docs").rglob("*.md"):
        for line_number, line in enumerate(markdown_path.read_text(encoding="utf-8").splitlines(), start=1):
            missing_center_class.extend(
                f"{markdown_path.relative_to(REPOSITORY_ROOT)}:{line_number}"
                for match in LOCAL_SVG_PATTERN.finditer(line)
                if 'class="img_center"' not in (match.group("attributes") or "")
            )

    assert not missing_center_class


def test_ansible_inventory_example(tmp_path: Path) -> None:
    """Verify the documented Ansible inventory produces the documented ANTA inventory."""
    input_inventory = REPOSITORY_ROOT / "docs/snippets/ansible-inventory.yml"
    expected_inventory = REPOSITORY_ROOT / "docs/snippets/anta-inventory-from-ansible.yml"
    generated_inventory = tmp_path / "anta-inventory.yml"

    create_inventory_from_ansible(input_inventory, generated_inventory, ansible_group="endpoints")

    assert generated_inventory.read_text(encoding="utf-8") == expected_inventory.read_text(encoding="utf-8")
