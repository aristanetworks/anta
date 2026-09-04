# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for EOS version parsing helpers."""

from __future__ import annotations

import pytest

from anta._eos.parsing import ParseFail, ParseFailureReason, ParseSuccessful
from anta._eos.version import EOSVersion, parse_eos_version


@pytest.mark.parametrize(
    ("version_string", "expected"),
    [
        pytest.param(" 4.36.1FX-build ", EOSVersion(major=4, minor=36, patch=1, suffix="FX-build"), id="suffix"),
        pytest.param("4.34.7.1M", EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M"), id="hotfix"),
    ],
)
def test_parse_eos_version(version_string: str, expected: EOSVersion) -> None:
    """Verify successful EOS version parsing."""
    result = parse_eos_version(version_string)

    assert isinstance(result, ParseSuccessful)
    assert result.value == expected


@pytest.mark.parametrize(
    ("version_value", "reason", "detail"),
    [
        pytest.param(None, ParseFailureReason.MISSING, "EOS version is missing", id="missing"),
        pytest.param(42, ParseFailureReason.MALFORMED, "EOS version is not a string", id="malformed"),
        pytest.param("", ParseFailureReason.INVALID, "EOS version is empty", id="empty"),
        pytest.param("   ", ParseFailureReason.INVALID, "EOS version is empty", id="whitespace"),
        pytest.param("unknown", ParseFailureReason.INVALID, "EOS version has an invalid format", id="invalid"),
        pytest.param("4.33", ParseFailureReason.INVALID, "EOS version has an invalid format", id="incomplete"),
    ],
)
def test_parse_eos_version_failure(version_value: object, reason: ParseFailureReason, detail: str) -> None:
    """Verify invalid EOS version evidence retains its failure reason and detail."""
    result = parse_eos_version(version_value)

    assert isinstance(result, ParseFail)
    assert result.reason is reason
    assert result.detail == detail


def test_parse_eos_version_unwrap_success() -> None:
    """Verify callers can unwrap a successfully parsed value."""
    assert parse_eos_version("4.34.7.1M").unwrap() == EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M")


def test_parse_eos_version_unwrap_failure() -> None:
    """Verify unwrapping a parsing failure raises with useful context."""
    with pytest.raises(ValueError, match="invalid: EOS version has an invalid format"):
        parse_eos_version("invalid").unwrap()


@pytest.mark.parametrize(
    ("version_value", "expected"),
    [
        pytest.param("4.34.7.1M", EOSVersion(major=4, minor=34, patch=7, hotfix=1, suffix="M"), id="success"),
        pytest.param("invalid", None, id="failure"),
    ],
)
def test_parse_eos_version_unwrap_or_none(version_value: object, expected: EOSVersion | None) -> None:
    """Verify callers can explicitly collapse parsing failures to `None`."""
    assert parse_eos_version(version_value).unwrap_or_none() == expected


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


def test_eos_version_is_orderable() -> None:
    """Order EOS releases by numeric components before using the suffix as a stable tie-breaker."""
    versions = (
        EOSVersion(4, 34, 8, suffix="M"),
        EOSVersion(4, 35, 6, suffix="M"),
        EOSVersion(4, 35, 6, hotfix=1, suffix="M"),
    )

    assert min(versions) == EOSVersion(4, 34, 8, suffix="M")
    assert max(versions) == EOSVersion(4, 35, 6, hotfix=1, suffix="M")
