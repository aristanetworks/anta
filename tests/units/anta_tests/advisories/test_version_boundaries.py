# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Cross-advisory EOS version-boundary consistency tests."""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

import pytest

from anta._advisory.eos_versions import VersionRule
from anta._advisory.remediation import FixedRelease
from anta._eos.version import EOSVersion
from anta.tests import advisories

if TYPE_CHECKING:
    from collections.abc import Iterator

UPPER_HOTFIX_BOUND_ATTRIBUTES = ("hotfix_eq", "hotfix_lt", "hotfix_lte")
AFFECTED_SUFFIXES = ("_AFFECTED_VERSION_MATRIX", "_AFFECTED_VERSIONS")


def _hotfix_boundaries() -> Iterator[tuple[str, VersionRule, tuple[FixedRelease, ...]]]:
    """Yield every hotfix-bounded advisory rule with its corresponding fixed releases."""
    for module_info in pkgutil.iter_modules(advisories.__path__, f"{advisories.__name__}."):
        if not module_info.name.rpartition(".")[2].startswith("sa_"):
            continue
        module = importlib.import_module(module_info.name)
        for affected_name, value in vars(module).items():
            if not isinstance(value, tuple) or not value or not all(isinstance(rule, VersionRule) for rule in value):
                continue
            prefix = (
                ""
                if affected_name == "AFFECTED_VERSION_MATRIX"
                else next((affected_name.removesuffix(suffix) for suffix in AFFECTED_SUFFIXES if affected_name.endswith(suffix)), None)
            )
            if prefix is None:
                continue
            fixed_name = f"{prefix}_FIXED_RELEASES" if prefix else "FIXED_RELEASES"
            fixed_releases = getattr(module, fixed_name, None)
            for rule in value:
                if any(getattr(rule, attribute) is not None for attribute in UPPER_HOTFIX_BOUND_ATTRIBUTES):
                    assert isinstance(fixed_releases, tuple), f"{module_info.name}.{affected_name} has no corresponding {fixed_name}"
                    assert all(isinstance(release, FixedRelease) for release in fixed_releases), f"{fixed_name} contains an invalid fixed release"
                    yield f"{module_info.name}.{affected_name}", rule, fixed_releases


@pytest.mark.parametrize(("source", "rule", "fixed_releases"), tuple(_hotfix_boundaries()))
def test_hotfix_boundaries_have_same_patch_fixed_release(source: str, rule: VersionRule, fixed_releases: tuple[FixedRelease, ...]) -> None:
    """Require every explicit hotfix boundary to be justified by a fixed release in the same patch."""
    same_patch_fixed_versions = tuple(
        version
        for release in fixed_releases
        if isinstance((version := release.version), EOSVersion) and (version.major, version.minor, version.patch) == (rule.major, rule.minor, rule.patch_eq)
    )
    assert same_patch_fixed_versions, f"{source} has an explicit hotfix boundary without a fixed EOS release in the same patch"
    assert all(not rule.matches(version) for version in same_patch_fixed_versions), f"{source} includes a fixed EOS release in its affected hotfix boundary"
