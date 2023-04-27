#!/usr/bin/env python
"""
generate_release.py

This script is used to generate the release.yml file as per
https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
"""

import yaml

SCOPES = [
    "anta",
    "anta.tests",
    "anta.cli",
]

# CI and Test are excluded from Release Notes
CATEGORIES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "cut": "Cut",
    "doc": "Documentation",
    # "CI": "CI",
    "bump": "Bump",
    # "test": "Test",
    "revert": "Revert",
    "refactor": "Refactoring",
}


class SafeDumper(yaml.SafeDumper):
    """
    Make yamllint happy
    https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586
    """

    # pylint: disable=R0901,W0613,W1113

    def increase_indent(self, flow=False, *args, **kwargs):
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
        }
    )

    # Add new features
    feat_labels = [f"rn: feat({scope})" for scope in SCOPES]
    feat_labels.append("rn: feat")

    categories_list.append(
        {
            "title": "New features and enhancements",
            "labels": feat_labels,
        }
    )

    # Add fixes
    fixes_labels = [f"rn: fix({scope})" for scope in SCOPES]
    fixes_labels.append("rn: fix")

    categories_list.append(
        {
            "title": "Fixed issues",
            "labels": fixes_labels,
        }
    )

    # Add Documentation
    doc_labels = [f"rn: doc({scope})" for scope in SCOPES]
    doc_labels.append("rn: doc")

    categories_list.append(
        {
            "title": "Documentation",
            "labels": doc_labels,
        }
    )

    # Add the catch all
    categories_list.append(
        {
            "title": "Other Changes",
            "labels": ["*"],
        }
    )
    with open(r"release.yml", "w", encoding="utf-8") as release_file:
        yaml.dump(
            {
                "changelog": {
                    "exclude": {"labels": exclude_list},
                    "categories": categories_list,
                }
            },
            release_file,
            Dumper=SafeDumper,
            sort_keys=False,
        )
