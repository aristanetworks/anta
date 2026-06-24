# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.version."""

from __future__ import annotations

import pytest

from anta.bugdb.version import EOSVersion, is_version_affected


class TestEOSVersion:
    """Tests for EOSVersion parsing and comparison."""

    @pytest.mark.parametrize(
        ("version_str", "major", "minor", "patch"),
        [
            ("4.30.1F", 4, 30, 1),
            ("4.23.3M", 4, 23, 3),
            ("4.32.0F", 4, 32, 0),
            ("4.28.3", 4, 28, 3),
        ],
    )
    def test_parse_standard(self, version_str: str, major: int, minor: int, patch: int) -> None:
        """Test parsing standard EOS versions."""
        v = EOSVersion(version_str)
        assert v.major == major
        assert v.minor == minor
        assert v.patch == patch

    @pytest.mark.parametrize(
        ("version_str", "hotfix1"),
        [
            ("4.23.3.1M", 1),
            ("4.30.1.2F", 2),
        ],
    )
    def test_parse_hotfix(self, version_str: str, hotfix1: int) -> None:
        """Test parsing hotfix versions."""
        v = EOSVersion(version_str)
        assert v.hotfix1 == hotfix1

    def test_parse_platform_specific(self) -> None:
        """Test parsing platform-specific versions."""
        v = EOSVersion("4.16.6FX-7060X")
        assert v.major == 4
        assert v.minor == 16
        assert v.patch == 6

    def test_parse_five_numbers(self) -> None:
        """Test parsing 5-number versions."""
        v = EOSVersion("4.21.2.1.2")
        assert v.major == 4
        assert v.minor == 21
        assert v.patch == 2
        assert v.hotfix1 == 1
        assert v.hotfix2 == 2

    def test_parse_invalid(self) -> None:
        """Test that invalid versions raise ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            EOSVersion("invalid")

    def test_parse_nofixyet(self) -> None:
        """Test that nofixyet versions raise ValueError."""
        with pytest.raises(ValueError, match="Cannot parse"):
            EOSVersion("4.26.nofixyet")

    def test_train(self) -> None:
        """Test train property."""
        assert EOSVersion("4.30.1F").train == (4, 30)
        assert EOSVersion("4.23.3.1M").train == (4, 23)

    def test_same_train(self) -> None:
        """Test same_train comparison."""
        assert EOSVersion("4.30.1F").same_train(EOSVersion("4.30.5F"))
        assert not EOSVersion("4.30.1F").same_train(EOSVersion("4.31.0F"))

    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            ("4.30.1F", "4.30.1", True),
            ("4.30.1F", "4.30.2F", False),
            ("4.23.3M", "4.23.3F", True),
        ],
    )
    def test_equality(self, a: str, b: str, *, expected: bool) -> None:
        """Test version equality."""
        assert (EOSVersion(a) == EOSVersion(b)) == expected

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            ("4.23.3F", "4.30.1F"),
            ("4.30.0F", "4.30.1F"),
            ("4.30.1F", "4.30.1.1F"),
        ],
    )
    def test_ordering(self, a: str, b: str) -> None:
        """Test version ordering."""
        assert EOSVersion(a) < EOSVersion(b)
        assert EOSVersion(b) > EOSVersion(a)

    def test_hash(self) -> None:
        """Test that equal versions have the same hash."""
        assert hash(EOSVersion("4.30.1F")) == hash(EOSVersion("4.30.1M"))

    def test_repr(self) -> None:
        """Test repr."""
        assert repr(EOSVersion("4.30.1F")) == "EOSVersion('4.30.1F')"

    def test_str(self) -> None:
        """Test str."""
        assert str(EOSVersion("4.30.1F")) == "4.30.1F"


class TestIsVersionAffected:
    """Tests for is_version_affected function."""

    def test_affected_same_train(self) -> None:
        """Test device in same train as introduction, before fix."""
        assert is_version_affected(EOSVersion("4.22.3F"), ["4.22.0"], ["4.22.5"])

    def test_not_affected_after_fix(self) -> None:
        """Test device in same train after fix."""
        assert not is_version_affected(EOSVersion("4.22.6F"), ["4.22.0"], ["4.22.5"])

    def test_not_affected_before_introduction(self) -> None:
        """Test device before bug introduction."""
        assert not is_version_affected(EOSVersion("4.13.0F"), ["4.14.0"], ["4.21.10"])

    def test_affected_cross_train(self) -> None:
        """Test device in a later train with fix available but not applied."""
        assert is_version_affected(EOSVersion("4.22.3F"), ["4.14.0"], ["4.21.10", "4.22.4", "4.23.3"])

    def test_not_affected_cross_train_after_fix(self) -> None:
        """Test device in a later train after fix."""
        assert not is_version_affected(EOSVersion("4.22.5F"), ["4.14.0"], ["4.21.10", "4.22.4"])

    def test_affected_nofixyet(self) -> None:
        """Test device in a train with nofixyet."""
        assert is_version_affected(EOSVersion("4.26.3F"), ["4.11.0"], ["4.20.6", "4.26.nofixyet", "4.27.0"])

    def test_not_affected_train_after_all_fixes(self) -> None:
        """Test device in a train newer than all fixes."""
        assert not is_version_affected(EOSVersion("4.30.1F"), ["4.14.0"], ["4.21.10", "4.22.4", "4.24.0"])

    def test_affected_no_fix_in_device_train(self) -> None:
        """Test device in a train with no fix but later trains have fixes."""
        assert is_version_affected(EOSVersion("4.25.1F"), ["4.14.0"], ["4.24.0", "4.26.0"])

    def test_no_introduced_versions(self) -> None:
        """Test with unparsable introduced versions."""
        assert not is_version_affected(EOSVersion("4.30.1F"), ["invalid"], ["4.30.2"])

    def test_affected_version_only(self) -> None:
        """Test bug with no conjunction — version check only."""
        assert is_version_affected(EOSVersion("4.30.1F"), ["4.14.0"], ["4.30.2"])

    def test_introduced_in_same_train_device_before(self) -> None:
        """Test device is before the introduction in the same train."""
        assert not is_version_affected(EOSVersion("4.36.0F"), ["4.36.1"], ["4.36.2"])

    def test_introduced_in_same_train_no_fix(self) -> None:
        """Test device in same train with no fix listed."""
        assert is_version_affected(EOSVersion("4.30.1F"), ["4.30.0"], [])

    def test_no_fix_later_train_has_fix(self) -> None:
        """Test device in a train without fix but later train has fix (still affected)."""
        assert is_version_affected(EOSVersion("4.25.1F"), ["4.20.0"], ["4.24.0", "4.26.0"])

    def test_all_fixes_before_device_train(self) -> None:
        """Test device in train after all fixes — not affected."""
        assert not is_version_affected(EOSVersion("4.30.1F"), ["4.14.0"], ["4.21.10", "4.22.4", "4.24.0"])

    def test_nofixyet_no_introduced_in_device_train(self) -> None:
        """Test nofixyet in device train from earlier introduced train."""
        assert is_version_affected(EOSVersion("4.26.3F"), ["4.20.0"], ["4.26.nofixyet"])


class TestEOSVersionEdgeCases:
    """Edge case tests for EOSVersion."""

    def test_eq_with_non_version(self) -> None:
        """Test equality with non-EOSVersion returns False."""
        v = EOSVersion("4.30.1F")
        assert (v == "not a version") is False
        assert (v != "not a version") is True

    def test_lt_with_non_version(self) -> None:
        """Test less-than with non-EOSVersion raises TypeError."""
        v = EOSVersion("4.30.1F")
        with pytest.raises(TypeError):
            v < "not a version"  # type: ignore[operator]  # noqa: B015


class TestVersionHelpers:
    """Tests for version helper functions."""

    def test_extract_train_invalid(self) -> None:
        """Test _extract_train with non-numeric parts."""
        from anta.bugdb.version import _extract_train

        assert _extract_train("abc.def") is None

    def test_extract_train_short(self) -> None:
        """Test _extract_train with single part."""
        from anta.bugdb.version import _extract_train

        assert _extract_train("4") is None

    def test_is_nofixyet(self) -> None:
        """Test _is_nofixyet with exact sentinel matching."""
        from anta.bugdb.version import _is_nofixyet

        assert _is_nofixyet("4.26.nofixyet")
        assert not _is_nofixyet("4.26.1")
        assert not _is_nofixyet("4.26.1-nofixyet2")
        assert not _is_nofixyet("4.26.nofixyetbeta")
