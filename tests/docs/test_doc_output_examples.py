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


def test_readme_help_matches_generated_snippet() -> None:
    """Verify the standalone README help block matches generated CLI help."""
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    generated_help = (REPOSITORY_ROOT / "docs/snippets/anta_help.txt").read_text(encoding="utf-8").rstrip()
    match = README_HELP_PATTERN.search(readme)

    assert match is not None
    assert match.group("help") == f"```bash\n{generated_help}\n```"


def test_ansible_inventory_example(tmp_path: Path) -> None:
    """Verify the documented Ansible inventory produces the documented ANTA inventory."""
    input_inventory = REPOSITORY_ROOT / "docs/snippets/ansible-inventory.yml"
    expected_inventory = REPOSITORY_ROOT / "docs/snippets/anta-inventory-from-ansible.yml"
    generated_inventory = tmp_path / "anta-inventory.yml"

    create_inventory_from_ansible(input_inventory, generated_inventory, ansible_group="endpoints")

    assert generated_inventory.read_text(encoding="utf-8") == expected_inventory.read_text(encoding="utf-8")
