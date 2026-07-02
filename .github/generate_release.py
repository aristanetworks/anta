# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: INP001
"""generate_release.py.

This script is used to generate the release.yml file as per
https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
"""

from itertools import permutations
from pathlib import Path

import yaml

BASE_SCOPES = [
    "anta",
    "anta.tests",
    "anta.cli",
]

# The shared release-note labeler replaces comma-separated PR scopes with "|"
# before creating the GitHub label.
SCOPES = [
    *BASE_SCOPES,
    *["|".join(scopes) for scope_count in range(2, len(BASE_SCOPES) + 1) for scopes in permutations(BASE_SCOPES, scope_count)],
]

# CI and Test are excluded from Release Notes
CATEGORIES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "cut": "Cut",
    "doc": "Documentation",
    "bump": "Bump",
    "revert": "Revert",
    "refactor": "Refactoring",
}


class SafeDumper(yaml.SafeDumper):
    """Make yamllint happy.

    https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586.
    """

    # pylint: disable=R0901

    def increase_indent(self, flow: bool = False, *_args: object, **_kwargs: object) -> None:  # noqa: FBT001, FBT002
        """Increase indentation for nested lists."""
        return super().increase_indent(flow=flow, indentless=False)


if __name__ == "__main__":
    exclude_list = []
    categories_list = []

    # First add exclude labels
    for scope in SCOPES:
        exclude_list.append(f"rn: test({scope})")
        exclude_list.append(f"rn: ci({scope})")
    exclude_list.extend(["rn: test", "rn: ci"])

    # Then add the categories
    # First add Breaking Changes
    breaking_label_categories = ["feat", "fix", "cut", "revert", "refactor", "bump"]
    breaking_labels = [f"rn: {cc_type}({scope})!" for cc_type in breaking_label_categories for scope in SCOPES]
    breaking_labels.extend([f"rn: {cc_type}!" for cc_type in breaking_label_categories])

    categories_list.append(
        {
            "title": "Breaking Changes",
            "labels": breaking_labels,
        },
    )

    # Add new features
    feat_labels = [f"rn: feat({scope})" for scope in SCOPES]
    feat_labels.append("rn: feat")

    categories_list.append(
        {
            "title": "New features and enhancements",
            "labels": feat_labels,
        },
    )

    # Add fixes
    fixes_labels = [f"rn: fix({scope})" for scope in SCOPES]
    fixes_labels.append("rn: fix")

    categories_list.append(
        {
            "title": "Fixed issues",
            "labels": fixes_labels,
        },
    )

    # Add Documentation
    doc_labels = [f"rn: doc({scope})" for scope in SCOPES]
    doc_labels.append("rn: doc")

    categories_list.append(
        {
            "title": "Documentation",
            "labels": doc_labels,
        },
    )

    # Add the catch all
    categories_list.append(
        {
            "title": "Other Changes",
            "labels": ["*"],
        },
    )
    with Path(__file__).with_name("release.yml").open("w", encoding="utf-8") as release_file:
        yaml.dump(
            {
                "changelog": {
                    "exclude": {"labels": exclude_list},
                    "categories": categories_list,
                },
            },
            release_file,
            Dumper=SafeDumper,
            sort_keys=False,
        )
