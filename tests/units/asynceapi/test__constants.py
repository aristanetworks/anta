# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi._constants module."""

import pytest

from asynceapi._constants import EapiCommandFormat


class TestEapiCommandFormat:
    """Test cases for the EapiCommandFormat enum."""

    def test_enum_values(self) -> None:
        """Test that the enum has the expected values."""
        assert EapiCommandFormat.JSON.value == "json"
        assert EapiCommandFormat.TEXT.value == "text"

    def test_str_method(self) -> None:
        """Test that the __str__ method returns the string value."""
        assert str(EapiCommandFormat.JSON) == "json"
        assert str(EapiCommandFormat.TEXT) == "text"

        # Test in string formatting
        assert f"Format: {EapiCommandFormat.JSON}" == "Format: json"

    def test_string_behavior(self) -> None:
        """Test that the enum behaves like a string."""
        # String methods should work
        assert EapiCommandFormat.JSON.upper() == "JSON"

        # String comparisons should work
        assert EapiCommandFormat.JSON == "json"
        assert EapiCommandFormat.TEXT == "text"

    def test_enum_lookup(self) -> None:
        """Test enum lookup by value."""
        assert EapiCommandFormat("json") is EapiCommandFormat.JSON
        assert EapiCommandFormat("text") is EapiCommandFormat.TEXT

        with pytest.raises(ValueError, match="'invalid' is not a valid EapiCommandFormat"):
            EapiCommandFormat("invalid")
