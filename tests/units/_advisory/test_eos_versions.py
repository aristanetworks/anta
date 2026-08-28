# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory EOS version helpers."""

from __future__ import annotations

from typing import Any

import pytest

from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version, require_affected_version
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult

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
    ("output", "expected_version", "expected_status"),
    [
        pytest.param({"version": "4.30.1F"}, "4.30.1F", AffectedStatus.AFFECTED, id="affected"),
        pytest.param({"version": "4.30.10M"}, "4.30.10M", AffectedStatus.NOT_AFFECTED, id="not-affected"),
        pytest.param({"version": "invalid"}, "invalid", AffectedStatus.UNKNOWN, id="invalid"),
        pytest.param({}, None, AffectedStatus.UNKNOWN, id="missing"),
        pytest.param({"version": 4301}, None, AffectedStatus.UNKNOWN, id="wrong-type"),
    ],
)
def test_evaluate_version(output: dict[str, Any], expected_version: str | None, expected_status: AffectedStatus) -> None:
    """Verify affected-version evaluation."""
    evaluation = evaluate_version(output, VERSION_MATRIX)

    assert evaluation.version == expected_version
    assert evaluation.affected_status is expected_status


@pytest.mark.parametrize(
    ("output", "should_continue", "expected_status", "expected_message"),
    [
        pytest.param({"version": "4.30.1F"}, True, AntaTestStatus.UNSET, "is affected by this advisory", id="affected"),
        pytest.param({"version": "4.30.10M"}, False, AntaTestStatus.SUCCESS, "is not affected by this advisory", id="not-affected"),
        pytest.param({"version": "invalid"}, False, AntaTestStatus.ERROR, "could not be determined", id="unknown"),
    ],
)
def test_require_affected_version(
    output: dict[str, Any],
    *,
    should_continue: bool,
    expected_status: AntaTestStatus,
    expected_message: str,
) -> None:
    """Verify affected-version result handling."""
    result = AntaTestResult(name="device", test="advisory", categories=["Security Advisory"], description="description")
    messages: list[str] = []

    assert require_affected_version(result, messages, output, VERSION_MATRIX) is should_continue
    assert result.result is expected_status
    assert expected_message in messages[0]
