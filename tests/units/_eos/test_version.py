# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for EOS version parsing helpers."""

from __future__ import annotations

import pytest

from anta._eos.version import EOSVersion, parse_eos_version


@pytest.mark.parametrize(
    ("version_string", "expected"),
    [
        pytest.param(" 4.36.1FX-build ", EOSVersion(major=4, minor=36, patch=1, suffix="FX-build"), id="suffix"),
        pytest.param("4.34.7.1M", EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M"), id="hotfix"),
        pytest.param("unknown", None, id="invalid"),
        pytest.param("4.33", None, id="incomplete"),
    ],
)
def test_parse_eos_version(version_string: str, expected: EOSVersion | None) -> None:
    """Verify EOS version parsing."""
    assert parse_eos_version(version_string) == expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        pytest.param(EOSVersion(major=4, minor=36, patch=1, suffix="FX-build"), "4.36.1FX-build", id="suffix"),
        pytest.param(EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M"), "4.34.7.1M", id="hotfix"),
    ],
)
def test_eos_version__str__(version: EOSVersion, expected: str) -> None:
    """Verify the normalized string representation."""
    assert str(version) == expected


def test_eos_version_to_dict() -> None:
    """Verify the JSON-compatible dictionary representation."""
    version = EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M")

    assert version.to_dict() == {"major": 4, "minor": 34, "patch": 7, "suffix": "M", "hotfix": 1}
