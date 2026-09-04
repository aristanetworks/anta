# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory EOS version helpers."""

from __future__ import annotations

import pytest

from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._eos.version import EOSVersion, parse_eos_version

VERSION_MATRIX = (
    VersionRule(major=4, minor=30, patch_gte=1, patch_lt=10),
    VersionRule(major=4, minor=33, patch_eq=1, exclude_suffixes=("FX-fixed",)),
)


@pytest.mark.parametrize(
    ("rule", "version", "expected"),
    [
        pytest.param(VersionRule(major=4, minor=30), EOSVersion(5, 30, 0), False, id="major-mismatch"),
        pytest.param(VersionRule(major=4, minor=30), EOSVersion(4, 31, 0), False, id="minor-mismatch"),
        pytest.param(VersionRule(major=4, minor=30, patch_eq=1), EOSVersion(4, 30, 2), False, id="exact-patch-mismatch"),
        pytest.param(VersionRule(major=4, minor=30, patch_lt=10), EOSVersion(4, 30, 10), False, id="patch-upper-bound"),
        pytest.param(VersionRule(major=4, minor=30, patch_gte=1), EOSVersion(4, 30, 0), False, id="patch-lower-bound"),
        pytest.param(
            VersionRule(major=4, minor=33, patch_eq=1, exclude_suffixes=("FX-fixed",)),
            EOSVersion(4, 33, 1, suffix="FX-fixed"),
            False,
            id="excluded-suffix",
        ),
        pytest.param(VersionRule(major=4, minor=30, patch_gte=1, patch_lt=10), EOSVersion(4, 30, 9, suffix="M"), True, id="match"),
    ],
)
def test_version_rule(rule: VersionRule, version: EOSVersion, *, expected: bool) -> None:
    """Verify affected-version rule matching."""
    assert rule.matches(version) is expected


@pytest.mark.parametrize(
    ("version", "expected_version", "expected_status"),
    [
        pytest.param("4.30.1F", "4.30.1F", AffectedStatus.AFFECTED, id="affected"),
        pytest.param("4.30.10M", "4.30.10M", AffectedStatus.NOT_AFFECTED, id="not-affected"),
        pytest.param(None, None, AffectedStatus.UNKNOWN, id="missing"),
    ],
)
def test_evaluate_version(version: str | None, expected_version: str | None, expected_status: AffectedStatus) -> None:
    """Verify affected-version evaluation."""
    device_version = parse_eos_version(version).get_value() if version is not None else None
    evaluation = evaluate_version(device_version, VERSION_MATRIX)

    assert evaluation.version == expected_version
    assert evaluation.affected_status is expected_status
